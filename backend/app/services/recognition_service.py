"""
拍照识件服务 — 对应设计文档 4.9 RecognitionService 类

编排 OCR → 多模态模型 → 数据库匹配管线。
"""
from app.repositories.component_repository import ComponentRepository
from app.external.ocr_client import OcrClient
from app.external.model_client import ModelClient


class RecognitionService:
    """图像预处理、OCR 调用、模型调用和元器件匹配"""

    ALLOWED_CONTENT_TYPES = {
        "image/jpeg", "image/png", "image/gif", "image/webp", "image/bmp",
    }
    MAX_FILE_SIZE = 10 * 1024 * 1024

    def __init__(self, component_repo: ComponentRepository):
        self._componentRepository = component_repo
        self._ocrClient = OcrClient()
        self._visionClient = ModelClient()

    def recognize(self, image_data: bytes) -> dict:
        """识别元器件 — 对应 RecognitionService.recognize

        管线: 预处理 → OCR 提取文字 → 模型预测 → DB 匹配
        """
        processed = self._preprocessImage(image_data)
        ocr_result = self._ocrClient.extractText(processed)
        model_result = self._visionClient.predictImage(processed)

        ocr_text = ocr_result.get("text", "")
        model_name = model_result.get("model", "")
        model_confidence = model_result.get("confidence", 0.0)

        match = self.matchComponent(
            {"model": model_name, "type": model_result.get("type", "")},
            {"text": ocr_text},
        )

        result = {
            "model": model_name,
            "type": model_result.get("type", ""),
            "packageType": model_result.get("package", ""),
            "manufacturer": "",
            "confidence": model_confidence,
            "ocrText": ocr_text,
            "componentId": None,
        }

        if match:
            result["componentId"] = match.get("componentId")
            result["manufacturer"] = match.get("manufacturer", "")
            result["packageType"] = result["packageType"] or match.get("packageType", "")

        return self._filterLowConfidence(result)

    def matchComponent(self, features: dict, texts: dict) -> dict | None:
        """根据图像特征和OCR文字匹配数据库元器件 — 对应 RecognitionService.matchComponent"""
        model_name = features.get("model", "").strip()
        ocr_text = texts.get("text", "").strip()

        if model_name:
            components, _ = self._componentRepository.searchByKeyword(model_name, 1, 1)
            if components:
                c = components[0]
                return {
                    "componentId": c.component_id,
                    "model": c.model,
                    "type": c.type or "",
                    "manufacturer": c.manufacturer or "",
                    "packageType": c.package_type or "",
                }

        if ocr_text:
            for line in ocr_text.split("\n"):
                line = line.strip()
                if len(line) >= 4:
                    components, _ = self._componentRepository.searchByKeyword(line, 1, 1)
                    if components:
                        c = components[0]
                        return {
                            "componentId": c.component_id,
                            "model": c.model,
                            "type": c.type or "",
                            "manufacturer": c.manufacturer or "",
                            "packageType": c.package_type or "",
                        }

        return None

    def _preprocessImage(self, image_data: bytes) -> bytes:
        """预处理图片：缩放大图以降低 API 调用延迟和成本"""
        from PIL import Image
        from io import BytesIO

        img = Image.open(BytesIO(image_data))
        max_dim = 2048
        if img.width > max_dim or img.height > max_dim:
            ratio = max_dim / max(img.width, img.height)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)

        buf = BytesIO()
        img_format = img.format or "JPEG"
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(buf, format=img_format, quality=85)
        return buf.getvalue()

    def _filterLowConfidence(self, result: dict, threshold: float = 0.5) -> dict:
        """过滤低置信度结果 — 当前直接返回，仅标记低置信度"""
        if result.get("confidence", 0.0) < threshold:
            result["model"] = result.get("model", "") + "（低置信度）"
        return result
