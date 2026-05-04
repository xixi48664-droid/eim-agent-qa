from typing import Optional
from pydantic import BaseModel, ConfigDict


class StandardCreateRequest(BaseModel):
    standardCode: Optional[str] = None
    standardName: str
    section: Optional[str] = None
    summary: Optional[str] = None
    tags: Optional[str] = None
    relatedProcess: Optional[str] = None


class StandardUpdateRequest(BaseModel):
    standardCode: Optional[str] = None
    standardName: Optional[str] = None
    section: Optional[str] = None
    summary: Optional[str] = None
    tags: Optional[str] = None
    relatedProcess: Optional[str] = None


class StandardRecord(BaseModel):
    standardId: str
    standardCode: str = ""
    standardName: str
    section: str = ""
    summary: str = ""
    tags: str = ""
    relatedProcess: str = ""
