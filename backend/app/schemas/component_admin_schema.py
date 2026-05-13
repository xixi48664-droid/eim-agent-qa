from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime


class ParamItem(BaseModel):
    paramName: str = Field(validation_alias="param_name")
    paramValue: str = Field(validation_alias="param_value")
    paramUnit: Optional[str] = Field(default=None, validation_alias="param_unit")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ComponentCreateRequest(BaseModel):
    model: str
    type: Optional[str] = None
    packageType: Optional[str] = Field(default=None, validation_alias="package_type")
    manufacturer: Optional[str] = None
    datasheetUrl: Optional[str] = Field(default=None, validation_alias="datasheet_url")
    imageUrl: Optional[str] = Field(default=None, validation_alias="image_url")
    params: list[ParamItem] = []

    model_config = ConfigDict(populate_by_name=True)


class ComponentUpdateRequest(BaseModel):
    model: Optional[str] = None
    type: Optional[str] = None
    packageType: Optional[str] = Field(default=None, validation_alias="package_type")
    manufacturer: Optional[str] = None
    datasheetUrl: Optional[str] = Field(default=None, validation_alias="datasheet_url")
    imageUrl: Optional[str] = Field(default=None, validation_alias="image_url")
    params: Optional[list[ParamItem]] = None

    model_config = ConfigDict(populate_by_name=True)


class ComponentAdminRecord(BaseModel):
    componentId: str
    model: str
    type: str = ""
    packageType: str = ""
    manufacturer: str = ""
    datasheetUrl: Optional[str] = None
    imageUrl: Optional[str] = None
    paramCount: int = 0
    createTime: Optional[datetime] = None
    updateTime: Optional[datetime] = None

    model_config = ConfigDict(populate_by_name=True)
