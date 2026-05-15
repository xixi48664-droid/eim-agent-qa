"""诊断 datasheet 检索链路 — 模拟实际 API 调用"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.query_service import QueryService
from app.repositories.component_repository import ComponentRepository
from app.db.mysql import SessionLocal
from app.external.model_client import ModelClient
from app.external.vector_store_client import get_qdrant_client
from qdrant_client.models import Filter, FieldCondition, MatchValue

db = SessionLocal()
repo = ComponentRepository(db)
qs = QueryService(repo)

questions = [
    "STM32F103C8T6的GPIO最大频率是多少",
    "AMS1117-3.3输出电压精度",
    "LM358的工作温度范围",
]

for text in questions:
    print(f"{'='*60}")
    print(f"Input: {text}")
    print()

    # Step 1: extract model
    model = qs._extractModel(text)
    print(f"  Extracted model: {model}")

    # Step 2: MySQL search
    result = qs.searchByKeyword(text)
    records = result.get("records", [])
    print(f"  MySQL results: {len(records)} records")
    for r in records[:3]:
        print(f"    - {r.get('model','')} (cid={r.get('componentId','')[:20]}...)")

    if not records:
        print("  -> No components found")
        print()
        continue

    # Step 3: Qdrant search
    component_id = records[0].get("componentId", "")
    print(f"  Searching Qdrant for cid={component_id[:20]}...")
    try:
        qdrant = get_qdrant_client()
        if not qdrant.collection_exists("component_datasheets"):
            print(f"  -> Collection NOT FOUND")
            continue

        mc = ModelClient()
        emb = mc.embedTexts([text])
        if not emb:
            print(f"  -> Embedding FAILED")
            continue

        results = qdrant.query_points(
            collection_name="component_datasheets",
            query=emb[0],
            query_filter=Filter(
                must=[FieldCondition(key="component_id", match=MatchValue(value=component_id))]
            ),
            limit=3,
        ).points
        print(f"  Qdrant results: {len(results)}")
        if results:
            for r in results:
                print(f"    - score={r.score:.3f} text={r.payload.get('text','')[:80] if r.payload else 'N/A'}")
        else:
            print(f"  -> No datasheet matches for this component!")

            # Check if ANY data exists in Qdrant for this component (unfiltered)
            all_results = qdrant.query_points(
                collection_name="component_datasheets",
                query=emb[0],
                limit=3,
            ).points
            if all_results:
                sample = all_results[0].payload or {}
                print(f"  Sample Qdrant cid: {sample.get('component_id','')}")
                print(f"  Qdrant has components, but not this one")
    except Exception as e:
        print(f"  -> Qdrant search FAILED: {type(e).__name__}: {e}")

    print()

db.close()
