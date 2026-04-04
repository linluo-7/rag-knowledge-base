"""
API 路由汇总
"""

from fastapi import APIRouter

from app.api import upload, chat, graph

api_router = APIRouter()

# 注册子路由
api_router.include_router(upload.router, prefix="/upload", tags=["文档上传"])
api_router.include_router(chat.router, prefix="/chat", tags=["问答"])
api_router.include_router(graph.router, prefix="/graph", tags=["知识图谱"])
