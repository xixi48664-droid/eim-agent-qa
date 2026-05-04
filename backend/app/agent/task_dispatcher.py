"""
任务分发器 — 对应设计文档 4.7 TaskDispatcher 类

根据意图类型将请求路由到对应的业务服务。
"""


class TaskDispatcher:
    """根据已识别的意图将请求路由至具体业务服务"""

    def __init__(
        self,
        recognition_service,
        query_service,
        qa_service,
        tutorial_service,
        history_service,
    ):
        self._recognitionService = recognition_service
        self._queryService = query_service
        self._qaService = qa_service
        self._tutorialService = tutorial_service
        self._historyService = history_service

    def dispatch(self, intentType: str, inputData: dict) -> dict:
        """根据意图分发任务 — 对应 TaskDispatcher.dispatch"""
        service = self._routeToService(intentType)
        if service is None:
            return self._handleUnknownIntent(inputData)

        text = (inputData.get("text") or "").strip()

        if intentType == "参数查询":
            result = self._queryService.searchByKeyword(text)
            return {"result": result, "intentType": intentType}

        elif intentType == "规范问答":
            result = self._qaService.answerQuestion(text)
            return {"result": result, "intentType": intentType}

        elif intentType == "流程指导":
            try:
                result = self._tutorialService.getTutorial(text)
            except ValueError:
                result = {
                    "tutorialId": "",
                    "processName": text,
                    "totalSteps": 0,
                    "estimatedTime": "",
                    "steps": [],
                    "hint": f"未找到工序「{text}」的教程，请尝试输入准确的工序名称",
                }
            return {"result": result, "intentType": intentType}

        elif intentType == "拍照识件":
            return {
                "result": {"answer": "请通过拍照识件功能上传图片进行元器件识别"},
                "intentType": intentType,
            }

        return {"result": {}, "intentType": intentType}

    def _routeToService(self, intentType: str):
        """返回对应的业务服务对象 — 对应 TaskDispatcher._routeToService"""
        mapping = {
            "参数查询": self._queryService,
            "规范问答": self._qaService,
            "流程指导": self._tutorialService,
            "拍照识件": self._recognitionService,
        }
        return mapping.get(intentType)

    def _handleUnknownIntent(self, inputData: dict) -> dict:
        """处理未知意图 — 对应 TaskDispatcher._handleUnknownIntent"""
        return {
            "result": {
                "answer": "抱歉，我没有理解您的问题。您可以尝试：\n"
                          "1. 输入元器件型号查询参数（如「STM32F103C8T6」）\n"
                          "2. 提问工艺规范问题（如「焊接验收标准是什么」）\n"
                          "3. 查询操作流程（如「SMT贴片怎么做」）\n"
                          "4. 上传元器件图片进行拍照识件",
            },
            "intentType": "unknown",
        }
