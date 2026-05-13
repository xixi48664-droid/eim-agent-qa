import secrets
import string
import uuid
from typing import Optional
from datetime import datetime
from app.repositories.user_repository import UserRepository
from app.repositories.history_repository import HistoryRepository
from app.repositories.component_repository import ComponentRepository
from app.repositories.standard_repository import StandardRepository
from app.repositories.tutorial_repository import TutorialRepository
from app.utils.password import hash_password
from app.entities.operation_log import OperationLog
from app.entities.component_info import Component, ComponentParam
from app.entities.process_standard import ProcessStandard
from app.entities.tutorial import Tutorial, TutorialStep
from app.schemas.user_schema import (
    UserRecord,
    UserStatusData,
    ResetPasswordData,
    OperationLogRecord,
)
from app.schemas.component_admin_schema import (
    ComponentCreateRequest,
    ComponentUpdateRequest,
    ComponentAdminRecord,
)
from app.schemas.standard_schema import (
    StandardCreateRequest,
    StandardUpdateRequest,
    StandardRecord,
)
from app.external.vector_store_client import VectorStoreClient
from app.schemas.tutorial_schema import (
    TutorialCreateRequest,
    TutorialUpdateRequest,
    TutorialRecord,
    TutorialDetail,
    StepRecord,
)


class AdminService:
    """管理员业务逻辑 — 对应设计文档 4.14 AdminService 类"""

    def __init__(
        self,
        user_repo: UserRepository,
        log_repo: HistoryRepository,
        component_repo: ComponentRepository | None = None,
        standard_repo: StandardRepository | None = None,
        tutorial_repo: TutorialRepository | None = None,
    ):
        self._userRepository = user_repo
        self._logRepository = log_repo
        self._componentRepository = component_repo
        self._standardRepository = standard_repo
        self._tutorialRepository = tutorial_repo

    def getUsers(
        self,
        username: Optional[str] = None,
        email: Optional[str] = None,
        status: Optional[str] = None,
        registerStart: Optional[str] = None,
        registerEnd: Optional[str] = None,
        pageNum: int = 1,
        pageSize: int = 10,
    ) -> dict:
        """查询用户列表 — 对应设计文档 AdminService.getUsers"""
        reg_start = (
            datetime.fromisoformat(registerStart) if registerStart else None
        )
        reg_end = (
            datetime.fromisoformat(registerEnd) if registerEnd else None
        )

        users, total = self._userRepository.findUsers(
            username=username,
            email=email,
            status=status,
            registerStart=reg_start,
            registerEnd=reg_end,
            pageNum=pageNum,
            pageSize=pageSize,
        )

        records = [UserRecord.model_validate(u).model_dump() for u in users]
        return {
            "pageNum": pageNum,
            "pageSize": pageSize,
            "total": total,
            "records": records,
        }

    def setUserStatus(self, user_id: str, status: str) -> UserStatusData:
        """启用/禁用用户 — 对应设计文档 AdminService.setUserStatus"""
        user = self._userRepository.findById(user_id)
        if not user:
            raise ValueError("用户不存在")

        user.status = status
        self._userRepository.update(user)

        return UserStatusData(userId=user.user_id, status=user.status)

    def batchSetUserStatus(self, user_ids: list[str], status: str) -> int:
        """批量修改用户状态"""
        return self._userRepository.batchUpdateStatus(user_ids, status)

    def batchDeleteUsers(self, user_ids: list[str]) -> int:
        """批量删除用户"""
        return self._userRepository.batchDelete(user_ids)

    def resetPassword(self, user_id: str, new_password: str | None = None) -> ResetPasswordData:
        """重置用户密码 — 对应接口文档 4.3 节"""
        user = self._userRepository.findById(user_id)
        if not user:
            raise ValueError("用户不存在")

        password = new_password or _generate_temp_password()
        user.password = hash_password(password)
        self._userRepository.update(user)

        return ResetPasswordData(userId=user.user_id, tempPassword=password)

    def getUserLogs(
        self,
        user_id: str,
        operationType: Optional[str] = None,
        startTime: Optional[str] = None,
        endTime: Optional[str] = None,
        pageNum: int = 1,
        pageSize: int = 10,
    ) -> dict:
        """查看用户操作日志 — 对应接口文档 4.4 节"""
        user = self._userRepository.findById(user_id)
        if not user:
            raise ValueError("用户不存在")

        st = datetime.fromisoformat(startTime) if startTime else None
        et = datetime.fromisoformat(endTime) if endTime else None

        logs, total = self._logRepository.findByUser(
            user_id=user_id,
            operationType=operationType,
            startTime=st,
            endTime=et,
            pageNum=pageNum,
            pageSize=pageSize,
        )

        records = []
        for log in logs:
            desc = log.operation_type
            if log.operation_target:
                desc = f"{desc} {log.operation_target}"
            records.append(
                OperationLogRecord(
                    logId=log.log_id,
                    operationType=log.operation_type,
                    operationDesc=desc,
                    operationTime=log.operation_time,
                ).model_dump()
            )

        return {
            "pageNum": pageNum,
            "pageSize": pageSize,
            "total": total,
            "records": records,
        }

    def saveComponent(self, form: ComponentCreateRequest) -> ComponentAdminRecord:
        """维护元器件信息 — 对应设计文档 AdminService.saveComponent"""
        exists = self._componentRepository.findByModel(form.model)
        if exists:
            raise ValueError(f"元器件型号已存在: {form.model}")

        comp = Component(
            component_id=uuid.uuid4().hex,
            model=form.model,
            type=form.type,
            package_type=form.packageType,
            manufacturer=form.manufacturer,
            datasheet_url=form.datasheetUrl,
            image_url=form.imageUrl,
        )
        self._componentRepository.save(comp)

        if form.params:
            param_entities = []
            for p in form.params:
                param_entities.append(ComponentParam(
                    param_id=uuid.uuid4().hex,
                    component_id=comp.component_id,
                    param_name=p.paramName,
                    param_value=p.paramValue,
                    param_unit=p.paramUnit,
                ))
            self._componentRepository.saveParams(param_entities)

        return self._to_admin_record(comp, len(form.params))

    def updateComponent(self, component_id: str, form: ComponentUpdateRequest) -> ComponentAdminRecord:
        """更新元器件信息"""
        comp = self._componentRepository.findById(component_id)
        if not comp:
            raise ValueError("元器件不存在")

        if form.model is not None:
            exists = self._componentRepository.findByModel(form.model)
            if exists and exists.component_id != component_id:
                raise ValueError(f"元器件型号已存在: {form.model}")
            comp.model = form.model
        if form.type is not None:
            comp.type = form.type
        if form.packageType is not None:
            comp.package_type = form.packageType
        if form.manufacturer is not None:
            comp.manufacturer = form.manufacturer
        if form.datasheetUrl is not None:
            comp.datasheet_url = form.datasheetUrl
        if form.imageUrl is not None:
            comp.image_url = form.imageUrl

        self._componentRepository.update(comp)

        if form.params is not None:
            self._componentRepository.deleteParams(component_id)
            param_entities = []
            for p in form.params:
                param_entities.append(ComponentParam(
                    param_id=uuid.uuid4().hex,
                    component_id=comp.component_id,
                    param_name=p.paramName,
                    param_value=p.paramValue,
                    param_unit=p.paramUnit,
                ))
            self._componentRepository.saveParams(param_entities)

        comp = self._componentRepository.findById(component_id)
        param_count = len(form.params) if form.params is not None else -1
        if param_count < 0:
            param_count = len(comp.params) if comp.params else 0
        return self._to_admin_record(comp, param_count)

    def deleteComponent(self, component_id: str) -> None:
        """删除元器件"""
        comp = self._componentRepository.findById(component_id)
        if not comp:
            raise ValueError("元器件不存在")

        self._componentRepository.deleteParams(component_id)
        self._componentRepository.delete(comp)

    def getComponents(
        self,
        model: Optional[str] = None,
        type: Optional[str] = None,
        manufacturer: Optional[str] = None,
        pageNum: int = 1,
        pageSize: int = 10,
    ) -> dict:
        """分页查询元器件列表"""
        comps, total = self._componentRepository.searchAdmin(
            model=model,
            type=type,
            manufacturer=manufacturer,
            pageNum=pageNum,
            pageSize=pageSize,
        )

        records = []
        for c in comps:
            param_count = len(c.params) if c.params else 0
            records.append(self._to_admin_record(c, param_count).model_dump())

        return {
            "pageNum": pageNum,
            "pageSize": pageSize,
            "total": total,
            "records": records,
        }

    # ── 工艺规范 CRUD ────────────────────────────────────────

    def saveStandard(self, form: StandardCreateRequest) -> StandardRecord:
        """维护工艺规范信息 — 对应设计文档 AdminService.saveStandard"""
        standard = ProcessStandard(
            standard_id=uuid.uuid4().hex,
            standard_code=form.standardCode,
            standard_name=form.standardName,
            section=form.section,
            summary=form.summary,
            tags=form.tags,
            related_process=form.relatedProcess,
        )
        self._standardRepository.save(standard)
        self._syncStandardToVector(standard)
        return self._to_standard_record(standard)

    def updateStandard(self, standard_id: str, form: StandardUpdateRequest) -> StandardRecord:
        standard = self._standardRepository.findById(standard_id)
        if not standard:
            raise ValueError("规范不存在")

        if form.standardCode is not None:
            standard.standard_code = form.standardCode
        if form.standardName is not None:
            standard.standard_name = form.standardName
        if form.section is not None:
            standard.section = form.section
        if form.summary is not None:
            standard.summary = form.summary
        if form.tags is not None:
            standard.tags = form.tags
        if form.relatedProcess is not None:
            standard.related_process = form.relatedProcess

        self._standardRepository.update(standard)
        self._syncStandardToVector(standard)
        return self._to_standard_record(standard)

    def deleteStandard(self, standard_id: str) -> None:
        standard = self._standardRepository.findById(standard_id)
        if not standard:
            raise ValueError("规范不存在")
        self._standardRepository.delete(standard)
        self._deleteStandardFromVector(standard_id)

    def getStandards(
        self,
        standardName: Optional[str] = None,
        standardCode: Optional[str] = None,
        pageNum: int = 1,
        pageSize: int = 10,
    ) -> dict:
        records, total = self._standardRepository.searchAdmin(
            standardName=standardName,
            standardCode=standardCode,
            pageNum=pageNum,
            pageSize=pageSize,
        )
        return {
            "pageNum": pageNum,
            "pageSize": pageSize,
            "total": total,
            "records": [self._to_standard_record(r).model_dump() for r in records],
        }

    def _to_standard_record(self, s: ProcessStandard) -> StandardRecord:
        return StandardRecord(
            standardId=s.standard_id,
            standardCode=s.standard_code or "",
            standardName=s.standard_name,
            section=s.section or "",
            summary=s.summary or "",
            tags=s.tags or "",
            relatedProcess=s.related_process or "",
        )

    # ── 教程 CRUD ────────────────────────────────────────────

    def saveTutorial(self, form: TutorialCreateRequest) -> TutorialDetail:
        """维护流程教程信息 — 对应设计文档 AdminService.saveTutorial"""
        tutorial = Tutorial(
            tutorial_id=uuid.uuid4().hex,
            process_name=form.processName,
            total_steps=len(form.steps),
            estimated_time=form.estimatedTime,
        )
        self._tutorialRepository.save(tutorial)

        step_entities = []
        for sp in form.steps:
            step_entities.append(TutorialStep(
                step_id=uuid.uuid4().hex,
                tutorial_id=tutorial.tutorial_id,
                step_no=sp.stepNo,
                step_title=sp.stepTitle,
                step_content=sp.stepContent,
                image_url=sp.imageUrl,
                note=sp.note,
                faq=sp.faq,
            ))
        if step_entities:
            self._tutorialRepository.saveSteps(step_entities)

        return self._to_tutorial_detail(tutorial, step_entities)

    def updateTutorial(self, tutorial_id: str, form: TutorialUpdateRequest) -> TutorialDetail:
        tutorial = self._tutorialRepository.findById(tutorial_id)
        if not tutorial:
            raise ValueError("教程不存在")

        if form.processName is not None:
            tutorial.process_name = form.processName
        if form.estimatedTime is not None:
            tutorial.estimated_time = form.estimatedTime

        if form.steps is not None:
            self._tutorialRepository.deleteSteps(tutorial_id)
            step_entities = []
            for sp in form.steps:
                step_entities.append(TutorialStep(
                    step_id=uuid.uuid4().hex,
                    tutorial_id=tutorial.tutorial_id,
                    step_no=sp.stepNo,
                    step_title=sp.stepTitle,
                    step_content=sp.stepContent,
                    image_url=sp.imageUrl,
                    note=sp.note,
                    faq=sp.faq,
                ))
            self._tutorialRepository.saveSteps(step_entities)
            tutorial.total_steps = len(form.steps)

        self._tutorialRepository.update(tutorial)

        steps = self._tutorialRepository.getSteps(tutorial_id)
        return self._to_tutorial_detail(tutorial, steps)

    def deleteTutorial(self, tutorial_id: str) -> None:
        tutorial = self._tutorialRepository.findById(tutorial_id)
        if not tutorial:
            raise ValueError("教程不存在")
        self._tutorialRepository.deleteSteps(tutorial_id)
        self._tutorialRepository.delete(tutorial)

    def getTutorials(
        self,
        processName: Optional[str] = None,
        pageNum: int = 1,
        pageSize: int = 10,
    ) -> dict:
        records, total = self._tutorialRepository.searchAdmin(
            processName=processName,
            pageNum=pageNum,
            pageSize=pageSize,
        )
        return {
            "pageNum": pageNum,
            "pageSize": pageSize,
            "total": total,
            "records": [TutorialRecord(
                tutorialId=t.tutorial_id,
                processName=t.process_name,
                totalSteps=t.total_steps,
                estimatedTime=t.estimated_time or "",
            ).model_dump() for t in records],
        }

    def getTutorialDetail(self, tutorial_id: str) -> TutorialDetail:
        tutorial = self._tutorialRepository.findById(tutorial_id)
        if not tutorial:
            raise ValueError("教程不存在")
        steps = self._tutorialRepository.getSteps(tutorial_id)
        return self._to_tutorial_detail(tutorial, steps)

    def _to_tutorial_detail(self, t: Tutorial, steps: list[TutorialStep]) -> TutorialDetail:
        return TutorialDetail(
            tutorialId=t.tutorial_id,
            processName=t.process_name,
            totalSteps=t.total_steps,
            estimatedTime=t.estimated_time or "",
            steps=[
                StepRecord(
                    stepId=s.step_id,
                    stepNo=s.step_no,
                    stepTitle=s.step_title or "",
                    stepContent=s.step_content,
                    imageUrl=s.image_url,
                    note=s.note,
                    faq=s.faq,
                )
                for s in steps
            ],
        )

    # ── 内部辅助 ──────────────────────────────────────────────

    def _syncStandardToVector(self, standard: ProcessStandard) -> None:
        """将规范同步到向量数据库"""
        try:
            text_parts = [standard.standard_name]
            if standard.section:
                text_parts.append(standard.section)
            if standard.summary:
                text_parts.append(standard.summary)
            text = " — ".join(text_parts)
            metadata = {
                "standardCode": standard.standard_code or "",
                "standardName": standard.standard_name,
                "section": standard.section or "",
            }
            VectorStoreClient().insert(
                doc_id=standard.standard_id, text=text, metadata=metadata,
            )
        except Exception:
            pass  # 向量同步失败不影响主流程

    def _deleteStandardFromVector(self, standard_id: str) -> None:
        """从向量数据库删除规范"""
        try:
            VectorStoreClient().delete(standard_id)
        except Exception:
            pass

    def _to_admin_record(self, comp: Component, param_count: int = 0) -> ComponentAdminRecord:
        """将 ORM 实体转为 DTO，处理 NULL 字段"""
        return ComponentAdminRecord(
            componentId=comp.component_id,
            model=comp.model,
            type=comp.type or "",
            packageType=comp.package_type or "",
            manufacturer=comp.manufacturer or "",
            datasheetUrl=comp.datasheet_url,
            imageUrl=comp.image_url,
            paramCount=param_count,
            createTime=comp.create_time,
            updateTime=comp.update_time,
        )

    def _recordAdminOperation(
        self, admin_user_id: str, operation_type: str, operation_target: str,
        operation_result: str = "成功"
    ) -> None:
        """记录管理员操作日志 — 对应设计文档 AdminService._recordAdminOperation"""
        log = OperationLog(
            user_id=admin_user_id,
            operation_type=operation_type,
            operation_target=operation_target,
            operation_result=operation_result,
        )
        self._logRepository.saveOperationLog(log)


def _generate_temp_password(length: int = 8) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))
