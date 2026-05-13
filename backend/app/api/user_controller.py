"""
认证接口 — 对应设计文档 4.1 UserController 类
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.mysql import get_db
from app.repositories.user_repository import UserRepository
from app.repositories.history_repository import HistoryRepository
from app.services.user_service import UserService
from app.services.history_service import HistoryService
from app.entities.operation_log import OperationLog
from app.schemas.auth_schema import LoginRequest
from app.schemas.user_schema import RegisterRequest, UpdateProfileRequest, ChangePasswordRequest, ForgotPasswordRequest, ResetPasswordByTokenRequest
from app.core.response import success, error
from app.core.security import get_current_user

router = APIRouter(prefix="/api/v1/auth", tags=["认证"])
user_router = APIRouter(prefix="/api/v1/user", tags=["个人中心"])


# ── 认证接口 ────────────────────────────────────────────────

@router.post("/login")
def login(loginForm: LoginRequest, db: Session = Depends(get_db)):
    """
    用户登录 — 对应设计文档 UserController.login
    接口文档 3.1 节
    """
    if not loginForm.account or not loginForm.password:
        return error(400, "账号和密码不能为空")

    user_repo = UserRepository(db)
    log_repo = HistoryRepository(db)
    user_service = UserService(user_repo)

    try:
        result = user_service.authenticate(
            loginForm.account, loginForm.password, log_repo
        )
        return success(data=result.model_dump(), message="登录成功")
    except ValueError as e:
        msg = str(e)
        if msg == "账号已被禁用":
            return error(403, msg)
        return error(401, msg)


@router.post("/register")
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    """
    用户注册 — 对应设计文档 UserController.register
    """
    user_repo = UserRepository(db)
    log_repo = HistoryRepository(db)
    user_service = UserService(user_repo)

    try:
        result = user_service.createUser(
            account=body.account,
            username=body.username,
            password=body.password,
            log_repo=log_repo,
        )
        return success(data=result.model_dump(), message="注册成功")
    except ValueError as e:
        return error(400, str(e))


@router.post("/logout")
def logout(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    用户登出 — 对应设计文档 UserController.logout
    """
    log_repo = HistoryRepository(db)
    log_repo.saveOperationLog(OperationLog(
        user_id=current_user.user_id,
        operation_type="登出",
        operation_target="系统",
        operation_result="成功",
    ))
    return success(message="已登出")


@router.post("/forgot-password")
def forgotPassword(
    body: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    """忘记密码 — 发送重置令牌"""
    user_repo = UserRepository(db)
    user_service = UserService(user_repo)

    try:
        token = user_service.forgotPassword(body.email)
        return success(
            data={"resetToken": token},
            message="重置令牌已生成（生产环境将通过邮件发送）",
        )
    except ValueError as e:
        return error(404, str(e))


@router.post("/reset-password")
def resetPasswordByToken(
    body: ResetPasswordByTokenRequest,
    db: Session = Depends(get_db),
):
    """通过重置令牌修改密码"""
    user_repo = UserRepository(db)
    user_service = UserService(user_repo)

    try:
        user_service.resetPasswordByToken(body.email, body.token, body.newPassword)
        return success(message="密码重置成功，请使用新密码登录")
    except ValueError as e:
        return error(400, str(e))


# ── 个人中心接口 ────────────────────────────────────────────

@user_router.get("/profile")
def getProfile(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """查看个人信息"""
    user_repo = UserRepository(db)
    log_repo = HistoryRepository(db)
    user_service = UserService(user_repo)

    try:
        result = user_service.getUserById(current_user.user_id, log_repo)
        return success(data=result.model_dump(), message="查询成功")
    except ValueError as e:
        return error(404, str(e))


@user_router.put("/profile")
def updateProfile(
    body: UpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """编辑个人信息"""
    user_repo = UserRepository(db)
    user_service = UserService(user_repo)

    try:
        result = user_service.updateProfile(
            user_id=current_user.user_id,
            username=body.username,
            email=body.email,
            phone=body.phone,
            department=body.department,
            avatar=body.avatar,
        )
        return success(data=result.model_dump(), message="更新成功")
    except ValueError as e:
        return error(400, str(e))


@user_router.post("/change-password")
def resetPassword(
    body: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """自行修改密码 — 对应设计文档 UserController.resetPassword"""
    user_repo = UserRepository(db)
    user_service = UserService(user_repo)

    try:
        user_service.changePassword(
            user_id=current_user.user_id,
            old_password=body.oldPassword,
            new_password=body.newPassword,
        )
        return success(message="密码修改成功")
    except ValueError as e:
        return error(400, str(e))


@user_router.get("/stats")
def getStats(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """活动统计"""
    user_repo = UserRepository(db)
    log_repo = HistoryRepository(db)
    user_service = UserService(user_repo)

    result = user_service.getUserStats(current_user.user_id, log_repo)
    return success(data=result.model_dump(), message="查询成功")


@user_router.get("/activities")
def getActivities(
    pageNum: int = 1,
    pageSize: int = 10,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """近期操作记录 — 对应设计文档 HistoryService.getUserActivities"""
    log_repo = HistoryRepository(db)
    history_service = HistoryService(log_repo)

    result = history_service.getUserActivities(
        user_id=current_user.user_id,
        pageNum=pageNum,
        pageSize=pageSize,
    )
    return success(data=result, message="查询成功")
