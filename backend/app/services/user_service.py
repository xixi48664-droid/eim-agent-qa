import uuid
from app.repositories.user_repository import UserRepository
from app.repositories.history_repository import HistoryRepository
from app.entities.user import User
from app.entities.operation_log import OperationLog
import secrets
from datetime import datetime, timedelta
from app.utils.password import verify_password, hash_password
from app.utils.token import create_access_token
from app.schemas.auth_schema import LoginData
from app.schemas.user_schema import (
    RegisterData,
    UserProfileData,
    UserStatsData,
)


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

        user.last_login_time = datetime.utcnow()
        self._userRepository.update(user)

        if log_repo:
            login_log = OperationLog(
                user_id=user.user_id,
                operation_type="登录",
                operation_target="系统",
                operation_result="成功",
            )
            log_repo.saveOperationLog(login_log)

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

    # ── 注册 ────────────────────────────────────────────────

    def createUser(
        self, account: str, username: str, password: str, log_repo: HistoryRepository = None
    ) -> RegisterData:
        """注册新用户 — 对应设计文档 UserService.createUser"""
        # 检查账号唯一性
        existing = self._userRepository.findByAccount(account)
        if existing:
            raise ValueError("该邮箱或手机号已被注册")

        # 检查用户名唯一性
        existing = self._userRepository.findByUsername(username)
        if existing:
            raise ValueError("该用户名已被使用")

        # 判断账号类型
        email = account if "@" in account else None
        phone = account if "@" not in account else None

        user = User(
            user_id=uuid.uuid4().hex,
            username=username,
            password=hash_password(password),
            email=email,
            phone=phone,
            role="user",
            status="enabled",
        )
        self._userRepository.save(user)

        if log_repo:
            log_repo.saveOperationLog(OperationLog(
                user_id=user.user_id,
                operation_type="注册",
                operation_target="系统",
                operation_result="成功",
            ))

        return RegisterData(
            userId=user.user_id,
            username=user.username,
            account=account,
        )

    # ── 个人中心 ────────────────────────────────────────────

    def getUserById(self, user_id: str, log_repo: HistoryRepository = None) -> UserProfileData:
        """查看个人信息 — 对应设计文档 UserService.getUserById"""
        user = self._userRepository.findById(user_id)
        if not user:
            raise ValueError("用户不存在")

        stats = self.getUserStats(user_id, log_repo)

        return UserProfileData(
            userId=user.user_id,
            username=user.username,
            email=user.email or "",
            phone=user.phone or "",
            role=user.role,
            status=user.status,
            registerTime=user.create_time,
            lastLoginTime=user.last_login_time,
            department=user.department or "",
            avatar=user.avatar or "",
            questionCount=stats.questionCount,
            savedRecordCount=stats.savedRecordCount,
            exportReportCount=stats.exportReportCount,
            satisfactionScore=stats.satisfactionScore,
        )

    def updateProfile(self, user_id: str, username: str | None, email: str | None, phone: str | None, department: str | None = None, avatar: str | None = None) -> UserProfileData:
        """编辑个人信息 — 对应设计文档 个人中心"""
        user = self._userRepository.findById(user_id)
        if not user:
            raise ValueError("用户不存在")

        if username is not None and username != user.username:
            existing = self._userRepository.findByUsername(username)
            if existing:
                raise ValueError("该用户名已被使用")
            user.username = username
        if email is not None and email != user.email:
            existing = self._userRepository.findByEmail(email)
            if existing:
                raise ValueError("该邮箱已被使用")
            user.email = email
        if phone is not None and phone != user.phone:
            existing = self._userRepository.findByPhone(phone)
            if existing:
                raise ValueError("该手机号已被使用")
            user.phone = phone
        if department is not None:
            user.department = department
        if avatar is not None:
            user.avatar = avatar

        self._userRepository.update(user)
        return self.getUserById(user_id)

    def changePassword(self, user_id: str, old_password: str, new_password: str) -> None:
        """自行修改密码 — 对应设计文档 UserService.changePassword"""
        user = self._userRepository.findById(user_id)
        if not user:
            raise ValueError("用户不存在")

        if not verify_password(old_password, user.password):
            raise ValueError("原密码错误")

        user.password = hash_password(new_password)
        self._userRepository.update(user)

    def getUserStats(self, user_id: str, log_repo: HistoryRepository = None) -> UserStatsData:
        """活动统计"""
        question_count = 0
        saved_count = 0
        like_count = 0
        total_feedback = 0
        if log_repo:
            question_count = log_repo.countUserMessages(user_id)
            saved_count = log_repo.countSessionsByUser(user_id)
            like_count = log_repo.countUserLikes(user_id)
            total_feedback = log_repo.countUserFeedback(user_id)

        score = 5.0
        if total_feedback > 0:
            score = round(like_count / total_feedback * 5.0, 1)

        return UserStatsData(
            totalOperations=self._userRepository.countOperationsByUser(user_id),
            loginCount=self._userRepository.countOperationsByType(user_id, "登录"),
            questionCount=question_count,
            savedRecordCount=saved_count,
            exportReportCount=0,
            satisfactionScore=score,
        )

    # ── 忘记密码 ────────────────────────────────────────────

    def forgotPassword(self, email: str) -> str:
        """生成密码重置令牌"""
        user = self._userRepository.findByEmail(email)
        if not user:
            raise ValueError("该邮箱未注册")

        token = secrets.token_urlsafe(32)
        user.reset_token = token
        user.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        self._userRepository.update(user)

        # 生产环境应发送邮件，此处返回 token 便于开发测试
        return token

    def resetPasswordByToken(self, email: str, token: str, new_password: str) -> None:
        """通过重置令牌修改密码"""
        user = self._userRepository.findByEmail(email)
        if not user:
            raise ValueError("该邮箱未注册")
        if user.reset_token != token:
            raise ValueError("重置令牌无效")
        if user.reset_token_expiry and user.reset_token_expiry < datetime.utcnow():
            raise ValueError("重置令牌已过期")

        user.password = hash_password(new_password)
        user.reset_token = None
        user.reset_token_expiry = None
        self._userRepository.update(user)
