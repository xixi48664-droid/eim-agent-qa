"""
服务监控服务 — 对应设计文档 4.15 MonitorService 类

聚合各外部服务的健康状态、API 调用统计和错误日志。
"""
from datetime import datetime, timedelta
from sqlalchemy import func
from app.repositories.history_repository import HistoryRepository
from app.entities.operation_log import OperationLog
from app.external.model_client import ModelClient
from app.external.ocr_client import OcrClient
from app.external.vector_store_client import VectorStoreClient
from app.external.file_storage_client import FileStorageClient


class MonitorService:
    """收集、汇总各服务健康状态与运行统计"""

    def __init__(self, history_repo: HistoryRepository):
        self._historyRepository = history_repo
        self._modelClient = ModelClient()
        self._ocrClient = OcrClient()
        self._vectorStoreClient = VectorStoreClient()
        self._fileStorageClient = FileStorageClient()

    def getServiceStatus(self) -> dict:
        """获取各服务健康状态总览 — 对应 MonitorService.getServiceStatus"""
        results = self._collectServiceHealth()

        all_ok = all(
            r.get("status") == "available"
            for r in results.values()
        )
        return {
            "overall": "healthy" if all_ok else "degraded",
            "services": results,
            "checkedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    def getApiStatistics(self, hours: int = 24) -> dict:
        """统计 API 调用情况 — 对应 MonitorService.getApiStatistics"""
        db = self._historyRepository._db
        since = datetime.now() - timedelta(hours=hours)

        total = (
            db.query(func.count(OperationLog.log_id))
            .filter(OperationLog.operation_time >= since)
            .scalar() or 0
        )

        by_type = (
            db.query(
                OperationLog.operation_type,
                func.count(OperationLog.log_id),
            )
            .filter(OperationLog.operation_time >= since)
            .group_by(OperationLog.operation_type)
            .all()
        )

        qps = round(total / (hours * 3600), 3) if hours > 0 else 0

        return {
            "hours": hours,
            "totalCalls": total,
            "qps": qps,
            "byType": [
                {"type": t, "count": c}
                for t, c in by_type
            ],
        }

    def getLatencyStats(self, hours: int = 24) -> dict:
        """统计推理延迟"""
        db = self._historyRepository._db
        since = datetime.now() - timedelta(hours=hours)

        rows = (
            db.query(OperationLog.response_time_ms)
            .filter(
                OperationLog.operation_time >= since,
                OperationLog.response_time_ms.isnot(None),
            )
            .all()
        )

        values = []
        for (v,) in rows:
            try:
                values.append(float(v))
            except (ValueError, TypeError):
                pass

        if not values:
            return {"hours": hours, "avgMs": 0, "maxMs": 0, "count": 0}

        return {
            "hours": hours,
            "avgMs": round(sum(values) / len(values), 1),
            "maxMs": round(max(values), 1),
            "count": len(values),
        }

    def getTimeSeries(self, hours: int = 24) -> list[dict]:
        """获取按小时聚合的调用时间序列"""
        db = self._historyRepository._db
        since = datetime.now() - timedelta(hours=hours)

        rows = (
            db.query(
                func.date_format(OperationLog.operation_time, "%Y-%m-%dT%H:00:00"),
                func.count(OperationLog.log_id),
            )
            .filter(OperationLog.operation_time >= since)
            .group_by(func.date_format(OperationLog.operation_time, "%Y-%m-%dT%H:00:00"))
            .order_by(func.date_format(OperationLog.operation_time, "%Y-%m-%dT%H:00:00"))
            .all()
        )

        return [{"time": t, "count": c} for t, c in rows]

    def getErrorLogs(self, hours: int = 24) -> dict:
        """获取近期错误日志 — 对应 MonitorService.getErrorLogs"""
        db = self._historyRepository._db
        since = datetime.now() - timedelta(hours=hours)

        logs = (
            db.query(OperationLog)
            .filter(
                OperationLog.operation_time >= since,
                OperationLog.operation_result.in_(["失败", "错误", "异常"]),
            )
            .order_by(OperationLog.operation_time.desc())
            .limit(50)
            .all()
        )

        return {
            "hours": hours,
            "total": len(logs),
            "records": [
                {
                    "time": log.operation_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "type": log.operation_type,
                    "target": log.operation_target or "",
                    "result": log.operation_result or "",
                }
                for log in logs
            ],
        }

    def _collectServiceHealth(self) -> dict:
        """采集各外部服务健康状态 — 对应 MonitorService._collectServiceHealth"""
        result = {}

        # 模型服务
        try:
            result["modelService"] = self._modelClient.checkServiceHealth()
        except Exception as e:
            result["modelService"] = {"status": "unavailable", "detail": str(e)}

        # OCR 服务
        try:
            result["ocrService"] = self._ocrClient.checkServiceHealth()
        except Exception as e:
            result["ocrService"] = {"status": "unavailable", "detail": str(e)}

        # 向量数据库
        try:
            result["vectorStore"] = self._vectorStoreClient.checkStoreHealth()
        except Exception as e:
            result["vectorStore"] = {"status": "unavailable", "detail": str(e)}

        # 文件存储
        try:
            result["fileStorage"] = self._fileStorageClient.checkStorageHealth()
        except Exception as e:
            result["fileStorage"] = {"status": "unavailable", "detail": str(e)}

        # 数据库连接
        try:
            db = self._historyRepository._db
            db.execute(db.query(func.count(OperationLog.log_id)).statement)
            result["database"] = {"status": "available"}
        except Exception as e:
            result["database"] = {"status": "unavailable", "detail": str(e)}

        return result
