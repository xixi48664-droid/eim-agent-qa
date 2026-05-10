from typing import Optional
from app.repositories.component_repository import ComponentRepository
from app.schemas.component_schema import ComponentSummary, ComponentDetail


class QueryService:
    """元器件参数查询业务 — 对应设计文档 4.10 QueryService 类"""

    def __init__(self, component_repo: ComponentRepository):
        self._componentRepository = component_repo

    def searchByKeyword(
        self, keyword: str, pageNum: int = 1, pageSize: int = 10, type: str = None
    ) -> dict:
        """根据关键词查询元器件 — 对应设计文档 QueryService.searchByKeyword"""
        keyword = keyword.strip()
        if not keyword:
            raise ValueError("关键词不能为空")

        components, total = self._componentRepository.searchByKeyword(
            keyword, pageNum, pageSize, type
        )

        records = []
        for c in components:
            params = self._componentRepository.getParams(c.component_id)
            coreParams = {}
            for p in params:
                value = p.param_value
                if p.param_unit:
                    value = f"{p.param_value}{p.param_unit}"
                coreParams[p.param_name] = value
            summary = ComponentSummary.model_validate(c).model_dump()
            summary["coreParams"] = coreParams if coreParams else None
            records.append(summary)
        return {
            "pageNum": pageNum,
            "pageSize": pageSize,
            "total": total,
            "records": records,
        }

    def getComponentDetail(self, componentId: str) -> ComponentDetail:
        """查询元器件详细信息 — 对应设计文档 QueryService.getComponentDetail"""
        component = self._componentRepository.findById(componentId)
        if not component:
            raise ValueError("元器件不存在")

        params = self._componentRepository.getParams(componentId)

        coreParams = {}
        for p in params:
            value = p.param_value
            if p.param_unit:
                value = f"{p.param_value}{p.param_unit}"
            coreParams[p.param_name] = value

        return ComponentDetail(
            componentId=component.component_id,
            model=component.model,
            type=component.type or "",
            packageType=component.package_type or "",
            manufacturer=component.manufacturer or "",
            coreParams=coreParams if coreParams else None,
            datasheetUrl=component.datasheet_url,
            imageUrl=component.image_url,
            updatedAt=component.create_time,
        )
