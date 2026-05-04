"""
文件上传接口
"""
from fastapi import APIRouter, Depends, UploadFile, File
from fastapi.responses import Response
from app.core.security import get_current_user
from app.services.file_service import FileService
from app.core.response import success, error

router = APIRouter(prefix="/api/v1/files", tags=["文件管理"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".pdf"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


@router.post("/upload")
async def uploadFile(
    file: UploadFile = File(...),
    current_user=Depends(get_current_user),
):
    """上传文件"""
    if not file.filename:
        return error(400, "文件名不能为空")

    ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        return error(400, f"不支持的文件类型: {ext}，允许: {', '.join(ALLOWED_EXTENSIONS)}")

    file_data = await file.read()
    if len(file_data) > MAX_FILE_SIZE:
        return error(400, f"文件大小不能超过 {MAX_FILE_SIZE // 1024 // 1024}MB")

    file_service = FileService()
    result = file_service.upload(file_data, file.filename)
    return success(data=result.model_dump(), message="上传成功")


@router.get("/{fileId}")
async def downloadFile(
    fileId: str,
    current_user=Depends(get_current_user),
):
    """下载/查看文件"""
    file_service = FileService()
    file_data = file_service.download(fileId)

    if file_data is None:
        return error(404, "文件不存在")

    ext = fileId.rsplit(".", 1)[-1].lower() if "." in fileId else "bin"
    media_types = {
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "gif": "image/gif",
        "webp": "image/webp",
        "bmp": "image/bmp",
        "pdf": "application/pdf",
    }
    return Response(
        content=file_data,
        media_type=media_types.get(ext, "application/octet-stream"),
    )


@router.delete("/{fileId}")
async def deleteFile(
    fileId: str,
    current_user=Depends(get_current_user),
):
    """删除文件"""
    file_service = FileService()
    ok = file_service.delete(fileId)

    if not ok:
        return error(404, "文件不存在")
    return success(message="删除成功")
