from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class UserRecord(BaseModel):
    """用户列表中的单条记录 — 对应接口文档 4.1 节"""
    userId: str = Field(validation_alias="user_id")
    username: str
    email: str = ""
    status: str
    registerTime: Optional[datetime] = Field(default=None, validation_alias="create_time")
    lastLoginTime: Optional[datetime] = Field(default=None, validation_alias="last_login_time")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class UserStatusUpdate(BaseModel):
    """启用/禁用用户 — 对应接口文档 4.2 节"""
    status: str = Field(..., pattern="^(enabled|disabled)$")


class UserStatusData(BaseModel):
    userId: str
    status: str


class ResetPasswordRequest(BaseModel):
    """重置密码请求 — 对应接口文档 4.3 节"""
    password: str | None = None


class ResetPasswordData(BaseModel):
    """重置密码响应 — 对应接口文档 4.3 节"""
    userId: str
    tempPassword: str


class OperationLogRecord(BaseModel):
    """操作日志单条记录 — 对应接口文档 4.4 节"""
    logId: str = Field(validation_alias="log_id")
    operationType: str = Field(validation_alias="operation_type")
    operationDesc: str
    operationTime: Optional[datetime] = Field(default=None, validation_alias="operation_time")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
