"""测试流程指导问答"""
import sys, os, io
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import httpx, json

res = httpx.post('http://localhost:8000/api/v1/auth/login',
                 json={"account": "user@example.com", "password": "user123"})
token = res.json()["data"]["token"]
print("Login OK\n")

questions = [
    "手工焊接怎么做",
    "SMT贴片流程",
    "胶接工艺步骤",
    "BGA怎么返修",
]

for q in questions:
    print(f"=== Q: {q} ===")
    try:
        res = httpx.post("http://localhost:8000/api/v1/chat/ask",
                         json={"text": q},
                         headers={"Authorization": f"Bearer {token}"},
                         timeout=120)
        d = res.json()
        data = d.get("data", {})
        ans = data.get("answer", "")
        if len(ans) > 400:
            ans = ans[:400] + "..."
        print(f"intent: {data.get('intent','')} | confidence: {data.get('confidence',0)}")
        print(f"answer: {ans}")
    except Exception as e:
        print(f"ERROR: {e}")
    print()
