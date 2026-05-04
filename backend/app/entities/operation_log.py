import uuid
from sqlalchemy import Column, String, DateTime, ForeignKey, func
from app.db.mysql import Base


def _gen_id() -> str:
    return uuid.uuid4().hex


class OperationLog(Base):
    """操作日志 — 对应设计文档 4.30 OperationLog 类 & 表9"""
    __tablename__ = "operation_log"

    log_id = Column(String(32), primary_key=True, default=_gen_id)
    user_id = Column(String(32), ForeignKey("user.user_id"), nullable=True)
    operation_type = Column(String(100), nullable=False)
    operation_target = Column(String(100), nullable=True)
    operation_time = Column(DateTime, server_default=func.now(), nullable=False)
    operation_result = Column(String(50), nullable=True)
    response_time_ms = Column(String(20), nullable=True)
