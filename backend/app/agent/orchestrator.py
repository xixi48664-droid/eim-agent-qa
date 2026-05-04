"""
智能体调度器 — 对应设计文档 4.5 AgentOrchestrator 类

统一入口：输入归一化 → 意图分类 → 任务分发。
"""
from app.agent.intent_classifier import IntentClassifier
from app.agent.task_dispatcher import TaskDispatcher


class AgentOrchestrator:
    """识别用户任务类型，分发给对应业务服务模块"""

    def __init__(
        self,
        intent_classifier: IntentClassifier,
        task_dispatcher: TaskDispatcher,
    ):
        self._intentClassifier = intent_classifier
        self._taskDispatcher = task_dispatcher

    def dispatchRequest(self, inputData: dict) -> dict:
        """统一分发请求 — 对应 AgentOrchestrator.dispatchRequest

        输入: {"text": "...", "imageUrl": "..."}
        输出: {"result": ..., "intentType": "...", "intent": {...}, "inputType": "..."}
        """
        normalized = self._normalizeInput(inputData)
        input_type = self._parseInputType(normalized)

        if input_type == "image":
            return self.handleImageQuery(normalized)

        intent_result = self._intentClassifier.classify(normalized)
        dispatch_result = self._taskDispatcher.dispatch(
            intent_result["intent"], normalized
        )

        return {
            **dispatch_result,
            "intent": intent_result,
            "inputType": input_type,
        }

    def handleImageQuery(self, inputData: dict) -> dict:
        """处理纯图片输入 — 对应 AgentOrchestrator.handleImageQuery"""
        return {
            "result": {"answer": "请使用拍照识件功能上传图片进行元器件识别"},
            "intentType": "拍照识件",
            "intent": {"intent": "拍照识件", "confidence": 1.0},
            "inputType": "image",
        }

    def handleTextQuery(self, inputData: dict) -> dict:
        """处理纯文本输入 — 对应 AgentOrchestrator.handleTextQuery"""
        intent_result = self._intentClassifier.classify(inputData)
        return self._taskDispatcher.dispatch(intent_result["intent"], inputData)

    def _parseInputType(self, inputData: dict) -> str:
        """判断输入类型 — 对应 AgentOrchestrator._parseInputType"""
        has_text = bool((inputData.get("text") or "").strip())
        has_image = bool(inputData.get("imageUrl"))

        if has_text and has_image:
            return "multimodal"
        if has_image:
            return "image"
        return "text"

    def _normalizeInput(self, inputData: dict) -> dict:
        """归一化输入 — 对应 AgentOrchestrator._normalizeInput"""
        return {
            "text": (inputData.get("text") or "").strip(),
            "imageUrl": inputData.get("imageUrl") or "",
        }
