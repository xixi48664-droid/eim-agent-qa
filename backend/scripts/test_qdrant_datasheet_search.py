"""
测试 Datasheet Qdrant 检索。

用法:
    python scripts/test_qdrant_datasheet_search.py --model "STM32F103C8T6" --query "工作电压"
    python scripts/test_qdrant_datasheet_search.py --model "ESP32" --query "功耗多少"
    python scripts/test_qdrant_datasheet_search.py --query "ADC resolution" --top-k 5
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from qdrant_client import QdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

from app.db.mysql import SessionLocal
from app.entities.component_info import Component
from app.external.model_client import ModelClient

QDRANT_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "qdrant")
COLLECTION_NAME = "component_datasheets"


def main():
    parser = argparse.ArgumentParser(description="测试 Datasheet Qdrant 检索")
    parser.add_argument("--model", type=str, help="元器件型号，用于过滤 component_id")
    parser.add_argument("--query", type=str, required=True, help="查询问题")
    parser.add_argument("--top-k", type=int, default=5, help="返回结果数 (默认 5)")
    args = parser.parse_args()

    # 1. 构建 filter
    qdrant_filter = None
    if args.model:
        db = SessionLocal()
        try:
            comps = db.query(Component).filter(Component.model == args.model).all()
            if not comps:
                print(f"未找到型号: {args.model}")
                return
            component_ids = [c.component_id for c in comps]
            print(f"型号 '{args.model}' 对应 {len(component_ids)} 条 component 记录:")
            for c in comps:
                print(f"  {c.model}  [{c.type}]  {c.manufacturer}")
            print()
            if len(component_ids) == 1:
                qdrant_filter = Filter(
                    must=[FieldCondition(key="component_id", match=MatchValue(value=component_ids[0]))]
                )
            else:
                qdrant_filter = Filter(
                    should=[FieldCondition(key="component_id", match=MatchValue(value=cid)) for cid in component_ids]
                )
        finally:
            db.close()

    # 2. 向量化查询
    model_client = ModelClient()
    embeddings = model_client.embedTexts([args.query])
    if not embeddings:
        print("Embedding 失败")
        return

    # 3. 检索 Qdrant
    qdrant = QdrantClient(path=QDRANT_DIR)
    if not qdrant.collection_exists(COLLECTION_NAME):
        print(f"Qdrant collection '{COLLECTION_NAME}' 不存在，请先运行 import 脚本")
        return

    results = qdrant.query_points(
        collection_name=COLLECTION_NAME,
        query=embeddings[0],
        query_filter=qdrant_filter,
        limit=args.top_k,
    ).points

    info = qdrant.get_collection(COLLECTION_NAME)
    print(f"Qdrant collection: {info.points_count} points")
    print(f"查询: '{args.query}'")
    print(f"过滤: {'component_id=' + component_ids[0] if args.model and len(component_ids) == 1 else ('component_id in [' + ','.join(component_ids[:3]) + '...]' if args.model and len(component_ids) > 1 else '无')}")
    print(f"结果数: {len(results)}")
    print()

    # 4. 输出结果
    for i, r in enumerate(results):
        p = r.payload or {}
        print(f"#{i+1}  score={r.score:.4f}  page={p.get('page', '?')}  model={p.get('model', '?')}")
        print(f"    datasheet: {p.get('datasheet_url', '')[:100]}")
        text = p.get("text", "")
        # 截取显示
        display_text = text[:300] + ("..." if len(text) > 300 else "")
        print(f"    text: {display_text}")
        print()


if __name__ == "__main__":
    main()
