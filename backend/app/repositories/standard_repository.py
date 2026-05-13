from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from app.entities.process_standard import ProcessStandard


class StandardRepository:
    """流程规范数据访问 — 对应设计文档 4.19 StandardRepository 类"""

    def __init__(self, db: Session):
        self._db = db

    def findById(self, standard_id: str) -> Optional[ProcessStandard]:
        return self._db.query(ProcessStandard).filter(
            ProcessStandard.standard_id == standard_id
        ).first()

    def searchByTags(self, tags: list[str]) -> List[ProcessStandard]:
        query = self._db.query(ProcessStandard)
        for tag in tags:
            query = query.filter(ProcessStandard.tags.like(f"%{tag}%"))
        return query.all()

    def searchAdmin(
        self,
        standardName: Optional[str] = None,
        standardCode: Optional[str] = None,
        pageNum: int = 1,
        pageSize: int = 10,
    ) -> Tuple[List[ProcessStandard], int]:
        query = self._db.query(ProcessStandard)

        if standardName:
            query = query.filter(ProcessStandard.standard_name.like(f"%{standardName}%"))
        if standardCode:
            query = query.filter(ProcessStandard.standard_code.like(f"%{standardCode}%"))

        total = query.count()
        records = (
            query.order_by(ProcessStandard.standard_code)
            .offset((pageNum - 1) * pageSize)
            .limit(pageSize)
            .all()
        )
        return records, total

    def save(self, standard: ProcessStandard) -> ProcessStandard:
        self._db.add(standard)
        self._db.commit()
        self._db.refresh(standard)
        return standard

    def update(self, standard: ProcessStandard) -> ProcessStandard:
        self._db.commit()
        self._db.refresh(standard)
        return standard

    def delete(self, standard: ProcessStandard) -> None:
        self._db.delete(standard)
        self._db.commit()
