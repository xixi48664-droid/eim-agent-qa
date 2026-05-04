from typing import Optional
from pydantic import BaseModel


class FileUploadData(BaseModel):
    fileId: str
    fileName: str
    fileSize: int
    fileUrl: str
    uploadTime: Optional[str] = None
