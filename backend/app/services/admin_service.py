import secrets
import string
from typing import Optional
from datetime import datetime
from app.repositories.user_repository import UserRepository
from app.repositories.history_repository import HistoryRepository
from app.utils.password import hash_password
from app.entities.operation_log import OperationLog
from app.schemas.user_schema import (
    UserRecord,
    UserStatusData,
    ResetPasswordData,
    OperationLogRecord,
)


class AdminService:
    """管理员业务逻辑 — 对应设计文档 4.14 AdminService 类"""

    def __init__(self, user_repo: UserRepository, log_repo: HistoryRepository):
        self._userRepository = user_repo
        self._logRepository = log_repo

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
        self._logRepository.save(log)


def _generate_temp_password(length: int = 8) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))
