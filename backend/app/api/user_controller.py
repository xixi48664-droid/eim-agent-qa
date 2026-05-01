"""
认证接口 — 对应设计文档 4.1 UserController 类
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.mysql import get_db
from app.repositories.user_repository import UserRepository
from app.repositories.history_repository import HistoryRepository
from app.services.user_service import UserService
from app.schemas.auth_schema import LoginRequest
from app.core.response import success, error

router = APIRouter(prefix="/api/v1/auth", tags=["认证"])


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
