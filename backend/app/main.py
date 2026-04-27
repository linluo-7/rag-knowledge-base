"""
FastAPI 应用入口
集成中间件、异常处理、监控等
"""

import time
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.logging import get_logger, log_request
from app.exceptions import RAGException
from app.api.router import api_router


logger = get_logger(__name__)
settings = get_settings()


def init_databases():
    """在后台线程初始化数据库连接"""
    import threading

    def _init():
        try:
            vector_store = get_settings()
            from app.factory import get_vector_store

            store = get_vector_store()
            store.init_collection()
            logger.info("Milvus connected")
        except Exception as e:
            logger.warning(f"Milvus connection failed: {e}")

        try:
            from app.factory import get_graph_store

            store = get_graph_store()
            store.init_schema()
            logger.info("Neo4j connected")
        except Exception as e:
            logger.warning(f"Neo4j connection failed: {e}")

    thread = threading.Thread(target=_init, daemon=True)
    thread.start()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("Starting RAG Knowledge Base System...")
    init_databases()
    yield
    logger.info("Shutting down RAG Knowledge Base System...")


# 创建 FastAPI 应用
app = FastAPI(
    title="RAG 知识库问答系统",
    description="基于 LangChain + Milvus + Neo4j 的 RAG 系统",
    version="2.0.0",
    lifespan=lifespan,
)

# ===== 中间件 =====

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.API_V1_PREFIX if settings.is_production else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录请求日志"""
    start_time = time.time()

    response = await call_next(request)

    latency_ms = (time.time() - start_time) * 1000
    log_request(
        method=request.method,
        path=str(request.url.path),
        status_code=response.status_code,
        latency_ms=latency_ms,
    )

    return response


# ===== 异常处理 =====


@app.exception_handler(RAGException)
async def rag_exception_handler(request: Request, exc: RAGException):
    """RAG 异常处理器"""
    logger.error(f"RAG exception: {exc.message}")
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理器"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Internal server error",
                "details": {"error": str(exc)} if settings.DEBUG else {},
            }
        },
    )


# ===== 路由 =====

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# ===== 基础接口 =====


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "RAG 知识库问答系统 API",
        "version": "2.0.0",
        "docs": "/docs",
    }


@app.get("/health", tags=["健康检查"])
async def health_check():
    """健康检查"""
    from app.factory import get_vector_store, get_graph_store

    milvus_status = "unhealthy"
    neo4j_status = "unhealthy"

    try:
        store = get_vector_store()
        if store.check_connection():
            milvus_status = "healthy"
    except Exception:
        pass

    try:
        store = get_graph_store()
        if store.check_connection():
            neo4j_status = "healthy"
    except Exception:
        pass

    return {
        "status": "ok" if milvus_status == "healthy" and neo4j_status == "healthy" else "degraded",
        "milvus": milvus_status,
        "neo4j": neo4j_status,
        "timestamp": datetime.now().isoformat(),
    }


# ===== 运行入口 =====


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT,
        log_level=settings.LOG_LEVEL.lower(),
    )