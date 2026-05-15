# QA 智能问答测试问题与解决方案

## 1. 型号提取：中文问句中 regex 无法匹配型号

**现象**：输入"STM32F103C8T6的GPIO最大频率是多少"，提取不到型号，MySQL 搜不到。

**根因**：Python 3 正则引擎中 `\b`（单词边界）将中文字符视为"单词字符"。`STM32F103C8T6的` 中 `6` 和 `的` 之间不存在 `\b`，导致整个型号匹配失败。

**解决**：正则加上 `flags=re.ASCII`，让 `\b` 只认 ASCII 字母数字。

```python
# backend/app/services/query_service.py
_MODEL_PATTERN = re.compile(
    r'\b([A-Za-z0-9][-A-Za-z0-9/+,.()]{2,30}[A-Za-z0-9])\b',
    flags=re.ASCII,  # 关键修复
)
```

---

## 2. Qdrant 检索：精确 component_id 过滤过严，全库回退引入噪音

**现象**：MySQL 能搜到元件，但 datasheet 检索经常返回空，导致 LLM 不被调用，只返回元件列表。

**根因**：
- 原始代码只按 `component_id` 精确过滤，很多元件的 datasheet 可能关联到同系列其他 variant（如 LM358DR 无数据但 LM358DT 有）
- 全库回退搜索会返回不相关元件（如搜"NSI45015WT1G 参数"搜到电容 datasheet）

**解决**：
1. 精确 component_id 搜索（阈值 0.35）
2. 无结果时全库搜索，但校验结果的 `model` 字段是否与搜索型号共享前缀（至少 4 字符），过滤掉不相关结果
3. 回退结果阈值提高到 0.4

```python
# backend/app/agent/task_dispatcher.py — _searchDatasheet()
# 精确搜索 + model 前缀校验回退 + 阈值过滤
prefix = search_model[:4].lower() if len(search_model) >= 4 else ""
for fp in fallback:
    fm = (fp.payload.get("model", "") if fp.payload else "").lower()
    if fp.score >= 0.4 and prefix and (prefix in fm or fm.startswith(prefix)):
        points.append(fp)
```

---

## 3. 无 datasheet 时不调用 LLM

**现象**：CDBHM160L-HF 在 MySQL 中有记录，但 Qdrant 无 datasheet，API 返回裸元件列表而非自然语言回答。

**根因**：`_generateComponentAnswer()` 开头有 `if not ds_context: return ""`，直接用空字符串跳过 LLM。

**解决**：移除 early return，即使无 datasheet 也让 LLM 基于元件基本信息生成回答，同时说明资料不足。

```python
# 修改前
if not ds_context:
    return ""

# 修改后：无 datasheet 时也给 LLM 基本信息
if ds_context:
    prompt = f"...{ds_context}..."
else:
    prompt = f"...（知识库暂无该型号的详细数据手册，但通过数据库查询到：...）"
```

---

## 4. LLM 回答质量问题

### 4.1 不识别元件类型

**现象**：AP61100QZ6-7 数据库标记为"二极管"，LLM 却说"可能是电源管理IC"。

**根因**：system prompt 没有强制要求使用匹配记录中的类型信息。

**解决**：prompt 明确要求"第一句话必须写型号+类型+厂商"，类型字段标注"必须引用"。

### 4.2 类型字段是分类路径，LLM 照抄斜杠

**现象**：类型字段为"运放/比较器/仪表放大器"，LLM 原样输出，答案不精准。

**根因**：数据库 type 是层级分类路径，direct prompt 让 LLM "选一个"，但无 datasheet 依据时只能瞎猜。

**解决**：告诉 LLM 分类路径仅供参考，应以 datasheet 实际内容为准判断功能。AD8137 因此被正确识别为"差分放大器"而非"运放"。

### 4.3 回答像标签罗列，语句不自然

**现象**："型号LAN8670C2T-E/LMX是通信接口由Microchip Technology生产，封装Tape & Reel (TR)"——无标点、无节奏。

**根因**：prompt 给了僵化的模板"型号XX是XX（类型）由XX（厂商）生产，封装XX"。

**解决**：改用自然语言描述期望风格，给具体例句示范语序和节奏。

### 4.4 回答过于啰嗦/模糊

**现象**：AD8137 的回答堆砌大量参数，包含"性能表现良好"等含糊表述。

**解决**：
- 限定 3-5 个关键参数
- "不确定的不要写"
- 整体控制在 200 字以内

### 最终 system_prompt

```
你是电子元器件应用工程师，用自然流畅的中文回答用户问题。
规则：
1) 开篇一句话概括：型号的具体功能（根据 datasheet 判断，不照抄数据库分类路径）、由谁生产、封装形式；
2) 数据库类型字段是分类路径，仅供参考，实际功能以 datasheet 为准；
3) 只列出 3-5 个最关键的参数，不要堆砌；
4) 有具体数值直接引用，不确定的不要写；
5) 如无 datasheet，用自然语序说明知识库暂无详细资料，再给出基本信息；
6) 整体回答控制在 200 字以内。
```

---

## 5. 基础设施：Qdrant 本地模式 → Docker 迁移

**背景**：本地 Qdrant 210K+ 点触发性能警告，单进程锁限制并发。

**操作**：
- 启动 Docker Qdrant 容器，挂载到 `backend/data/qdrant_storage/`
- 创建迁移脚本 `migrate_qdrant_to_docker.py`，将 `Record` 对象转换为 `PointStruct` 后 upsert
- 224,896 个向量点全部迁入 Docker
- 更新 `vector_store_client.py` 的 `get_qdrant_client()` 为 `QdrantClient(host="localhost", port=6333)`

---

## 关键文件改动汇总

| 文件 | 改动 |
|------|------|
| `app/services/query_service.py` | regex 加 `re.ASCII` |
| `app/agent/task_dispatcher.py` | Qdrant 回退+前缀校验、LLM prompt 多轮优化、无 datasheet 时也调用 LLM |
| `app/external/vector_store_client.py` | 切换到 Docker Qdrant |
| `scripts/import_datasheets_to_qdrant.py` | Docker 模式 + 浏览器 headers |
| `scripts/migrate_qdrant_to_docker.py` | 新增：本地→Docker 迁移脚本 |
| `scripts/test_qa.py` | 新增：问答接口测试脚本 |
| `scripts/diagnose_search.py` | 新增：检索链路诊断脚本 |
