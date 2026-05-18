"""
参数查询与问答接口 — 对应设计文档 4.3 QaController 类
"""
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session
from app.db.mysql import get_db
from app.core.security import get_current_user
from app.repositories.component_repository import ComponentRepository
from app.repositories.history_repository import HistoryRepository
from app.repositories.standard_repository import StandardRepository
from app.repositories.tutorial_repository import TutorialRepository
from app.entities.operation_log import OperationLog
from app.services.query_service import QueryService
from app.services.history_service import HistoryService
from app.services.recognition_service import RecognitionService
from app.services.qa_service import QaService
from app.services.tutorial_service import TutorialService
from app.agent.intent_classifier import IntentClassifier
from app.agent.task_dispatcher import TaskDispatcher
from app.agent.orchestrator import AgentOrchestrator
from app.external.model_client import ModelClient
from app.schemas.qa_schema import InputForm, QaResponse, SourceInfo, ChatFeedbackRequest, ChatFeedbackData
from app.core.response import success, error

router = APIRouter(prefix="/api/v1/components", tags=["智能问答"])
chat_router = APIRouter(prefix="/api/v1/chat", tags=["智能问答"])
tutorial_guide_router = APIRouter(prefix="/api/v1/tutorials", tags=["智能问答"])
standards_router = APIRouter(prefix="/api/v1/standards", tags=["智能问答"])


@router.get("/search")
def searchByKeyword(
    keyword: str = Query(..., description="元器件型号或关键词"),
    type: Optional[str] = Query(None, description="元器件类型筛选"),
    pageNum: int = Query(1, ge=1, description="页码"),
    pageSize: int = Query(10, ge=1, le=100, description="每页条数"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    元器件搜索 — 对应接口文档 5.1 节
    """
    component_repo = ComponentRepository(db)
    query_service = QueryService(component_repo)

    try:
        result = query_service.searchByKeyword(keyword, pageNum, pageSize, type)

        log_repo = HistoryRepository(db)
        log_repo.saveOperationLog(OperationLog(
            user_id=current_user.user_id,
            operation_type="参数查询",
            operation_target=keyword,
            operation_result="成功" if result["total"] > 0 else "无结果",
        ))
        if result["total"] == 0:
            return error(404, "未查询到匹配的元器件")
        return success(data=result, message="查询成功")
    except ValueError as e:
        return error(400, str(e))


@router.get("/{componentId}")
def getComponentDetail(
    componentId: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    元器件参数详情 — 对应接口文档 5.2 节
    """
    component_repo = ComponentRepository(db)
    query_service = QueryService(component_repo)

    try:
        result = query_service.getComponentDetail(componentId)

        log_repo = HistoryRepository(db)
        log_repo.saveOperationLog(OperationLog(
            user_id=current_user.user_id,
            operation_type="查看详情",
            operation_target=result.model,
            operation_result="成功",
        ))

        return success(data=result.model_dump(), message="查询成功")
    except ValueError as e:
        return error(404, str(e))


# ── 问答历史接口（设计文档 QaController）─────────────────────────

@chat_router.get("/sessions")
def getChatSessions(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """查询当前用户的会话列表 — 对应设计文档 QaController.getHistory"""
    log_repo = HistoryRepository(db)
    history_service = HistoryService(log_repo)

    result = history_service.getHistoryByUser(current_user.user_id)
    return success(data=result, message="查询成功")


@chat_router.get("/sessions/{sessionId}")
def getHistory(
    sessionId: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """读取指定会话历史 — 对应设计文档 QaController.getHistory"""
    log_repo = HistoryRepository(db)
    history_service = HistoryService(log_repo)

    try:
        result = history_service.getSessionDetail(sessionId)
        return success(data=result.model_dump(), message="查询成功")
    except ValueError as e:
        return error(404, str(e))


@chat_router.delete("/sessions/{sessionId}")
def deleteHistory(
    sessionId: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """删除单条历史会话 — 对应设计文档 QaController.deleteHistory"""
    log_repo = HistoryRepository(db)
    history_service = HistoryService(log_repo)

    try:
        history_service.deleteSession(sessionId)
        return success(message="删除成功")
    except ValueError as e:
        return error(404, str(e))


@chat_router.post("/sessions/batch-delete")
def batchdeleteHistory(
    sessionIds: list[str] = Body(..., description="会话编号列表"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """批量删除历史会话 — 对应设计文档 QaController.batchdeleteHistory"""
    log_repo = HistoryRepository(db)
    history_service = HistoryService(log_repo)

    result = history_service.batchDeleteSessions(sessionIds)
    return success(data=result, message="批量删除完成")


# ── AI 问答接口（设计文档 QaController.askQuestion / continueConversation）──


def _buildOrchestrator(db: Session):
    """组装 orchestrator 管线：所有 repo / service / agent 对象"""
    comp_repo = ComponentRepository(db)
    standard_repo = StandardRepository(db)
    tutorial_repo = TutorialRepository(db)
    log_repo = HistoryRepository(db)

    recognition_service = RecognitionService(comp_repo)
    query_service = QueryService(comp_repo)
    qa_service = QaService(standard_repo)
    tutorial_service = TutorialService(tutorial_repo)
    history_service = HistoryService(log_repo)

    intent_classifier = IntentClassifier(threshold=0.5, model_client=ModelClient())
    task_dispatcher = TaskDispatcher(
        recognition_service, query_service, qa_service,
        tutorial_service, history_service,
    )
    return AgentOrchestrator(intent_classifier, task_dispatcher), history_service, log_repo


def _buildQaResponse(result: dict, session_id: str) -> dict:
    """统一封装问答响应 — 对应 QaController._buildQaResponse"""
    r = result.get("result", {})
    intent_info = result.get("intent", {})
    intent_type = result.get("intentType", "")

    # 根据意图类型格式化 answer 和 sources
    answer = r.get("answer", "")
    sources = []
    recommended = r.get("recommendedQuestions", [])

    if intent_type == "参数查询":
        total = r.get("total", 0)
        records = r.get("records", [])
        if records:
            generated = r.get("answer", "")
            if generated:
                answer = generated
            else:
                lines = [f"找到 {total} 个相关元器件："]
                for rec in records[:5]:
                    lines.append(
                        f"- {rec.get('model', '')} "
                        f"({rec.get('type', '')} | {rec.get('manufacturer', '')} "
                        f"| {rec.get('packageType', '')})"
                    )
                answer = "\n".join(lines)

            for rec in records[:3]:
                sources.append(SourceInfo(
                    sourceType="component",
                    sourceId=rec.get("componentId", ""),
                    sourceTitle=rec.get("model", ""),
                    contentSnippet=f"{rec.get('type', '')} {rec.get('manufacturer', '')}",
                ))
            ds_snippets = r.get("datasheetSnippets", "")
            if ds_snippets:
                sources.append(SourceInfo(
                    sourceType="datasheet",
                    sourceId=records[0].get("componentId", ""),
                    sourceTitle=f"{records[0].get('model', '')} datasheet",
                    contentSnippet=ds_snippets[:500],
                ))
            recommended = [f"{rec.get('model', '')}的详细参数？" for rec in records[:3]]
        else:
            answer = "未找到匹配的元器件，请尝试其他关键词。"
    elif intent_type == "流程指导":
        answer = f"工序「{r.get('processName', '')}」共 {r.get('totalSteps', 0)} 个步骤"
        if r.get("estimatedTime"):
            answer += f"，预计时长 {r.get('estimatedTime')}"
        steps = r.get("steps", [])
        for s in steps:
            answer += f"\n\n步骤{s.get('stepNo', '')}: {s.get('stepTitle', '')}\n{s.get('stepContent', '')}"
        if not steps and r.get("hint"):
            answer = r["hint"]
        for s in steps:
            sources.append(SourceInfo(
                sourceType="tutorial",
                sourceId=s.get("stepId", ""),
                sourceTitle=s.get("stepTitle", ""),
                contentSnippet=s.get("stepContent", ""),
            ))
        recommended = [f"{s.get('stepTitle', '')}的注意事项？" for s in steps[:3]]
    else:
        for s in r.get("sources", []):
            sources.append(SourceInfo(
                sourceType=s.get("sourceType", ""),
                sourceId=s.get("sourceId", ""),
                sourceTitle=s.get("sourceTitle", ""),
                contentSnippet=s.get("contentSnippet", ""),
            ))

    return QaResponse(
        sessionId=session_id,
        answer=answer,
        intent=intent_info.get("intent", ""),
        confidence=intent_info.get("confidence", 0.0),
        sources=sources,
        recommendedQuestions=recommended,
    ).model_dump()


@chat_router.post("/ask")
def askQuestion(
    body: InputForm,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """综合问答（文字/图文）— 对应设计文档 QaController.askQuestion"""
    if not body.text and not body.imageUrl:
        return error(400, "请输入问题文本或上传图片")

    orchestrator, history_service, log_repo = _buildOrchestrator(db)

    input_data = {"text": body.text, "imageUrl": body.imageUrl}
    result = orchestrator.dispatchRequest(input_data)

    title = (body.text or "")[:30] or "图片问答"
    session = history_service.saveSession(current_user.user_id, title)
    history_service.saveMessage(
        session_id=session.session_id,
        sender_type="user",
        content=body.text or "[图片]",
        image_url=body.imageUrl,
    )

    r = result.get("result", {})
    history_service.saveMessage(
        session_id=session.session_id,
        sender_type="bot",
        content=r.get("answer", ""),
        source_info=str(r.get("sources", [])),
    )

    log_repo.saveOperationLog(OperationLog(
        user_id=current_user.user_id,
        operation_type="AI 问答",
        operation_target=(body.text or "")[:50],
        operation_result=result.get("intentType", ""),
    ))

    return success(
        data=_buildQaResponse(result, session.session_id),
        message="问答完成",
    )


@chat_router.post("/sessions/{sessionId}/continue")
def continueConversation(
    sessionId: str,
    body: InputForm,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """基于历史上下文继续提问 — 对应设计文档 QaController.continueConversation"""
    if not body.text and not body.imageUrl:
        return error(400, "请输入问题文本或上传图片")

    log_repo = HistoryRepository(db)
    history_service = HistoryService(log_repo)

    owner_id = log_repo.findUserIdBySessionId(sessionId)
    if owner_id is None:
        return error(404, "会话不存在")
    if owner_id != current_user.user_id:
        return error(404, "会话不存在")

    # 拼接历史上下文
    history_lines = []
    detail = history_service.getSessionDetail(sessionId)
    for msg in detail.messages:
        role = "用户" if msg.senderType == "user" else "助手"
        history_lines.append(f"{role}: {msg.content}")

    context_text = "\n".join(history_lines[-6:])
    full_text = f"对话历史：\n{context_text}\n\n当前问题：{body.text}"

    orchestrator, _, _ = _buildOrchestrator(db)
    input_data = {"text": full_text, "imageUrl": body.imageUrl}
    result = orchestrator.dispatchRequest(input_data)

    history_service.saveMessage(
        session_id=sessionId,
        sender_type="user",
        content=body.text or "[图片]",
        image_url=body.imageUrl,
    )
    r = result.get("result", {})
    history_service.saveMessage(
        session_id=sessionId,
        sender_type="bot",
        content=r.get("answer", ""),
        source_info=str(r.get("sources", [])),
    )

    log_repo.saveOperationLog(OperationLog(
        user_id=current_user.user_id,
        operation_type="AI 追问",
        operation_target=(body.text or "")[:50],
        operation_result=result.get("intentType", ""),
    ))

    return success(
        data=_buildQaResponse(result, sessionId),
        message="问答完成",
    )


# ── 答案反馈接口 ────────────────────────────────────────────────

@chat_router.post("/feedback")
def submitChatFeedback(
    body: ChatFeedbackRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """提交答案反馈（like/dislike）"""
    log_repo = HistoryRepository(db)

    ok = log_repo.setMessageFeedback(body.messageId, body.feedback)
    if not ok:
        return error(404, "消息不存在或不可反馈")

    log_repo.saveOperationLog(OperationLog(
        user_id=current_user.user_id,
        operation_type="答案反馈",
        operation_target=body.messageId,
        operation_result=body.feedback,
    ))

    return success(
        data=ChatFeedbackData(messageId=body.messageId, feedback=body.feedback).model_dump(),
        message="反馈提交成功",
    )


# ── 用户端流程指导接口 ─────────────────────────────────────────


@tutorial_guide_router.get("/guide")
def getTutorialByProcess(
    processName: str = Query(..., description="工序名称"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """按工序名称查询教程 — 对应设计文档 TutorialService.getTutorial"""
    tutorial_repo = TutorialRepository(db)
    tutorial_service = TutorialService(tutorial_repo)

    try:
        result = tutorial_service.getTutorial(processName)
        return success(data=result, message="查询成功")
    except ValueError as e:
        return error(404, str(e))


@tutorial_guide_router.get("/guide/{tutorialId}")
def getTutorialDetail(
    tutorialId: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取教程详情含步骤列表 — 对应设计文档 TutorialService.getTutorialSteps"""
    tutorial_repo = TutorialRepository(db)
    tutorial_service = TutorialService(tutorial_repo)

    try:
        result = tutorial_service.getTutorialSteps(tutorialId)
        return success(data=result, message="查询成功")
    except ValueError as e:
        return error(404, str(e))


# ── 用户端规范文档接口 ─────────────────────────────────────────


@standards_router.get("/{standardId}")
def getStandardDetail(
    standardId: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """获取规范文档详情 — 对应设计文档 QaService.getStandardById"""
    standard_repo = StandardRepository(db)
    qa_service = QaService(standard_repo)

    try:
        result = qa_service.getStandardById(standardId)
        return success(data=result, message="查询成功")
    except ValueError as e:
        return error(404, str(e))
