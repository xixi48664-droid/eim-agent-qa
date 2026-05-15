# AI 智能问答 Bug 修复记录

## 问题现象

用户使用自然语言提问元器件相关问题，AI 问答始终返回"未找到匹配的元器件"。测试用例如下：

- "ANNA-B402-00B 的供电电压范围是多少？"
- "74HC4052 的工作温度范围？"
- "AT32UC3B 有多少个 GPIO？"

三个问题全部显示"未匹配"。

---

## Bug 1：自然语言问句直接传入 MySQL LIKE 查询

**文件**：`backend/app/services/query_service.py`

**根因**：`TaskDispatcher.dispatch` 将用户的完整中文问句（如 `"ANNA-B402-00B 的供电电压范围是多少？"`）原封不动传给 `QueryService.searchByKeyword` → `ComponentRepository.searchByKeyword`，底层执行 `LIKE '%完整中文问句%'`，当然匹配不到任何型号。

**修复**：在 `QueryService` 中新增 `_extractModel()` 方法，用正则从自然语言中提取元器件型号：

```python
_MODEL_PATTERN = re.compile(
    r'\b([A-Za-z0-9][-A-Za-z0-9/+,.()]{2,30}[A-Za-z0-9])\b'
)
```

`searchByKeyword` 调用前先执行 `search_keyword = self._extractModel(keyword)`，将 "ANNA-B402-00B 的供电电压范围是多少？" 提取为 "ANNA-B402-00B" 再传入 MySQL。

---

## Bug 2：datasheet 向量库路径错误

**文件**：`backend/app/agent/task_dispatcher.py:34`

**根因**：`_getDatasheetQdrant()` 中拼接 Qdrant 数据目录时少了一层 `..`：

```python
# 错误：解析为 backend/app/data/qdrant（不存在）
QDRANT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "qdrant")

# 正确：解析为 backend/data/qdrant（实际数据位置）
QDRANT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "qdrant")
```

`__file__` 位于 `backend/app/agent/task_dispatcher.py`，需要向上两级才能到达 `backend/`。

---

## Bug 3：Qdrant 本地模式锁冲突

**文件**：
- `backend/app/external/vector_store_client.py`
- `backend/app/agent/task_dispatcher.py`

**根因**：Qdrant 本地模式（文件存储）**只允许单个进程内的单个 `QdrantClient` 实例**访问同一目录。但代码中存在两处独立的 `QdrantClient` 创建：

1. `VectorStoreClient.__init__` → `QdrantClient(path=DATA_DIR)` — 在 `QaService` 构造时创建
2. `TaskDispatcher._getDatasheetQdrant()` → `QdrantClient(path=QDRANT_DIR)` — 在查询 datasheet 时延迟创建

两者指向同一目录 `backend/data/qdrant`。当请求进入 `/api/v1/chat/ask` 时：
- `_buildOrchestrator` 先创建 `QaService`（包含 `VectorStoreClient`），持有锁
- 后续 `_searchDatasheet` 尝试创建第二个 `QdrantClient`，抛出 `AlreadyLocked`
- 被 `except Exception: pass` 静默吞掉，返回空字符串

**修复**：

1. 在 `vector_store_client.py` 中新增模块级单例函数：

```python
_qdrant_client = None

def get_qdrant_client() -> QdrantClient:
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = QdrantClient(path=DATA_DIR)
    return _qdrant_client
```

2. `VectorStoreClient` 和 `TaskDispatcher` 均改为调用 `get_qdrant_client()` 获取同一个实例，确保全进程只有一个 `QdrantClient`。

---

## 附加修复：缺少 Optional 导入

**文件**：`backend/app/api/qa_controller.py:36`

函数签名使用了 `Optional[str]` 但未导入 `Optional`，导致 uvicorn 启动失败。添加 `from typing import Optional`。

---

## 修复后效果

| 测试问题 | 修复前 | 修复后 |
|---|---|---|
| ANNA-B402-00B 供电电压 | 未找到匹配 | 找到 1 个元器件 + datasheet 内容片段（供电电压 1.7-3.6V） |
| 74HC4052 工作温度 | 未找到匹配 | 找到 4 个元器件（首个匹配 CD74HC4052M96 无 datasheet 数据） |
| AT32UC3B GPIO | 未找到匹配 | 找到 14 个元器件 + datasheet 内容片段（配置摘要） |
