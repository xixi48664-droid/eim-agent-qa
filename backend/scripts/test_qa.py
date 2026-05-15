"""测试 QA 问答接口"""
import sys, os, io
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import httpx, json

res = httpx.post("http://localhost:8000/api/v1/auth/login",
                 json={"account": "user@example.com", "password": "user123"})
token = res.json()["data"]["token"]
print("Login OK\n")

questions = [
    "AD8137YRZ-REEL 的相关参数",
]
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

for q in questions:
    print(f"=== Q: {q} ===")
    res = httpx.post("http://localhost:8000/api/v1/chat/ask",
                     json={"text": q}, headers=headers, timeout=120)
    d = res.json().get("data", {})
    ans = d.get("answer", "")
    if len(ans) > 200:
        ans = ans[:200] + "..."
    print(f"answer: {ans}")
    print(f"intent: {d.get('intent','')} | confidence: {d.get('confidence',0)} | sources: {len(d.get('sources',[]))}")
    for s in d.get("sources", []):
        print(f"  [{s.get('sourceType','')}] {s.get('sourceTitle','')[:50]} | {s.get('contentSnippet','')[:80]}")
    print()
