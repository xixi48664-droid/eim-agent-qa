from typing import Optional, Tuple, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.entities.operation_log import OperationLog
from app.entities.chat import ChatSession, ChatMessage


class HistoryRepository:
    """操作日志与历史数据访问 — 对应设计文档 4.21 HistoryRepository 类"""

    def __init__(self, db: Session):
        self._db = db

    # ── 操作日志 ─────────────────────────────────────────────

    def findByUser(
        self,
        user_id: str,
        operationType: Optional[str] = None,
        startTime: Optional[datetime] = None,
        endTime: Optional[datetime] = None,
        pageNum: int = 1,
        pageSize: int = 10,
    ) -> Tuple[List[OperationLog], int]:
        """按用户查询操作日志"""
        query = self._db.query(OperationLog).filter(
            OperationLog.user_id == user_id
        )

        if operationType:
            query = query.filter(OperationLog.operation_type == operationType)
        if startTime:
            query = query.filter(OperationLog.operation_time >= startTime)
        if endTime:
            query = query.filter(OperationLog.operation_time <= endTime)

        total = query.count()
        logs = (
            query.order_by(OperationLog.operation_time.desc())
            .offset((pageNum - 1) * pageSize)
            .limit(pageSize)
            .all()
        )
        return logs, total

    def saveOperationLog(self, log: OperationLog) -> OperationLog:
        """保存操作日志 — 对应设计文档 saveOperationLog"""
        self._db.add(log)
        self._db.commit()
        self._db.refresh(log)
        return log

    # ── 会话 ─────────────────────────────────────────────────

    def saveSession(self, session: ChatSession) -> ChatSession:
        self._db.add(session)
        self._db.commit()
        self._db.refresh(session)
        return session

    def saveMessage(self, message: ChatMessage) -> ChatMessage:
        self._db.add(message)
        self._db.commit()
        self._db.refresh(message)
        return message

    def findSessionsByUser(self, user_id: str) -> List[ChatSession]:
        return (
            self._db.query(ChatSession)
            .filter(ChatSession.user_id == user_id)
            .order_by(ChatSession.update_time.desc())
            .all()
        )

    def findSessionById(self, session_id: str) -> Optional[ChatSession]:
        return self._db.query(ChatSession).filter(
            ChatSession.session_id == session_id
        ).first()

    def findUserIdBySessionId(self, session_id: str) -> Optional[str]:
        session = self.findSessionById(session_id)
        return session.user_id if session else None

    def findMessagesBySessionId(self, session_id: str) -> List[ChatMessage]:
        return (
            self._db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.create_time)
            .all()
        )

    def deleteById(self, session_id: str) -> bool:
        session = self._db.query(ChatSession).filter(
            ChatSession.session_id == session_id
        ).first()
        if not session:
            return False
        self._db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).delete()
        self._db.delete(session)
        self._db.commit()
        return True

    def existsById(self, session_id: str) -> bool:
        return self._db.query(ChatSession).filter(
            ChatSession.session_id == session_id
        ).first() is not None

    def countSessionsByUser(self, user_id: str) -> int:
        return (
            self._db.query(ChatSession)
            .filter(ChatSession.user_id == user_id)
            .count()
        )

    def countUserMessages(self, user_id: str) -> int:
        return (
            self._db.query(ChatMessage)
            .join(ChatSession)
            .filter(
                ChatSession.user_id == user_id,
                ChatMessage.sender_type == "user",
            )
            .count()
        )

    def setMessageFeedback(self, message_id: str, feedback: str) -> bool:
        """设置消息反馈（like/dislike）"""
        msg = self._db.query(ChatMessage).filter(
            ChatMessage.message_id == message_id,
            ChatMessage.sender_type == "bot",
        ).first()
        if not msg:
            return False
        msg.feedback = feedback
        self._db.commit()
        return True

    def countUserLikes(self, user_id: str) -> int:
        """统计用户收到的 like 数"""
        return (
            self._db.query(ChatMessage)
            .join(ChatSession)
            .filter(
                ChatSession.user_id == user_id,
                ChatMessage.sender_type == "bot",
                ChatMessage.feedback == "like",
            )
            .count()
        )

    def countUserFeedback(self, user_id: str) -> int:
        """统计用户收到的总反馈数（like + dislike）"""
        return (
            self._db.query(ChatMessage)
            .join(ChatSession)
            .filter(
                ChatSession.user_id == user_id,
                ChatMessage.sender_type == "bot",
                ChatMessage.feedback.isnot(None),
            )
            .count()
        )
