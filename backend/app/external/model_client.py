"""
外部多模态模型服务适配器 — 对应设计文档 4.31 ModelClient 类

基于阿里云 DashScope (通义千问 qwen-vl) 实现。
"""
import base64
import json
import httpx
from app.core.config import settings


class ModelClient:
    """封装与 DashScope 多模态模型服务的调用"""

    def __init__(self):
        self._baseUrl = settings.DASHSCOPE_BASE_URL
        self._apiKey = settings.DASHSCOPE_API_KEY
        self._modelVL = settings.DASHSCOPE_MODEL_VL

    def predictImage(self, image_data: bytes) -> dict:
        """向模型服务发送图片识别请求，识别元器件信息"""
        image_b64 = base64.b64encode(image_data).decode("utf-8")

        body = {
            "model": self._modelVL,
            "input": {
                "messages": [{
                    "role": "user",
                    "content": [
                        {"image": f"data:image/jpeg;base64,{image_b64}"},
                        {"text": (
                            "请识别图片中的电子元器件，提取以下信息并以JSON格式返回："
                            "model（型号）、type（类型，如MCU/电阻/电容等）、"
                            "package（封装形式）、manufacturer（生产厂商）。"
                            "只返回JSON，不要其他内容。"
                            '格式：{"model":"...","type":"...","package":"...","manufacturer":"..."}'
                        )},
                    ],
                }]
            },
        }
        return self._callApi(body)

    def predictMultimodal(self, image_data: bytes, text: str) -> dict:
        """发送图文联合推理请求"""
        image_b64 = base64.b64encode(image_data).decode("utf-8")

        body = {
            "model": self._modelVL,
            "input": {
                "messages": [{
                    "role": "user",
                    "content": [
                        {"image": f"data:image/jpeg;base64,{image_b64}"},
                        {"text": text},
                    ],
                }]
            },
        }
        return self._callApi(body)

    def predictText(self, prompt: str, system_prompt: str = "") -> str:
        """纯文本推理，用于规范问答等场景"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        body = {
            "model": settings.DASHSCOPE_MODEL_TEXT,
            "input": {"messages": messages},
        }
        return self._callTextApi(body)

    def embedTexts(self, texts: list[str]) -> list[list[float]]:
        """文本向量化，用于语义检索"""
        body = {
            "model": settings.DASHSCOPE_MODEL_EMBEDDING,
            "input": {"texts": texts},
            "parameters": {"dimensions": 1024, "text_type": "document"},
        }
        url = f"{self._baseUrl}/services/embeddings/text-embedding/text-embedding"
        headers = {
            "Authorization": f"Bearer {self._apiKey}",
            "Content-Type": "application/json",
        }
        with httpx.Client(timeout=60) as client:
            response = client.post(url, json=body, headers=headers)
        if response.status_code != 200:
            raise RuntimeError(f"Embedding API error: {response.text}")
        embeddings = response.json()["output"]["embeddings"]
        embeddings.sort(key=lambda e: e["text_index"])
        return [e["embedding"] for e in embeddings]

    def checkServiceHealth(self) -> dict:
        """检测模型服务是否可用"""
        try:
            text_body = {
                "model": self._modelVL,
                "input": {
                    "messages": [{
                        "role": "user",
                        "content": [{"text": "hello"}],
                    }]
                },
            }
            result = self._callApi(text_body)
            return {"status": "available", "detail": result.get("model", "ok")}
        except Exception as e:
            return {"status": "unavailable", "detail": str(e)}

    def _callApi(self, body: dict) -> dict:
        """统一调用 DashScope API"""
        url = f"{self._baseUrl}/services/aigc/multimodal-generation/generation"
        headers = {
            "Authorization": f"Bearer {self._apiKey}",
            "Content-Type": "application/json",
        }

        with httpx.Client(timeout=60) as client:
            response = client.post(url, json=body, headers=headers)

        if response.status_code != 200:
            return {"error": response.text, "model": "", "rawText": ""}

        return self._parseResponse(response.json())

    def _callTextApi(self, body: dict) -> str:
        """调用 DashScope 文本生成 API"""
        url = f"{self._baseUrl}/services/aigc/text-generation/generation"
        headers = {
            "Authorization": f"Bearer {self._apiKey}",
            "Content-Type": "application/json",
        }

        with httpx.Client(timeout=60) as client:
            response = client.post(url, json=body, headers=headers)

        if response.status_code != 200:
            return ""

        try:
            data = response.json()
            return data.get("output", {}).get("text", "")
        except Exception:
            return ""

    def _parseResponse(self, response_data: dict) -> dict:
        """解析 DashScope 返回的多模态结果"""
        try:
            output = response_data.get("output", {})
            choices = output.get("choices", [])
            if not choices:
                return {"model": "", "type": "", "package": "", "rawText": ""}

            content_list = choices[0].get("message", {}).get("content", [])
            text = ""
            for item in content_list:
                if isinstance(item, dict) and "text" in item:
                    text += item["text"]

            if not text:
                return {"model": "", "type": "", "package": "", "rawText": ""}

            # 尝试解析 JSON 格式的识别结果
            text = text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[-1]
                if text.endswith("```"):
                    text = text[:-3]

            try:
                parsed = json.loads(text)
                return {
                    "model": parsed.get("model", ""),
                    "type": parsed.get("type", ""),
                    "package": parsed.get("package", ""),
                    "manufacturer": parsed.get("manufacturer", ""),
                    "confidence": 0.9,
                    "rawText": json.dumps(parsed, ensure_ascii=False),
                }
            except json.JSONDecodeError:
                return {
                    "model": text[:100],
                    "type": "",
                    "package": "",
                    "manufacturer": "",
                    "confidence": 0.85,
                    "rawText": text,
                }
        except Exception:
            return {"model": "", "type": "", "package": "", "rawText": ""}
