from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Dict
from datetime import datetime


class ComponentSummary(BaseModel):
    """元器件搜索摘要 — 对应接口文档 5.1 节"""
    componentId: str = Field(validation_alias="component_id")
    model: str
    type: str = ""
    packageType: str = Field(default="", validation_alias="package_type")
    manufacturer: str = ""
    coreParams: Optional[Dict[str, str]] = None

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ComponentDetail(BaseModel):
    """元器件参数详情 — 对应接口文档 5.2 节"""
    componentId: str = Field(validation_alias="component_id")
    model: str
    type: str = ""
    packageType: str = Field(default="", validation_alias="package_type")
    manufacturer: str = ""
    coreParams: Optional[Dict[str, str]] = None
    datasheetUrl: Optional[str] = Field(default=None, validation_alias="datasheet_url")
    imageUrl: Optional[str] = Field(default=None, validation_alias="image_url")
    updatedAt: Optional[datetime] = Field(default=None, validation_alias="create_time")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
