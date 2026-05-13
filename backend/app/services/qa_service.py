"""
规范问答服务 — 对应设计文档 4.11 QaService 类

通过向量检索 + 规范数据库查询实现知识检索，使用千问模型生成自然语言答案。
"""
from app.repositories.standard_repository import StandardRepository
from app.external.vector_store_client import VectorStoreClient
from app.external.model_client import ModelClient
from app.schemas.qa_schema import StandardDetailResponse


class QaService:
    """处理工艺规范问答，检索知识库并生成答案和来源依据"""

    def __init__(self, standard_repo: StandardRepository):
        self._standardRepository = standard_repo
        self._vectorClient = VectorStoreClient()
        self._modelClient = ModelClient()

    def answerQuestion(self, question: str) -> dict:
        """回答工艺规范问题 — 对应 QaService.answerQuestion"""
        if not question or not question.strip():
            raise ValueError("问题不能为空")

        knowledge_list = self._retrieveKnowledge(question.strip())
        answer = self._composeAnswer(question, knowledge_list)
        recommended = self.recommendQuestions(question)

        sources = []
        for k in knowledge_list:
            sources.append({
                "sourceType": "standard",
                "sourceId": k.get("id", ""),
                "sourceTitle": k.get("metadata", {}).get("standardCode", ""),
                "contentSnippet": k.get("content", ""),
            })

        return {
            "answer": answer,
            "sources": sources,
            "recommendedQuestions": recommended,
        }

    def recommendQuestions(self, question: str) -> list[str]:
        """生成相关问题推荐 — 对应 QaService.recommendQuestions"""
        keywords = self._extractKeywords(question)
        if not keywords:
            return [
                "电子组件的可接受性标准是什么？",
                "SMT贴片工艺有哪些规范要求？",
                "焊接质量的验收标准有哪些？",
            ]

        standards = self._standardRepository.searchByTags(keywords[:3])
        if not standards:
            return [
                f"关于{keywords[0]}的工艺规范有哪些？",
                f"{keywords[0]}的操作标准是什么？",
                "常见的焊接缺陷有哪些？",
            ]

        return [f"{s.standard_name}的具体要求是什么？" for s in standards[:3]]

    def _retrieveKnowledge(self, question: str) -> list:
        """向量检索 + 数据库查询知识库 — 对应 QaService._retrieveKnowledge"""
        result = self._vectorClient.search(question, top_k=5)

        keywords = self._extractKeywords(question)
        if keywords:
            db_standards = self._standardRepository.searchByTags(keywords[:2])
            if db_standards:
                for s in db_standards:
                    result.append({
                        "id": s.standard_id,
                        "score": 0.85,
                        "metadata": {
                            "standardCode": s.standard_code or "",
                        },
                        "content": s.summary or f"{s.standard_name} — {s.section or ''}",
                    })
        return result

    def _composeAnswer(self, question: str, knowledge_list: list) -> str:
        """使用千问模型根据知识片段生成自然语言答案"""
        if not knowledge_list:
            return "抱歉，未找到与您问题相关的工艺规范知识。请尝试使用更具体的工艺术语提问。"

        # 构建知识上下文
        knowledge_text_parts = []
        for i, k in enumerate(knowledge_list, 1):
            meta = k.get("metadata", {})
            code = meta.get("standardCode", "")
            content = k.get("content", "")
            knowledge_text_parts.append(f"[参考{i}] {code}: {content}")

        knowledge_context = "\n".join(knowledge_text_parts)

        system_prompt = (
            "你是电子制造业工艺专家。请根据提供的参考知识回答用户问题。"
            "回答要专业、准确、简洁。如果参考知识不足以回答，请诚实说明。"
        )
        prompt = f"参考知识：\n{knowledge_context}\n\n用户问题：{question}\n\n请回答："

        try:
            answer = self._modelClient.predictText(prompt, system_prompt)
            return answer if answer else "\n\n".join(knowledge_text_parts)
        except Exception:
            return "\n\n".join(knowledge_text_parts)

    def getStandardById(self, standard_id: str) -> dict:
        """根据规范编号获取规范文档详情 — 对应 QaService.getStandardById"""
        standard = self._standardRepository.findById(standard_id)
        if not standard:
            raise ValueError("规范文档不存在")
        return StandardDetailResponse(
            standardId=standard.standard_id,
            standardCode=standard.standard_code or "",
            standardName=standard.standard_name,
            section=standard.section or "",
            summary=standard.summary or "",
            tags=standard.tags or "",
            relatedProcess=standard.related_process or "",
        ).model_dump()

    def _extractKeywords(self, text: str) -> list[str]:
        """从问题中提取关键工艺术语"""
        TECHNICAL_TERMS = [
            "焊接", "贴片", "SMT", "PCB", "回流焊", "波峰焊", "检测",
            "IPC", "验收", "质量", "封装", "清洁", "装配", "QFN", "BGA",
            "工艺", "标准", "规范", "操作", "流程",
        ]
        return [t for t in TECHNICAL_TERMS if t.lower() in text.lower()]
