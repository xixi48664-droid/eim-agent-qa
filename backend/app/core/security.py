from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.db.mysql import get_db
from app.utils.token import decode_access_token
from app.repositories.user_repository import UserRepository

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    """获取当前登录用户 — JWT 校验 + 用户状态校验"""
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Token无效或已过期")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token无效")

    user = UserRepository(db).findById(user_id)
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")

    if user.status != "enabled":
        raise HTTPException(status_code=403, detail="用户已被禁用")

    return user


def get_current_admin(current_user=Depends(get_current_user)):
    """获取当前管理员 — 要求 role=admin"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="无权限访问该接口")
    return current_user
