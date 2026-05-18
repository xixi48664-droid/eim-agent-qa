"""Datasheet 处理状态跟踪表"""
import uuid
from sqlalchemy import Column, String, Integer, DateTime, Text, func
from app.db.mysql import Base


def _gen_id() -> str:
    return uuid.uuid4().hex


class DatasheetRecord(Base):
    __tablename__ = "datasheet_record"

    record_id = Column(String(32), primary_key=True, default=_gen_id)
    component_id = Column(String(32), nullable=False, index=True)
    source_url = Column(String(1000), nullable=False)
    local_path = Column(String(500), nullable=True)
    file_hash = Column(String(64), nullable=True, index=True)
    status = Column(
        String(20), nullable=False, default="pending", index=True,
        comment="pending/downloaded/parsed/embedded/failed"
    )
    chunk_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    create_time = Column(DateTime, server_default=func.now())
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now())
