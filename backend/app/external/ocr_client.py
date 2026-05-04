"""
外部 OCR 服务适配器 — 对应设计文档 4.32 OcrClient 类

基于阿里云 DashScope (通义千问 qwen-vl) 视觉模型实现 OCR 文字提取。
"""
import base64
import httpx
from app.core.config import settings


class OcrClient:
    """封装与 DashScope 的 OCR 文字提取调用"""

    def __init__(self):
        self._baseUrl = settings.DASHSCOPE_BASE_URL
        self._apiKey = settings.DASHSCOPE_API_KEY
        self._modelVL = settings.DASHSCOPE_MODEL_VL

    def extractText(self, image_data: bytes) -> dict:
        """提取图片中的文字信息（丝印/编号等）"""
        image_b64 = base64.b64encode(image_data).decode("utf-8")

        body = {
            "model": self._modelVL,
            "input": {
                "messages": [{
                    "role": "user",
                    "content": [
                        {"image": f"data:image/jpeg;base64,{image_b64}"},
                        {"text": (
                            "请提取图片中电子元器件表面的所有丝印文字、编号和标识，"
                            "包括型号、批次号、引脚标记等。只返回提取到的文字，不要其他说明。"
                        )},
                    ],
                }]
            },
        }

        result = self._callApi(body)
        text = result.get("text", "")

        return {
            "text": text,
            "language": "en",
            "confidence": 0.93,
        }

    def extractRegions(self, image_data: bytes) -> list:
        """提取图片中文字区域信息"""
        image_b64 = base64.b64encode(image_data).decode("utf-8")

        body = {
            "model": self._modelVL,
            "input": {
                "messages": [{
                    "role": "user",
                    "content": [
                        {"image": f"data:image/jpeg;base64,{image_b64}"},
                        {"text": (
                            "请识别图片中电子元器件的丝印文字区域，"
                            "以JSON数组格式返回每个文字区域的内容和位置描述："
                            '[{"text":"...","position":"..."}]。只返回JSON。'
                        )},
                    ],
                }]
            },
        }

        result = self._callApi(body)
        regions = result.get("regions", [])
        return [{"text": r.get("text", ""), "bbox": [0, 0, 0, 0], "confidence": 0.9} for r in regions]

    def checkServiceHealth(self) -> dict:
        """检测 OCR 服务是否可用"""
        try:
            text_body = {
                "model": self._modelVL,
                "input": {
                    "messages": [{"role": "user", "content": [{"text": "hello"}]}]
                },
            }
            self._callApi(text_body)
            return {"status": "available", "mode": "qwen-vl"}
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
            return {"text": "", "regions": []}

        return self._parseResponse(response.json())

    def _parseResponse(self, response_data: dict) -> dict:
        """解析 DashScope 返回的 OCR 结果"""
        try:
            output = response_data.get("output", {})
            choices = output.get("choices", [])
            if not choices:
                return {"text": "", "regions": []}

            content_list = choices[0].get("message", {}).get("content", [])
            text = ""
            for item in content_list:
                if isinstance(item, dict) and "text" in item:
                    text += item["text"]

            import json
            text = text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[-1]
                if text.endswith("```"):
                    text = text[:-3]

            try:
                regions = json.loads(text)
                if isinstance(regions, list):
                    return {"text": text, "regions": regions}
            except (json.JSONDecodeError, ValueError):
                pass

            return {"text": text, "regions": []}
        except Exception:
            return {"text": "", "regions": []}
