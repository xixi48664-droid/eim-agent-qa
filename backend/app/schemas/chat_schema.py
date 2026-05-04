from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class ChatSessionRecord(BaseModel):
    sessionId: str
    title: str = ""
    createTime: Optional[datetime] = None
    updateTime: Optional[datetime] = None
    messageCount: int = 0


class ChatMessageRecord(BaseModel):
    messageId: str
    senderType: str
    content: str = ""
    imageUrl: Optional[str] = None
    sourceInfo: Optional[str] = None
    feedback: Optional[str] = None
    createTime: Optional[datetime] = None


class SessionDetail(BaseModel):
    sessionId: str
    title: str = ""
    messages: list[ChatMessageRecord] = []
