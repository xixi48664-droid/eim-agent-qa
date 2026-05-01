from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """登录请求 — 对应接口文档 3.1 节"""
    account: str = Field(..., description="邮箱或手机号")
    password: str = Field(..., description="登录密码")


class LoginData(BaseModel):
    """登录响应 data — 对应接口文档 3.1 节成功响应"""
    token: str
    userId: str
    account: str
    role: str
    status: str
