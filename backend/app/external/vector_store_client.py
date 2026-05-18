"""
向量数据库适配器 — 对应设计文档 4.33 VectorStoreClient 类

基于 Qdrant 本地模式 + DashScope text-embedding-v3 实现语义检索。
"""
import os
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from app.core.config import settings
from app.external.model_client import ModelClient


DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "qdrant")
EMBEDDING_DIM = 1024  # text-embedding-v4 输出维度
COLLECTION_NAME = "knowledge"

_qdrant_client = None


def get_qdrant_client() -> QdrantClient:
    """返回进程内唯一的 QdrantClient 实例"""
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = QdrantClient(host="localhost", port=6333, timeout=60)
    return _qdrant_client


class VectorStoreClient:
    """封装与 Qdrant 向量数据库之间的交互"""

    def __init__(self):
        self._client = get_qdrant_client()
        self._modelClient = ModelClient()
        self._available = False
        try:
            self._ensureCollection()
            self._available = True
        except Exception:
            self._available = False

    def _ensureCollection(self):
        if not self._client.collection_exists(COLLECTION_NAME):
            self._client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=EMBEDDING_DIM,
                    distance=Distance.COSINE,
                ),
            )

    @property
    def isAvailable(self) -> bool:
        return self._available

    def search(self, query_text: str, top_k: int = 5) -> list:
        """语义检索 — 嵌入查询文本，搜索最相似的向量"""
        if not self._available or not query_text or not query_text.strip():
            return []

        embeddings = self._modelClient.embedTexts([query_text.strip()])
        if not embeddings:
            return []

        results = self._client.query_points(
            collection_name=COLLECTION_NAME,
            query=embeddings[0],
            limit=top_k,
        ).points

        return [
            {
                "id": r.id,
                "score": r.score,
                "metadata": r.payload.get("metadata", {}),
                "content": r.payload.get("content", ""),
            }
            for r in results
        ]

    def insert(self, doc_id: str, text: str, metadata: dict) -> dict:
        """写入一条向量记录"""
        embeddings = self._modelClient.embedTexts([text])
        if not embeddings:
            raise RuntimeError("Embedding returned empty")

        self._client.upsert(
            collection_name=COLLECTION_NAME,
            points=[
                PointStruct(
                    id=doc_id,
                    vector=embeddings[0],
                    payload={"content": text, "metadata": metadata},
                )
            ],
        )
        return {"id": doc_id, "status": "inserted"}

    def delete(self, doc_id: str) -> dict:
        """删除指定向量记录"""
        self._client.delete(collection_name=COLLECTION_NAME, points_selector=[doc_id])
        return {"id": doc_id, "status": "deleted"}

    def clear(self):
        """清空集合（重建）"""
        self._client.delete_collection(COLLECTION_NAME)
        self._ensureCollection()

    def checkStoreHealth(self) -> dict:
        """检测向量数据库是否可用"""
        try:
            info = self._client.get_collection(COLLECTION_NAME)
            return {
                "status": "available",
                "mode": "qdrant-local",
                "points_count": info.points_count,
            }
        except Exception as e:
            return {"status": "unavailable", "detail": str(e)}
