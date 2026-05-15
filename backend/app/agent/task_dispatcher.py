"""
任务分发器 — 对应设计文档 4.7 TaskDispatcher 类

根据意图类型将请求路由到对应的业务服务。
"""
from qdrant_client.models import Filter, FieldCondition, MatchValue


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
        self._datasheetQdrant = None
        self._modelClient = None

    def _getDatasheetQdrant(self):
        if self._datasheetQdrant is None:
            from app.external.model_client import ModelClient
            from app.external.vector_store_client import get_qdrant_client
            self._datasheetQdrant = get_qdrant_client()
            self._modelClient = ModelClient()
        return self._datasheetQdrant, self._modelClient

    def dispatch(self, intentType: str, inputData: dict) -> dict:
        """根据意图分发任务 — 对应 TaskDispatcher.dispatch"""
        service = self._routeToService(intentType)
        if service is None:
            return self._handleUnknownIntent(inputData)

        text = (inputData.get("text") or "").strip()

        if intentType == "参数查询":
            result = self._queryService.searchByKeyword(text)
            records = result.get("records", [])
            if records:
                ds_context = self._searchDatasheet(text, records)
                generated_answer = self._generateComponentAnswer(text, records, ds_context)
                if generated_answer:
                    result["answer"] = generated_answer
                    result["datasheetSnippets"] = ds_context
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

    def _searchDatasheet(self, query: str, records: list) -> str:
        """在 datasheet Qdrant 中搜索与问题相关的文本片段"""
        try:
            qdrant, model_client = self._getDatasheetQdrant()
            if not qdrant.collection_exists("component_datasheets"):
                return ""
            if not records:
                return ""

            embeddings = model_client.embedTexts([query])
            if not embeddings:
                return ""

            component_id = records[0].get("componentId", "")
            search_model = records[0].get("model", "")
            points = []
            if component_id:
                # 先按 component_id 精确搜索
                filtered = qdrant.query_points(
                    collection_name="component_datasheets",
                    query=embeddings[0],
                    query_filter=Filter(
                        must=[FieldCondition(key="component_id", match=MatchValue(value=component_id))]
                    ),
                    limit=3,
                ).points
                if filtered and filtered[0].score >= 0.35:
                    points = filtered

                # 精确匹配无结果时，全库搜索但校验结果型号与搜索型号是否同系列
                if not points:
                    fallback = qdrant.query_points(
                        collection_name="component_datasheets",
                        query=embeddings[0],
                        limit=5,
                    ).points
                    # 取搜索型号的前 4 个字符作为系列前缀
                    prefix = search_model[:4].lower() if len(search_model) >= 4 else ""
                    for fp in fallback:
                        fm = (fp.payload.get("model", "") if fp.payload else "").lower()
                        if fp.score >= 0.4 and prefix and (prefix in fm or fm.startswith(prefix)):
                            points.append(fp)
                    if points:
                        points = points[:3]

            if not points or points[0].score < 0.35:
                return ""

            snippets = []
            for r in points[:3]:
                p = r.payload or {}
                text = p.get("text", "")[:500]
                if text:
                    snippets.append(text)
            if snippets:
                return "相关 datasheet 内容:\n" + "\n...\n".join(snippets)
        except Exception:
            import traceback
            traceback.print_exc()
            pass
        return ""

    def _generateComponentAnswer(self, query: str, records: list, ds_context: str) -> str:
        """用 LLM 根据元件信息（及可选的 datasheet）生成自然语言答案"""
        try:
            _, model_client = self._getDatasheetQdrant()

            comp_lines = []
            for rec in records[:3]:
                comp_lines.append(
                    f"- 型号：{rec.get('model', '')} | 类型：{rec.get('type', '')} | "
                    f"厂商：{rec.get('manufacturer', '')} | 封装：{rec.get('packageType', '')}"
                )
            comp_info = "\n".join(comp_lines)

            system_prompt = (
                "你是电子元器件应用工程师，用自然流畅的中文回答用户问题。"
                "规则：1) 开篇一句话概括：型号的具体功能（不要照抄数据库分类路径，根据 datasheet 判断实际功能）、"
                "由谁生产、封装形式；"
                "2) 数据库类型字段是分类路径（如「运放/比较器/仪表放大器」），仅供参考，"
                "实际功能以 datasheet 为准。如果 datasheet 说明是差分放大器，就写差分放大器，不要从分类里硬选；"
                "3) 只列出 3-5 个最关键的参数，不要堆砌所有信息；"
                "4) 有具体数值直接引用，不确定的不要写；"
                "5) 如无 datasheet，末尾说明知识库暂无详细资料。"
                "6) 整体回答控制在 200 字以内。"
            )
            if ds_context:
                prompt = (
                    f"用户问题：{query}\n\n"
                    f"元器件基本信息：\n{comp_info}\n\n"
                    f"datasheet 参考资料：\n{ds_context}\n\n"
                    f"回答："
                )
            else:
                prompt = (
                    f"用户问题：{query}\n\n"
                    f"元器件基本信息：\n{comp_info}\n\n"
                    f"（知识库暂无该型号的 datasheet，仅根据数据库基本资料回答。"
                    f"参照以下风格：「知识库暂无该型号的详细数据手册，但通过数据库查询到："
                    f"CDBHM160L-HF 是一款二极管，由 Comchip Technology 生产，"
                    f"采用 Tape & Reel 封装。如需更详细的参数，建议查阅官方数据手册。」）\n\n"
                    f"回答："
                )

            answer = model_client.predictText(prompt, system_prompt)
            if answer:
                return answer
        except Exception:
            import traceback
            traceback.print_exc()
            pass
        return ""

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
