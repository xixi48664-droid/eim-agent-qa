import uuid
from sqlalchemy import Column, String, DateTime, func
from app.db.mysql import Base


def _gen_id() -> str:
    return uuid.uuid4().hex


class User(Base):
    __tablename__ = "user"

    user_id = Column(String(32), primary_key=True, default=_gen_id)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(100), nullable=False)
    email = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    role = Column(String(20), nullable=False, default="user")
    status = Column(String(20), nullable=False, default="enabled")
    create_time = Column(DateTime, server_default=func.now())
    last_login_time = Column(DateTime, nullable=True)
