import uuid
from typing import Optional
from datetime import datetime
from app.repositories.history_repository import HistoryRepository
from app.entities.chat import ChatSession, ChatMessage
from app.schemas.user_schema import ActivityRecord
from app.schemas.chat_schema import (
    ChatSessionRecord,
    ChatMessageRecord,
    SessionDetail,
)


class HistoryService:
    """历史记录业务逻辑 — 对应设计文档 4.13 HistoryService 类"""

    def __init__(self, log_repo: HistoryRepository):
        self._historyRepository = log_repo

    # ── 操作日志 ──────────────────────────────────────────────

    def getUserActivities(
        self, user_id: str,
        pageNum: int = 1, pageSize: int = 10,
    ) -> dict:
        """查看用户近期操作记录 — 对应设计文档 HistoryService.getUserActivities"""
        logs, total = self._historyRepository.findByUser(
            user_id=user_id,
            pageNum=pageNum,
            pageSize=pageSize,
        )

        records = []
        for log in logs:
            desc = log.operation_type
            if log.operation_target:
                desc = f"{desc} {log.operation_target}"
            records.append(
                ActivityRecord(
                    logId=log.log_id,
                    operationType=log.operation_type,
                    operationDesc=desc,
                    operationTime=log.operation_time,
                ).model_dump()
            )

        return {
            "pageNum": pageNum,
            "pageSize": pageSize,
            "total": total,
            "records": records,
        }

    # ── 会话与消息 ────────────────────────────────────────────

    def saveSession(self, user_id: str, title: Optional[str] = None) -> ChatSession:
        """保存新会话"""
        session = ChatSession(
            session_id=uuid.uuid4().hex,
            user_id=user_id,
            title=title,
        )
        return self._historyRepository.saveSession(session)

    def saveMessage(
        self, session_id: str, sender_type: str, content: str,
        image_url: Optional[str] = None, source_info: Optional[str] = None,
    ) -> ChatMessage:
        """保存消息"""
        message = ChatMessage(
            message_id=uuid.uuid4().hex,
            session_id=session_id,
            sender_type=sender_type,
            content=content,
            image_url=image_url,
            source_info=source_info,
        )
        return self._historyRepository.saveMessage(message)

    def getHistoryByUser(self, user_id: str) -> list:
        """读取指定用户历史会话 — 对应设计文档 HistoryService.getHistoryByUser"""
        sessions = self._historyRepository.findSessionsByUser(user_id)
        records = []
        for s in sessions:
            msgs = self._historyRepository.findMessagesBySessionId(s.session_id)
            records.append(
                ChatSessionRecord(
                    sessionId=s.session_id,
                    title=s.title or "",
                    createTime=s.create_time,
                    updateTime=s.update_time,
                    messageCount=len(msgs),
                ).model_dump()
            )
        return records

    def getSessionDetail(self, session_id: str) -> SessionDetail:
        """读取会话详情及消息"""
        session = self._historyRepository.findSessionById(session_id)
        if not session:
            raise ValueError("会话不存在")

        messages = self._historyRepository.findMessagesBySessionId(session_id)
        msg_records = []
        for m in messages:
            msg_records.append(
                ChatMessageRecord(
                    messageId=m.message_id,
                    senderType=m.sender_type,
                    content=m.content or "",
                    imageUrl=m.image_url,
                    sourceInfo=m.source_info,
                    feedback=m.feedback,
                    createTime=m.create_time,
                )
            )

        return SessionDetail(
            sessionId=session.session_id,
            title=session.title or "",
            messages=msg_records,
        )

    def deleteSession(self, session_id: str) -> bool:
        """删除单条历史会话 — 对应设计文档 HistoryService.deleteSession"""
        if not self._historyRepository.existsById(session_id):
            raise ValueError("会话不存在")
        return self._historyRepository.deleteById(session_id)

    def batchDeleteSessions(self, session_ids: list[str]) -> dict:
        """批量删除历史会话 — 对应设计文档 HistoryService.batchDeleteSessions"""
        success_count = 0
        fail_count = 0
        for sid in session_ids:
            if self._historyRepository.existsById(sid):
                self._historyRepository.deleteById(sid)
                success_count += 1
            else:
                fail_count += 1
        return {"successCount": success_count, "failCount": fail_count}
