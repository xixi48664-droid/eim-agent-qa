from typing import Optional, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.entities.component_info import Component, ComponentParam


class ComponentRepository:
    """元器件数据访问 — 对应设计文档 4.17 ComponentRepository 类"""

    def __init__(self, db: Session):
        self._db = db

    def findByModel(self, model: str) -> Optional[Component]:
        """按型号查询元器件 — 对应设计文档 findByModel"""
        return self._db.query(Component).filter(Component.model == model).first()

    def findById(self, component_id: str) -> Optional[Component]:
        """按编号查询元器件"""
        return (
            self._db.query(Component)
            .filter(Component.component_id == component_id)
            .first()
        )

    def searchByKeyword(
        self, keyword: str, pageNum: int = 1, pageSize: int = 10
    ) -> Tuple[List[Component], int]:
        """按关键词模糊查询 — 对应设计文档 searchByKeyword"""
        query = self._db.query(Component).filter(
            or_(
                Component.model.like(f"%{keyword}%"),
                Component.type.like(f"%{keyword}%"),
                Component.manufacturer.like(f"%{keyword}%"),
            )
        )

        total = query.count()
        components = (
            query.order_by(Component.create_time.desc())
            .offset((pageNum - 1) * pageSize)
            .limit(pageSize)
            .all()
        )
        return components, total

    def getParams(self, component_id: str) -> List[ComponentParam]:
        """查询参数列表 — 对应设计文档 getParams"""
        return (
            self._db.query(ComponentParam)
            .filter(ComponentParam.component_id == component_id)
            .all()
        )

    def save(self, component: Component) -> Component:
        """保存元器件记录 — 对应设计文档 save"""
        self._db.add(component)
        self._db.commit()
        self._db.refresh(component)
        return component
