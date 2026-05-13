"""
拍照识件接口 — 对应设计文档 4.2 RecognitionController 类
"""
import uuid

from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.db.mysql import get_db
from app.core.security import get_current_user
from app.repositories.component_repository import ComponentRepository
from app.repositories.history_repository import HistoryRepository
from app.services.recognition_service import RecognitionService
from app.services.history_service import HistoryService
from app.schemas.qa_schema import FeedbackForm, RecognitionResult, FeedbackResult
from app.entities.chat import ChatSession, ChatMessage
from app.entities.operation_log import OperationLog
from app.core.response import success, error

router = APIRouter(prefix="/api/v1/recognize", tags=["智能问答"])

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp", "image/bmp"}
MAX_FILE_SIZE = 10 * 1024 * 1024


def _validateImage(content_type: str | None, file_size: int) -> str | None:
    """校验图片格式和大小 — 对应 RecognitionController._validateImage"""
    if not content_type or content_type not in ALLOWED_CONTENT_TYPES:
        return f"不支持的图片格式，允许: {', '.join(ALLOWED_CONTENT_TYPES)}"
    if file_size > MAX_FILE_SIZE:
        return f"图片大小不能超过 {MAX_FILE_SIZE // 1024 // 1024}MB"
    return None


def _buildRecognitionResponse(result: dict, session_id: str) -> dict:
    """封装识别响应 — 对应 RecognitionController._buildRecognitionResponse"""
    return RecognitionResult(
        sessionId=session_id,
        componentId=result.get("componentId"),
        model=result.get("model", ""),
        type=result.get("type", ""),
        packageType=result.get("packageType", ""),
        manufacturer=result.get("manufacturer", ""),
        confidence=result.get("confidence", 0.0),
        ocrText=result.get("ocrText", ""),
    ).model_dump()


@router.post("")
async def recognizeComponent(
    imageFile: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """上传图片识别元器件 — 对应 RecognitionController.recognizeComponent"""
    if not imageFile.filename:
        return error(400, "文件名不能为空")

    image_data = await imageFile.read()

    err_msg = _validateImage(imageFile.content_type, len(image_data))
    if err_msg:
        return error(400, err_msg)

    component_repo = ComponentRepository(db)
    recognition_service = RecognitionService(component_repo)

    try:
        result = recognition_service.recognize(image_data)
    except Exception as e:
        return error(500, f"识别失败: {str(e)}")

    # 保存会话记录
    log_repo = HistoryRepository(db)
    history_service = HistoryService(log_repo)

    title = f"拍照识件 — {result.get('model', '未知')}"
    session = history_service.saveSession(current_user.user_id, title)

    history_service.saveMessage(
        session_id=session.session_id,
        sender_type="user",
        content="[上传图片]",
        image_url=f"/api/v1/files/{imageFile.filename}",
    )
    history_service.saveMessage(
        session_id=session.session_id,
        sender_type="bot",
        content=f"识别结果：{result.get('model', '')} "
                f"({result.get('type', '')}，置信度 {result.get('confidence', 0):.0%})",
        source_info=result.get("ocrText", ""),
    )

    log_repo.saveOperationLog(OperationLog(
        user_id=current_user.user_id,
        operation_type="拍照识件",
        operation_target=result.get("model", ""),
        operation_result="成功" if result.get("componentId") else "低置信度",
    ))

    return success(
        data=_buildRecognitionResponse(result, session.session_id),
        message="识别完成",
    )


@router.post("/feedback")
async def submitFeedback(
    body: FeedbackForm,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """提交识别反馈 — 对应 RecognitionController.submitFeedback"""
    log_repo = HistoryRepository(db)

    # 校验会话存在
    if not log_repo.existsById(body.sessionId):
        return error(404, "会话不存在")

    feedback_log = OperationLog(
        user_id=current_user.user_id,
        operation_type="识别反馈",
        operation_target=body.sessionId,
        operation_result="正确" if body.isCorrect else f"错误 — {body.correction or ''}",
    )
    log_repo.saveOperationLog(feedback_log)

    return success(
        data=FeedbackResult(
            feedbackId=feedback_log.log_id,
            status="recorded",
        ).model_dump(),
        message="反馈已提交",
    )
