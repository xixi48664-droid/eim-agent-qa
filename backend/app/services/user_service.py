from datetime import datetime
from app.repositories.user_repository import UserRepository
from app.repositories.history_repository import HistoryRepository
from app.entities.operation_log import OperationLog
from app.utils.password import verify_password
from app.utils.token import create_access_token
from app.schemas.auth_schema import LoginData


class UserService:
    """认证业务逻辑 — 对应设计文档 4.8 UserService 类"""

    def __init__(self, user_repo: UserRepository):
        self._userRepository = user_repo

    def authenticate(
        self, account: str, password: str, log_repo: HistoryRepository = None
    ) -> LoginData:
        """校验用户身份 — 对应设计文档 UserService.authenticate"""
        user = self._userRepository.findByAccount(account)
        if not user:
            raise ValueError("账号或密码错误")

        if user.status != "enabled":
            raise ValueError("账号已被禁用")

        if not verify_password(password, user.password):
            raise ValueError("账号或密码错误")

        # 更新最后登录时间
        user.last_login_time = datetime.utcnow()
        self._userRepository.update(user)

        # 记录登录日志
        if log_repo:
            login_log = OperationLog(
                user_id=user.user_id,
                operation_type="登录",
                operation_target="系统",
                operation_result="成功",
            )
            log_repo.save(login_log)

        token = create_access_token(
            data={"sub": user.user_id, "role": user.role}
        )

        return LoginData(
            token=token,
            userId=user.user_id,
            account=account,
            role=user.role,
            status=user.status,
        )
