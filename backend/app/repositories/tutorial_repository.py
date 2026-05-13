from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from app.entities.tutorial import Tutorial, TutorialStep


class TutorialRepository:
    """流程教程数据访问 — 对应设计文档 4.20 TutorialRepository 类"""

    def __init__(self, db: Session):
        self._db = db

    def findByProcessName(self, process_name: str) -> Optional[Tutorial]:
        return self._db.query(Tutorial).filter(
            Tutorial.process_name == process_name
        ).first()

    def findById(self, tutorial_id: str) -> Optional[Tutorial]:
        return self._db.query(Tutorial).filter(
            Tutorial.tutorial_id == tutorial_id
        ).first()

    def getSteps(self, tutorial_id: str) -> List[TutorialStep]:
        return (
            self._db.query(TutorialStep)
            .filter(TutorialStep.tutorial_id == tutorial_id)
            .order_by(TutorialStep.step_no)
            .all()
        )

    def searchAdmin(
        self,
        processName: Optional[str] = None,
        pageNum: int = 1,
        pageSize: int = 10,
    ) -> Tuple[List[Tutorial], int]:
        query = self._db.query(Tutorial)

        if processName:
            query = query.filter(Tutorial.process_name.like(f"%{processName}%"))

        total = query.count()
        records = (
            query.order_by(Tutorial.process_name)
            .offset((pageNum - 1) * pageSize)
            .limit(pageSize)
            .all()
        )
        return records, total

    def save(self, tutorial: Tutorial) -> Tutorial:
        self._db.add(tutorial)
        self._db.commit()
        self._db.refresh(tutorial)
        return tutorial

    def saveSteps(self, steps: List[TutorialStep]) -> None:
        self._db.add_all(steps)
        self._db.commit()

    def deleteSteps(self, tutorial_id: str) -> None:
        self._db.query(TutorialStep).filter(
            TutorialStep.tutorial_id == tutorial_id
        ).delete()
        self._db.commit()

    def update(self, tutorial: Tutorial) -> Tutorial:
        self._db.commit()
        self._db.refresh(tutorial)
        return tutorial

    def delete(self, tutorial: Tutorial) -> None:
        self._db.delete(tutorial)
        self._db.commit()
