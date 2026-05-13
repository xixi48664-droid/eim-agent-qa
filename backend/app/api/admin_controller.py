"""
管理员用户管理接口 — 对应设计文档 4.4 AdminController 类
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.mysql import get_db
from app.core.security import get_current_admin
from app.repositories.user_repository import UserRepository
from app.repositories.history_repository import HistoryRepository
from app.repositories.component_repository import ComponentRepository
from app.repositories.standard_repository import StandardRepository
from app.repositories.tutorial_repository import TutorialRepository
from app.services.admin_service import AdminService
from app.services.monitor_service import MonitorService
from app.schemas.user_schema import UserStatusUpdate, ResetPasswordRequest, BatchUserStatusRequest, BatchDeleteRequest, BatchResult
from app.schemas.component_admin_schema import (
    ComponentCreateRequest,
    ComponentUpdateRequest,
)
from app.schemas.standard_schema import StandardCreateRequest, StandardUpdateRequest
from app.schemas.tutorial_schema import TutorialCreateRequest, TutorialUpdateRequest
from app.core.response import success, error

router = APIRouter(prefix="/api/v1/admin/users", tags=["用户管理"])
component_router = APIRouter(prefix="/api/v1/admin/components", tags=["元器件管理"])
standard_router = APIRouter(prefix="/api/v1/admin/standards", tags=["规范管理"])
tutorial_router = APIRouter(prefix="/api/v1/admin/tutorials", tags=["教程管理"])
monitor_router = APIRouter(prefix="/api/v1/admin", tags=["服务监控"])


@router.get("")
def getUserList(
    username: Optional[str] = Query(None, description="用户名筛选"),
    email: Optional[str] = Query(None, description="邮箱筛选"),
    status: Optional[str] = Query(None, description="用户状态，enabled/disabled"),
    registerStart: Optional[str] = Query(None, description="注册开始时间"),
    registerEnd: Optional[str] = Query(None, description="注册结束时间"),
    pageNum: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(10, ge=1, le=100, description="每页条数"),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """
    查询用户列表 — 对应设计文档 AdminController.getUserList
    接口文档 4.1 节
    """
    user_repo = UserRepository(db)
    log_repo = HistoryRepository(db)
    admin_service = AdminService(user_repo, log_repo)

    result = admin_service.getUsers(
        username=username,
        email=email,
        status=status,
        registerStart=registerStart,
        registerEnd=registerEnd,
        pageNum=pageNum,
        pageSize=pageSize,
    )
    return success(data=result, message="查询成功")


@router.patch("/{userId}/status")
def updateUserStatus(
    userId: str,
    body: UserStatusUpdate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """
    启用/禁用用户 — 对应设计文档 AdminController.updateUserStatus
    接口文档 4.2 节
    """
    user_repo = UserRepository(db)
    log_repo = HistoryRepository(db)
    admin_service = AdminService(user_repo, log_repo)

    try:
        result = admin_service.setUserStatus(userId, body.status)
        admin_service._recordAdminOperation(
            current_admin.user_id, "修改用户状态",
            f"用户{userId} -> {body.status}"
        )
        return success(data=result.model_dump(), message="用户状态更新成功")
    except ValueError as e:
        return error(404, str(e))


@router.post("/{userId}/reset-password")
def resetUserPassword(
    userId: str,
    body: ResetPasswordRequest,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """
    重置用户密码 — 对应接口文档 4.3 节
    """
    user_repo = UserRepository(db)
    log_repo = HistoryRepository(db)
    admin_service = AdminService(user_repo, log_repo)

    try:
        result = admin_service.resetPassword(userId, body.password)
        admin_service._recordAdminOperation(
            current_admin.user_id, "重置密码", f"用户{userId}"
        )
        return success(data=result.model_dump(), message="密码重置成功")
    except ValueError as e:
        return error(404, str(e))


@router.post("/batch-status")
def batchUpdateUserStatus(
    body: BatchUserStatusRequest,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """批量启用/禁用用户"""
    user_repo = UserRepository(db)
    log_repo = HistoryRepository(db)
    admin_service = AdminService(user_repo, log_repo)

    count = admin_service.batchSetUserStatus(body.userIds, body.status)
    admin_service._recordAdminOperation(
        current_admin.user_id, "批量修改用户状态",
        f"{len(body.userIds)}个用户 -> {body.status}"
    )
    return success(
        data=BatchResult(affectedCount=count, failedIds=[]).model_dump(),
        message=f"已{('启用' if body.status == 'enabled' else '禁用')}{count}个用户",
    )


@router.post("/batch-delete")
def batchDeleteUsers(
    body: BatchDeleteRequest,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """批量删除用户"""
    user_repo = UserRepository(db)
    log_repo = HistoryRepository(db)
    admin_service = AdminService(user_repo, log_repo)

    count = admin_service.batchDeleteUsers(body.userIds)
    admin_service._recordAdminOperation(
        current_admin.user_id, "批量删除用户",
        f"{len(body.userIds)}个用户"
    )
    return success(
        data=BatchResult(affectedCount=count, failedIds=[]).model_dump(),
        message=f"已删除{count}个用户",
    )


@router.get("/{userId}/logs")
def getUserLogs(
    userId: str,
    operationType: Optional[str] = Query(None, description="操作类型"),
    startTime: Optional[str] = Query(None, description="开始时间"),
    endTime: Optional[str] = Query(None, description="结束时间"),
    pageNum: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """
    查看用户操作日志 — 对应接口文档 4.4 节
    """
    user_repo = UserRepository(db)
    log_repo = HistoryRepository(db)
    admin_service = AdminService(user_repo, log_repo)

    try:
        result = admin_service.getUserLogs(
            user_id=userId,
            operationType=operationType,
            startTime=startTime,
            endTime=endTime,
            pageNum=pageNum,
            pageSize=pageSize,
        )
        return success(data=result, message="查询成功")
    except ValueError as e:
        return error(404, str(e))


# ── 元器件管理接口（设计文档 AdminController.manageComponent）────────────────

@component_router.get("")
def getComponentList(
    model: Optional[str] = Query(None, description="型号筛选"),
    type: Optional[str] = Query(None, description="类型筛选"),
    manufacturer: Optional[str] = Query(None, description="厂商筛选"),
    pageNum: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """分页查询元器件列表"""
    user_repo = UserRepository(db)
    log_repo = HistoryRepository(db)
    component_repo = ComponentRepository(db)
    admin_service = AdminService(user_repo, log_repo, component_repo)

    result = admin_service.getComponents(
        model=model,
        type=type,
        manufacturer=manufacturer,
        pageNum=pageNum,
        pageSize=pageSize,
    )
    return success(data=result, message="查询成功")


@component_router.post("")
def createComponent(
    body: ComponentCreateRequest,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """新增元器件及参数"""
    user_repo = UserRepository(db)
    log_repo = HistoryRepository(db)
    component_repo = ComponentRepository(db)
    admin_service = AdminService(user_repo, log_repo, component_repo)

    try:
        result = admin_service.saveComponent(body)
        admin_service._recordAdminOperation(
            current_admin.user_id, "新增元器件",
            f"型号: {body.model}"
        )
        return success(data=result.model_dump(), message="新增元器件成功")
    except ValueError as e:
        return error(400, str(e))


@component_router.put("/{componentId}")
def updateComponent(
    componentId: str,
    body: ComponentUpdateRequest,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """更新元器件及参数"""
    user_repo = UserRepository(db)
    log_repo = HistoryRepository(db)
    component_repo = ComponentRepository(db)
    admin_service = AdminService(user_repo, log_repo, component_repo)

    try:
        result = admin_service.updateComponent(componentId, body)
        admin_service._recordAdminOperation(
            current_admin.user_id, "编辑元器件",
            f"编号: {componentId}"
        )
        return success(data=result.model_dump(), message="更新元器件成功")
    except ValueError as e:
        return error(400, str(e))


@component_router.delete("/{componentId}")
def deleteComponent(
    componentId: str,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """删除元器件及参数"""
    user_repo = UserRepository(db)
    log_repo = HistoryRepository(db)
    component_repo = ComponentRepository(db)
    admin_service = AdminService(user_repo, log_repo, component_repo)

    try:
        admin_service.deleteComponent(componentId)
        admin_service._recordAdminOperation(
            current_admin.user_id, "删除元器件",
            f"编号: {componentId}"
        )
        return success(message="删除元器件成功")
    except ValueError as e:
        return error(404, str(e))


# ── 工艺规范管理接口（设计文档 AdminController.manageStandard）──────

@standard_router.get("")
def getStandardList(
    standardName: Optional[str] = Query(None, description="规范名称筛选"),
    standardCode: Optional[str] = Query(None, description="规范编号筛选"),
    pageNum: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """分页查询规范列表"""
    user_repo = UserRepository(db)
    log_repo = HistoryRepository(db)
    standard_repo = StandardRepository(db)
    admin_service = AdminService(user_repo, log_repo, standard_repo=standard_repo)

    result = admin_service.getStandards(
        standardName=standardName,
        standardCode=standardCode,
        pageNum=pageNum,
        pageSize=pageSize,
    )
    return success(data=result, message="查询成功")


@standard_router.post("")
def createStandard(
    body: StandardCreateRequest,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """新增规范"""
    user_repo = UserRepository(db)
    log_repo = HistoryRepository(db)
    standard_repo = StandardRepository(db)
    admin_service = AdminService(user_repo, log_repo, standard_repo=standard_repo)

    try:
        result = admin_service.saveStandard(body)
        admin_service._recordAdminOperation(
            current_admin.user_id, "新增规范",
            f"名称: {body.standardName}"
        )
        return success(data=result.model_dump(), message="新增规范成功")
    except ValueError as e:
        return error(400, str(e))


@standard_router.put("/{standardId}")
def updateStandard(
    standardId: str,
    body: StandardUpdateRequest,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """更新规范"""
    user_repo = UserRepository(db)
    log_repo = HistoryRepository(db)
    standard_repo = StandardRepository(db)
    admin_service = AdminService(user_repo, log_repo, standard_repo=standard_repo)

    try:
        result = admin_service.updateStandard(standardId, body)
        admin_service._recordAdminOperation(
            current_admin.user_id, "编辑规范",
            f"编号: {standardId}"
        )
        return success(data=result.model_dump(), message="更新规范成功")
    except ValueError as e:
        return error(400, str(e))


@standard_router.delete("/{standardId}")
def deleteStandard(
    standardId: str,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """删除规范"""
    user_repo = UserRepository(db)
    log_repo = HistoryRepository(db)
    standard_repo = StandardRepository(db)
    admin_service = AdminService(user_repo, log_repo, standard_repo=standard_repo)

    try:
        admin_service.deleteStandard(standardId)
        admin_service._recordAdminOperation(
            current_admin.user_id, "删除规范",
            f"编号: {standardId}"
        )
        return success(message="删除规范成功")
    except ValueError as e:
        return error(404, str(e))


# ── 教程管理接口（设计文档 AdminController.manageTutorial）────────

@tutorial_router.get("")
def getTutorialList(
    processName: Optional[str] = Query(None, description="工艺名称筛选"),
    pageNum: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """分页查询教程列表"""
    user_repo = UserRepository(db)
    log_repo = HistoryRepository(db)
    tutorial_repo = TutorialRepository(db)
    admin_service = AdminService(user_repo, log_repo, tutorial_repo=tutorial_repo)

    result = admin_service.getTutorials(
        processName=processName,
        pageNum=pageNum,
        pageSize=pageSize,
    )
    return success(data=result, message="查询成功")


@tutorial_router.get("/{tutorialId}")
def getTutorialDetail(
    tutorialId: str,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """查看教程详情（含步骤）"""
    user_repo = UserRepository(db)
    log_repo = HistoryRepository(db)
    tutorial_repo = TutorialRepository(db)
    admin_service = AdminService(user_repo, log_repo, tutorial_repo=tutorial_repo)

    try:
        result = admin_service.getTutorialDetail(tutorialId)
        return success(data=result.model_dump(), message="查询成功")
    except ValueError as e:
        return error(404, str(e))


@tutorial_router.post("")
def createTutorial(
    body: TutorialCreateRequest,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """新增教程（含步骤）"""
    user_repo = UserRepository(db)
    log_repo = HistoryRepository(db)
    tutorial_repo = TutorialRepository(db)
    admin_service = AdminService(user_repo, log_repo, tutorial_repo=tutorial_repo)

    try:
        result = admin_service.saveTutorial(body)
        admin_service._recordAdminOperation(
            current_admin.user_id, "新增教程",
            f"名称: {body.processName}"
        )
        return success(data=result.model_dump(), message="新增教程成功")
    except ValueError as e:
        return error(400, str(e))


@tutorial_router.put("/{tutorialId}")
def updateTutorial(
    tutorialId: str,
    body: TutorialUpdateRequest,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """更新教程及步骤"""
    user_repo = UserRepository(db)
    log_repo = HistoryRepository(db)
    tutorial_repo = TutorialRepository(db)
    admin_service = AdminService(user_repo, log_repo, tutorial_repo=tutorial_repo)

    try:
        result = admin_service.updateTutorial(tutorialId, body)
        admin_service._recordAdminOperation(
            current_admin.user_id, "编辑教程",
            f"编号: {tutorialId}"
        )
        return success(data=result.model_dump(), message="更新教程成功")
    except ValueError as e:
        return error(400, str(e))


@tutorial_router.delete("/{tutorialId}")
def deleteTutorial(
    tutorialId: str,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """删除教程及步骤"""
    user_repo = UserRepository(db)
    log_repo = HistoryRepository(db)
    tutorial_repo = TutorialRepository(db)
    admin_service = AdminService(user_repo, log_repo, tutorial_repo=tutorial_repo)

    try:
        admin_service.deleteTutorial(tutorialId)
        admin_service._recordAdminOperation(
            current_admin.user_id, "删除教程",
            f"编号: {tutorialId}"
        )
        return success(message="删除教程成功")
    except ValueError as e:
        return error(404, str(e))


# ── 服务监控接口（设计文档 AdminController.getServiceMonitorData）───


@monitor_router.get("/monitor")
def getServiceMonitor(
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin),
):
    """获取各服务健康状态及近期运行统计"""
    history_repo = HistoryRepository(db)
    monitor_service = MonitorService(history_repo)

    service_status = monitor_service.getServiceStatus()
    api_stats = monitor_service.getApiStatistics(hours=24)
    latency_stats = monitor_service.getLatencyStats(hours=24)
    time_series = monitor_service.getTimeSeries(hours=24)
    error_logs = monitor_service.getErrorLogs(hours=24)

    return success(data={
        **service_status,
        "apiStats": api_stats,
        "latencyStats": latency_stats,
        "timeSeries": time_series,
        "recentErrors": error_logs,
    })
