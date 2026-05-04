from typing import Optional, Tuple, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.entities.user import User


class UserRepository:
    """用户数据访问 — 对应设计文档 4.16 UserRepository 类"""

    def __init__(self, db: Session):
        self._db = db

    def findById(self, user_id: str) -> Optional[User]:
        """按用户编号查询 — 对应设计文档 findById"""
        return self._db.query(User).filter(User.user_id == user_id).first()

    def findByAccount(self, account: str) -> Optional[User]:
        """按账号查询（邮箱或手机号）— 对应设计文档 findByAccount"""
        return self._db.query(User).filter(
            or_(User.email == account, User.phone == account)
        ).first()

    def findUsers(
        self,
        username: Optional[str] = None,
        email: Optional[str] = None,
        status: Optional[str] = None,
        registerStart: Optional[datetime] = None,
        registerEnd: Optional[datetime] = None,
        pageNum: int = 1,
        pageSize: int = 10,
    ) -> Tuple[List[User], int]:
        """分页查询用户列表 — 对应接口文档 4.1 节"""
        query = self._db.query(User)

        if username:
            query = query.filter(User.username.like(f"%{username}%"))
        if email:
            query = query.filter(User.email.like(f"%{email}%"))
        if status:
            query = query.filter(User.status == status)
        if registerStart:
            query = query.filter(User.create_time >= registerStart)
        if registerEnd:
            query = query.filter(User.create_time <= registerEnd)

        total = query.count()
        users = (
            query.order_by(User.create_time.desc())
            .offset((pageNum - 1) * pageSize)
            .limit(pageSize)
            .all()
        )
        return users, total

    def save(self, user: User) -> User:
        """保存用户对象 — 对应设计文档 save"""
        self._db.add(user)
        self._db.commit()
        self._db.refresh(user)
        return user

    def update(self, user: User) -> User:
        """更新用户对象 — 对应设计文档 update"""
        self._db.commit()
        self._db.refresh(user)
        return user
