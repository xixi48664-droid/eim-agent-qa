import re
from typing import Optional
from app.repositories.component_repository import ComponentRepository
from app.schemas.component_schema import ComponentSummary, ComponentDetail

# 匹配元器件型号的正则：字母数字组合，含连字符、斜杠、逗号等
_MODEL_PATTERN = re.compile(
    r'\b([A-Za-z0-9][-A-Za-z0-9/+,.()]{2,30}[A-Za-z0-9])\b',
    flags=re.ASCII,
)


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

        # 从自然语言问句中提取型号，例如 "ANNA-B402-00B 的供电电压" → "ANNA-B402-00B"
        search_keyword = self._extractModel(keyword)

        components, total = self._componentRepository.searchByKeyword(
            search_keyword, pageNum, pageSize, type
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
            summary = ComponentSummary(
                componentId=c.component_id,
                model=c.model,
                type=c.type or "",
                packageType=c.package_type or "",
                manufacturer=c.manufacturer or "",
                coreParams=coreParams if coreParams else None,
                imageUrl=c.image_url,
            ).model_dump()
            records.append(summary)
        return {
            "pageNum": pageNum,
            "pageSize": pageSize,
            "total": total,
            "records": records,
        }

    def _extractModel(self, text: str) -> str:
        """从自然语言问句中提取元器件型号。
        "ANNA-B402-00B 的供电电压" → "ANNA-B402-00B"
        如果没提取到型号，返回原始文本。
        """
        matches = _MODEL_PATTERN.findall(text)
        if not matches:
            return text
        matches.sort(key=len, reverse=True)
        return matches[0]

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
            updatedAt=component.update_time or component.create_time,
        )
