from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Optional, Any
from datetime import datetime


class UserRecord(BaseModel):
    """用户列表中的单条记录 — 对应接口文档 4.1 节"""
    userId: str = Field(validation_alias="user_id")
    username: str
    email: str = ""
    status: str
    registerTime: Optional[datetime] = Field(default=None, validation_alias="create_time")
    lastLoginTime: Optional[datetime] = Field(default=None, validation_alias="last_login_time")
    department: Optional[str] = ""
    avatar: Optional[str] = ""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class UserStatusUpdate(BaseModel):
    """启用/禁用用户 — 对应接口文档 4.2 节"""
    status: str = Field(..., pattern="^(enabled|disabled)$")


class UserStatusData(BaseModel):
    userId: str
    status: str


class BatchUserStatusRequest(BaseModel):
    """批量修改用户状态请求"""
    userIds: list[str] = Field(..., min_length=1, description="用户编号列表")
    status: str = Field(..., pattern="^(enabled|disabled)$")


class BatchDeleteRequest(BaseModel):
    """批量删除用户请求"""
    userIds: list[str] = Field(..., min_length=1, description="用户编号列表")


class BatchResult(BaseModel):
    """批量操作结果"""
    affectedCount: int = 0
    failedIds: list[str] = []


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


# ── 用户注册 ────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    """用户注册请求 — 对应设计文档 UserController.register"""
    account: str = Field(..., description="邮箱或手机号")
    username: str = Field(..., min_length=1, description="用户名")
    password: str = Field(..., min_length=6, description="登录密码")
    confirmPassword: str = Field(..., min_length=6, description="确认密码")

    @model_validator(mode="after")
    def check_passwords_match(self) -> "RegisterRequest":
        if self.password != self.confirmPassword:
            raise ValueError("两次输入的密码不一致")
        return self


class RegisterData(BaseModel):
    """注册成功响应 — 对应接口文档"""
    userId: str
    username: str
    account: str


# ── 个人中心 ────────────────────────────────────────────────

class UserProfileData(BaseModel):
    """用户个人信息 — 对应设计文档 个人中心"""
    userId: str
    username: str
    email: str = ""
    phone: str = ""
    role: str
    status: str
    registerTime: Optional[datetime] = None
    lastLoginTime: Optional[datetime] = None
    department: str = ""
    avatar: str = ""
    questionCount: int = 0
    savedRecordCount: int = 0
    exportReportCount: int = 0
    satisfactionScore: float = 0.0


class UpdateProfileRequest(BaseModel):
    """编辑个人信息请求"""
    username: Optional[str] = Field(default=None, min_length=1)
    email: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    avatar: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    """自行修改密码请求 — 对应设计文档 UserController.resetPassword"""
    oldPassword: str
    newPassword: str = Field(..., min_length=6)
    confirmPassword: str = Field(..., min_length=6)

    @model_validator(mode="after")
    def check_passwords(self) -> "ChangePasswordRequest":
        if self.newPassword != self.confirmPassword:
            raise ValueError("两次输入的新密码不一致")
        if self.oldPassword == self.newPassword:
            raise ValueError("新密码不能与旧密码相同")
        return self


class UserStatsData(BaseModel):
    """用户活动统计"""
    totalOperations: int = 0
    loginCount: int = 0
    questionCount: int = 0
    savedRecordCount: int = 0
    exportReportCount: int = 0
    satisfactionScore: float = 0.0


class ActivityRecord(BaseModel):
    """用户活动记录"""
    logId: str
    operationType: str
    operationDesc: str
    operationTime: Optional[datetime] = None


# ── 忘记密码 ────────────────────────────────────────────────

class ForgotPasswordRequest(BaseModel):
    """忘记密码请求"""
    email: str = Field(..., description="注册邮箱")


class ResetPasswordByTokenRequest(BaseModel):
    """通过令牌重置密码请求"""
    email: str = Field(..., description="注册邮箱")
    token: str = Field(..., description="重置令牌")
    newPassword: str = Field(..., min_length=6)
    confirmPassword: str = Field(..., min_length=6)

    @model_validator(mode="after")
    def check_passwords(self) -> "ResetPasswordByTokenRequest":
        if self.newPassword != self.confirmPassword:
            raise ValueError("两次输入的新密码不一致")
        return self
