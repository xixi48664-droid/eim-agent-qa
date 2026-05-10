"""
参数查询接口 — 对应设计文档 4.3 QaController 类
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.mysql import get_db
from app.core.security import get_current_user
from app.repositories.component_repository import ComponentRepository
from app.services.query_service import QueryService
from app.core.response import success, error

router = APIRouter(prefix="/api/v1/components", tags=["参数查询"])


@router.get("/search")
def searchByKeyword(
    keyword: str = Query(..., description="元器件型号或关键词"),
    type: Optional[str] = Query(None, description="元器件类型筛选"),
    pageNum: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(10, ge=1, le=100, description="每页条数"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    元器件搜索 — 对应接口文档 5.1 节
    """
    component_repo = ComponentRepository(db)
    query_service = QueryService(component_repo)

    try:
        result = query_service.searchByKeyword(keyword, pageNum, pageSize, type)
        if result["total"] == 0:
            return error(404, "未查询到匹配的元器件")
        return success(data=result, message="查询成功")
    except ValueError as e:
        return error(400, str(e))


@router.get("/{componentId}")
def getComponentDetail(
    componentId: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    元器件参数详情 — 对应接口文档 5.2 节
    """
    component_repo = ComponentRepository(db)
    query_service = QueryService(component_repo)

    try:
        result = query_service.getComponentDetail(componentId)
        return success(data=result.model_dump(), message="查询成功")
    except ValueError as e:
        return error(404, str(e))
