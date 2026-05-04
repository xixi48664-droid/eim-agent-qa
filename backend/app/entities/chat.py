import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from app.db.mysql import Base


def _gen_id() -> str:
    return uuid.uuid4().hex


class ChatSession(Base):
    __tablename__ = "chat_session"

    session_id = Column(String(32), primary_key=True, default=_gen_id)
    user_id = Column(String(32), ForeignKey("user.user_id"), nullable=False)
    title = Column(String(200), nullable=True)
    create_time = Column(DateTime, server_default=func.now())
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now())

    messages = relationship("ChatMessage", back_populates="session")


class ChatMessage(Base):
    __tablename__ = "chat_message"

    message_id = Column(String(32), primary_key=True, default=_gen_id)
    session_id = Column(String(32), ForeignKey("chat_session.session_id"), nullable=False)
    sender_type = Column(String(20), nullable=False)
    content = Column(Text, nullable=True)
    image_url = Column(String(255), nullable=True)
    source_info = Column(Text, nullable=True)
    feedback = Column(String(20), nullable=True)
    create_time = Column(DateTime, server_default=func.now())

    session = relationship("ChatSession", back_populates="messages")
