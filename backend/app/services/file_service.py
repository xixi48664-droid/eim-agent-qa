from app.external.file_storage_client import FileStorageClient
from app.schemas.file_schema import FileUploadData


class FileService:
    """文件管理业务逻辑"""

    def __init__(self, storage_client: FileStorageClient | None = None):
        self._storageClient = storage_client or FileStorageClient()

    def upload(self, file_data: bytes, file_name: str) -> FileUploadData:
        result = self._storageClient.uploadFile(file_data, file_name)
        file_url = f"/api/v1/files/{result['fileId']}"
        return FileUploadData(
            fileId=result["fileId"],
            fileName=result["fileName"],
            fileSize=result["fileSize"],
            fileUrl=file_url,
            uploadTime=result.get("uploadTime"),
        )

    def download(self, file_id: str) -> bytes | None:
        return self._storageClient.downloadFile(file_id)

    def delete(self, file_id: str) -> bool:
        return self._storageClient.deleteFile(file_id)
