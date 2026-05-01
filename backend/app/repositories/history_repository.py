from typing import Optional, Tuple, List
from datetime import datetime
from sqlalchemy.orm import Session
from app.entities.operation_log import OperationLog


class HistoryRepository:
    """操作日志数据访问 — 对应设计文档 4.20 HistoryRepository 类"""

    def __init__(self, db: Session):
        self._db = db

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

    def save(self, log: OperationLog) -> OperationLog:
        """保存操作日志 — 对应设计文档 saveOperationLog"""
        self._db.add(log)
        self._db.commit()
        self._db.refresh(log)
        return log
