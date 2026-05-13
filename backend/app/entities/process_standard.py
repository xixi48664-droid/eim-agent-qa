import uuid
from sqlalchemy import Column, String, Text
from app.db.mysql import Base


def _gen_id() -> str:
    return uuid.uuid4().hex


class ProcessStandard(Base):
    __tablename__ = "process_standard"

    standard_id = Column(String(32), primary_key=True, default=_gen_id)
    standard_code = Column(String(100), nullable=True)
    standard_name = Column(String(200), nullable=False)
    section = Column(String(100), nullable=True)
    summary = Column(Text, nullable=True)
    tags = Column(String(255), nullable=True)
    related_process = Column(String(255), nullable=True)
