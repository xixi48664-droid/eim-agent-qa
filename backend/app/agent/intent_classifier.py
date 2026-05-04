"""
意图分类器 — 对应设计文档 4.6 IntentClassifier 类

混合策略：关键词命中率高时直接返回（零延迟/零成本），
低置信度时使用 LLM 进行语义分类（更准确）。
"""
import json


class IntentClassifier:
    """识别用户意图：拍照识件 | 参数查询 | 规范问答 | 流程指导"""

    INTENT_KEYWORDS = {
        "拍照识件": [
            "拍照", "识别", "图片", "这个元器件", "这是什么", "照片", "图像",
            "拍一下", "拍个", "上传图片", "看图",
        ],
        "参数查询": [
            "参数", "型号", "规格", "datasheet", "技术参数", "查询", "搜索",
            "电压", "电流", "频率", "封装", "引脚", "flash", "ram", "多少",
            "多大", "什么型号", "哪个",
        ],
        "规范问答": [
            "规范", "标准", "ipc", "要求", "规定", "验收", "工艺规范",
            "操作规范", "焊接", "贴片", "检测", "质量", "合格", "标准是什么",
            "应该", "必须", "允许", "不允许",
        ],
        "流程指导": [
            "流程", "步骤", "教程", "怎么做", "如何", "指导", "过程",
            "工序", "smt", "pcb", "装配", "操作步骤", "方法", "指南",
            "教程", "怎么操作", "怎样",
        ],
    }

    INTENT_DESCRIPTIONS = {
        "拍照识件": "用户希望通过上传图片或拍照来识别电子元器件的型号和参数",
        "参数查询": "用户想查询某个电子元器件的技术参数、规格、datasheet等信息",
        "规范问答": "用户询问电子制造工艺规范、IPC标准、验收要求、焊接/贴片质量标准等",
        "流程指导": "用户想了解某个工序的操作流程、步骤教程、SMT/PCB装配指导等",
    }

    LLM_CLASSIFY_PROMPT = """你是一个电子制造领域的意图分类器。请分析用户输入，判断其意图属于以下四类之一：

1. 参数查询 — 用户想查询电子元器件的技术参数、型号规格、datasheet等
2. 规范问答 — 用户询问工艺规范、IPC标准、质量验收要求等
3. 流程指导 — 用户想了解操作流程、工序步骤、教程指导等
4. 拍照识件 — 用户希望通过图片识别元器件（输入中包含图片相关描述）

请只返回JSON，不要其他内容：
{"intent": "<意图名称>", "confidence": <0.0-1.0之间的置信度>}"""

    def __init__(self, threshold: float = 0.5, model_client=None):
        self._intentRules = self.INTENT_KEYWORDS
        self._threshold = threshold
        self._modelClient = model_client

    def classify(self, inputData: dict) -> dict:
        """识别用户意图 — 混合策略。

        输入: {"text": "...", "imageUrl": "..."}
        输出: {"intent": "规范问答", "confidence": 0.85, "scores": {...}}
        """
        text = (inputData.get("text") or "").strip().lower()
        has_image = bool(inputData.get("imageUrl"))

        if not text and has_image:
            return {"intent": "拍照识件", "confidence": 1.0, "scores": {"拍照识件": 1.0}}

        if not text:
            return {"intent": "参数查询", "confidence": 0.1, "scores": {}}

        # 第一层：关键词快速匹配
        keywords = self._extractKeywords(text)
        scores = self._scoreIntent(keywords)

        if scores:
            best_intent = max(scores, key=scores.get)
            best_score = scores[best_intent]
            confidence = min(best_score / max(len(keywords), 1), 1.0)

            # 高置信度直接返回，避免不必要的 LLM 调用
            if confidence >= self._threshold:
                return {"intent": best_intent, "confidence": round(confidence, 2), "scores": scores}

        # 第二层：LLM 语义分类（低置信度或无命中时）
        if self._modelClient:
            llm_result = self._classifyByLLM(inputData.get("text", ""))
            if llm_result:
                return llm_result

        # 兜底
        if scores:
            best_intent = max(scores, key=scores.get)
            return {"intent": best_intent, "confidence": round(confidence, 2), "scores": scores}

        return {"intent": "参数查询", "confidence": 0.1, "scores": {}}

    def _classifyByLLM(self, text: str) -> dict | None:
        """使用 LLM 进行意图分类"""
        try:
            raw = self._modelClient.predictText(
                prompt=text,
                system_prompt=self.LLM_CLASSIFY_PROMPT,
            )
            if not raw:
                return None
            raw = raw.strip()
            if raw.startswith("```"):
                lines = raw.split("\n")
                raw = "\n".join(lines[1:])
                if raw.endswith("```"):
                    raw = raw[:-3]
            parsed = json.loads(raw)
            intent = parsed.get("intent", "")
            confidence = float(parsed.get("confidence", 0.5))
            if intent in self.INTENT_DESCRIPTIONS:
                return {"intent": intent, "confidence": round(confidence, 2), "scores": {}}
        except Exception:
            pass
        return None

    def _extractKeywords(self, text: str) -> list[str]:
        """从文本中提取匹配到的关键词"""
        found = []
        for intent, words in self._intentRules.items():
            for w in words:
                if w in text:
                    found.append(w)
        return found

    def _scoreIntent(self, keywords: list[str]) -> dict:
        """根据关键词命中数计算各意图得分"""
        scores = {}
        for intent, words in self._intentRules.items():
            hits = sum(1 for w in words if w in keywords)
            if hits > 0:
                scores[intent] = hits
        return scores
