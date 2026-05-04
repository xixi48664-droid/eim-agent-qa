"""
AI 功能请求/响应 DTO — 对应设计文档 4.2/4.3/4.5 相关类
"""
from typing import Optional
from pydantic import BaseModel, Field


class InputForm(BaseModel):
    """综合问答输入 — 对应 QaController.askQuestion / continueConversation"""
    text: Optional[str] = None
    imageUrl: Optional[str] = None


class FeedbackForm(BaseModel):
    """识别反馈表单 — 对应 RecognitionController.submitFeedback"""
    sessionId: str
    isCorrect: bool
    correction: Optional[str] = None


class SourceInfo(BaseModel):
    """答案来源依据"""
    sourceType: str = ""
    sourceId: str = ""
    sourceTitle: str = ""
    contentSnippet: str = ""


class QaResponse(BaseModel):
    """综合问答结果 — 对应 QaController.askQuestion 输出"""
    sessionId: str
    answer: str
    intent: str = ""
    confidence: float = 0.0
    sources: list[SourceInfo] = []
    recommendedQuestions: list[str] = []


class RecognitionResult(BaseModel):
    """元器件识别结果 — 对应 RecognitionController.recognizeComponent 输出"""
    sessionId: str
    componentId: Optional[str] = None
    model: str = ""
    type: str = ""
    packageType: str = ""
    manufacturer: str = ""
    confidence: float = 0.0
    ocrText: str = ""


class FeedbackResult(BaseModel):
    """反馈提交结果 — 对应 RecognitionController.submitFeedback 输出"""
    feedbackId: str
    status: str


class TutorialGuideResponse(BaseModel):
    """用户端教程指导响应"""
    tutorialId: str
    processName: str
    totalSteps: int
    estimatedTime: Optional[str] = None
    steps: list[dict] = []


class StandardDetailResponse(BaseModel):
    """用户端规范文档详情响应"""
    standardId: str
    standardCode: str = ""
    standardName: str
    section: str = ""
    summary: str = ""
    tags: str = ""
    relatedProcess: str = ""


class ChatFeedbackRequest(BaseModel):
    """答案反馈请求 — like/dislike"""
    messageId: str
    feedback: str = Field(..., pattern="^(like|dislike)$")


class ChatFeedbackData(BaseModel):
    """答案反馈响应"""
    messageId: str
    feedback: str
