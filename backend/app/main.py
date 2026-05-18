"""
FastAPI 应用入口。

启动方式（在 backend/ 目录下执行）:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.user_controller import router as user_controller_router
from app.api.user_controller import user_router as user_profile_router
from app.api.admin_controller import router as admin_controller_router
from app.api.admin_controller import component_router as admin_component_router
from app.api.admin_controller import standard_router as admin_standard_router
from app.api.admin_controller import tutorial_router as admin_tutorial_router
from app.api.admin_controller import monitor_router as admin_monitor_router
from app.api.admin_controller import knowledge_router as admin_knowledge_router
from app.api.qa_controller import router as qa_controller_router
from app.api.qa_controller import chat_router as chat_router
from app.api.qa_controller import tutorial_guide_router as tutorial_guide_router
from app.api.qa_controller import standards_router as standards_router
from app.api.file_controller import router as file_router
from app.api.recognition_controller import router as recognition_router

app = FastAPI(
    title="EIM Agent QA API",
    description="基于智能体的电子信息制造业多模态图文问答系统 - 后端接口（V1.0）",
    version="1.0.0",
    openapi_tags=[
        {"name": "认证", "description": "登录、注册、忘记密码、重置密码"},
        {"name": "个人中心", "description": "个人信息查看/编辑、修改密码、活动统计、操作记录"},
        {"name": "智能问答", "description": "元器件搜索、AI 综合问答、拍照识件、流程指导、规范文档、问答历史"},
        {"name": "文件管理", "description": "文件上传、下载、删除"},
        {"name": "用户管理", "description": "管理员 — 用户列表、启用/禁用、重置密码、批量操作"},
        {"name": "元器件管理", "description": "管理员 — 元器件增删改查"},
        {"name": "规范管理", "description": "管理员 — 工艺规范增删改查"},
        {"name": "教程管理", "description": "管理员 — 教程及步骤增删改查"},
        {"name": "服务监控", "description": "管理员 — 服务健康状态、API 统计、响应时间"},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_controller_router)
app.include_router(user_profile_router)
app.include_router(admin_controller_router)
app.include_router(admin_component_router)
app.include_router(admin_standard_router)
app.include_router(admin_tutorial_router)
app.include_router(admin_monitor_router)
app.include_router(admin_knowledge_router)
app.include_router(qa_controller_router)
app.include_router(chat_router)
app.include_router(tutorial_guide_router)
app.include_router(standards_router)
app.include_router(file_router)
app.include_router(recognition_router)


@app.get("/")
def root():
    return {"message": "EIM Agent QA API v1.0"}
