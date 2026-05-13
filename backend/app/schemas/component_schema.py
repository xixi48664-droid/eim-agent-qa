from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict
from datetime import datetime


class ComponentSummary(BaseModel):
    """元器件搜索摘要 — 对应接口文档 5.1 节"""
    componentId: str
    model: str
    type: str = ""
    packageType: str = ""
    manufacturer: str = ""
    coreParams: Optional[Dict[str, str]] = None

    model_config = ConfigDict(populate_by_name=True)


class ComponentDetail(BaseModel):
    """元器件参数详情 — 对应接口文档 5.2 节"""
    componentId: str
    model: str
    type: str = ""
    packageType: str = ""
    manufacturer: str = ""
    coreParams: Optional[Dict[str, str]] = None
    datasheetUrl: Optional[str] = None
    imageUrl: Optional[str] = None
    updatedAt: Optional[datetime] = None

    model_config = ConfigDict(populate_by_name=True)
