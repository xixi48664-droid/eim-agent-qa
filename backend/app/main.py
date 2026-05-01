"""
FastAPI 应用入口。

启动方式（在 backend/ 目录下执行）:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.user_controller import router as user_controller_router
from app.api.admin_controller import router as admin_controller_router
from app.api.qa_controller import router as qa_controller_router

app = FastAPI(
    title="EIM Agent QA API",
    description="基于智能体的电子信息制造业多模态图文问答系统 - 后端接口（V1.0）",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_controller_router)
app.include_router(admin_controller_router)
app.include_router(qa_controller_router)


@app.get("/")
def root():
    return {"message": "EIM Agent QA API v1.0"}
