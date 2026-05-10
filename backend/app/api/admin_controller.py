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
from app.services.admin_service import AdminService
from app.schemas.user_schema import UserStatusUpdate, ResetPasswordRequest
from app.core.response import success, error

router = APIRouter(prefix="/api/v1/admin/users", tags=["用户管理"])


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
