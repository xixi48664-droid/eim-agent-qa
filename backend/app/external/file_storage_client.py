"""
文件存储服务适配器 — 对应设计文档 4.34 FileStorageClient 类

当前为本地文件系统实现，Phase 5 可切换为 OSS/S3 等云存储。
"""
import os
import uuid
from datetime import datetime


UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")


class FileStorageClient:
    """封装与文件存储服务的交互"""

    def __init__(self, base_path: str = "", bucket_name: str = "", timeout: int = 30):
        self._basePath = base_path or UPLOAD_DIR
        self._bucketName = bucket_name
        self._timeout = timeout
        os.makedirs(self._basePath, exist_ok=True)

    def uploadFile(self, file_data: bytes, file_name: str) -> dict:
        """上传文件"""
        ext = os.path.splitext(file_name)[1] or ".bin"
        stored_name = f"{uuid.uuid4().hex}{ext}"
        file_path = os.path.join(self._basePath, stored_name)

        with open(file_path, "wb") as f:
            f.write(file_data)

        return {
            "fileId": stored_name,
            "fileName": file_name,
            "filePath": file_path,
            "fileSize": len(file_data),
            "uploadTime": datetime.now().isoformat(),
        }

    def downloadFile(self, file_path: str) -> bytes | None:
        """读取文件"""
        full_path = os.path.join(self._basePath, file_path) if not os.path.isabs(file_path) else file_path
        if not os.path.exists(full_path):
            return None
        with open(full_path, "rb") as f:
            return f.read()

    def deleteFile(self, file_path: str) -> bool:
        """删除文件"""
        full_path = os.path.join(self._basePath, file_path) if not os.path.isabs(file_path) else file_path
        if os.path.exists(full_path):
            os.remove(full_path)
            return True
        return False

    def getFileUrl(self, file_path: str) -> str:
        """获取文件访问地址"""
        return f"/api/v1/files/{file_path}"

    def checkStorageHealth(self) -> dict:
        """检测文件存储服务是否可用"""
        writable = os.access(self._basePath, os.W_OK)
        return {"status": "available" if writable else "unavailable", "basePath": self._basePath}
