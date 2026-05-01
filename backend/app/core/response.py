"""
统一响应格式，与 docs/api/interface-v2.0.md 中定义的响应结构保持一致。

成功: {"code": 200, "message": "success", "data": {...}}
失败: {"code": 400, "message": "错误原因", "data": null}
分页: {"code": 200, "message": "success", "data": {"pageNum": 1, "pageSize": 10, "total": 128, "records": [...]}}
"""

from typing import Any, Optional


def success(data: Any = None, message: str = "success") -> dict:
    return {"code": 200, "message": message, "data": data}


def error(code: int = 400, message: str = "error", data: Any = None) -> dict:
    return {"code": code, "message": message, "data": data}


def paginated_success(
    records: list,
    total: int,
    page_num: int = 1,
    page_size: int = 10,
    message: str = "success",
) -> dict:
    return {
        "code": 200,
        "message": message,
        "data": {
            "pageNum": page_num,
            "pageSize": page_size,
            "total": total,
            "records": records,
        },
    }
