"""
FastAPI 应用入口 - 生产级版本
集成中间件、异常处理、监控、安全
"""

import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.logging import get_logger, log_request
from app.exceptions import RAGException
from app.api.router import api_router
from app.metrics import metrics, stats as metrics_stats


logger = get_logger(__name__)
settings = get_settings()


def init_databases():
    """在后台线程初始化数据库连接"""
    import threading

    def _init():
        # 延迟初始化，懒加载
        pass

    thread = threading.Thread(target=_init, daemon=True)
    thread.start()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期"""
    logger.info("Starting RAG Knowledge Base v2.0.0...")
    init_databases()

    # 预热
    if settings.is_production:
        logger.info("Warming up...")
        try:
            from app.dependencies import get_vector_store
            store = get_vector_store()
            store.init_collection()
        except Exception as e:
            logger.warning(f"Warmup failed: {e}")

    yield

    logger.info("Shutting down...")
    # 清理资源
    try:
        from app.core.pool import MilvusConnectionPool, Neo4jConnectionPool
        MilvusConnectionPool.close_all()
        Neo4jConnectionPool.close_all()
    except Exception as e:
        logger.warning(f"Cleanup error: {e}")


# ===== 应用 =====

app = FastAPI(
    title="RAG 知识库问答系统",
    description="基于 LangChain + Milvus + Neo4j 的 RAG 系统",
    version="2.0.0",
    lifespan=lifespan,
)


# ===== 中间件 =====


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if not settings.is_production else settings.API_V1_PREFIX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 请求日志
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录请求"""
    if settings.METRICS_ENABLED:
        start_time = time.time()

    response = await call_next(request)

    if settings.METRICS_ENABLED:
        from app.metrics import REQUEST_COUNT, REQUEST_LATENCY, ACTIVE_REQUESTS

        duration = time.time() - start_time
        status_code = response.status_code

        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status_code=str(status_code),
        ).inc()
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.url.path,
        ).observe(duration)

    return response


# ===== 异常处理 =====


@app.exception_handler(RAGException)
async def rag_exception_handler(request: Request, exc: RAGException):
    """RAG 异常处理"""
    logger.error(f"RAG exception: {exc.message}")

    # 生产环境不暴露内部信息
    if settings.is_production:
        error_detail = "Internal server error"
    else:
        error_detail = exc.message

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": error_detail,
            }
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    if settings.is_production:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Internal server error",
                }
            },
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": str(exc),
                    "details": {"type": type(exc).__name__},
                }
            },
        )


# ===== 路由 =====

app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# ===== 指标端点 =====

app.add_route("/metrics", metrics)
app.add_route("/stats", metrics_stats)


# ===== 基础接口 =====


@app.get("/")
async def root():
    return {
        "message": "RAG 知识库问答系统 API",
        "version": "2.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    milvus_status = "unhealthy"
    neo4j_status = "unhealthy"

    try:
        from app.dependencies import get_vector_store

        store = get_vector_store()
        if store.check_connection():
            milvus_status = "healthy"
    except Exception:
        pass

    try:
        from app.dependencies import get_graph_store

        store = get_graph_store()
        if store.check_connection():
            neo4j_status = "healthy"
    except Exception:
        pass

    overall = "healthy" if milvus_status == "healthy" and neo4j_status == "healthy" else "degraded"

    return {
        "status": overall,
        "milvus": milvus_status,
        "neo4j": neo4j_status,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/health/deep")
async def deep_health_check():
    """深度健康检查"""
    checks = {}

    # Milvus
    try:
        from app.dependencies import get_vector_store

        store = get_vector_store()
        checks["milvus"] = {
            "status": "healthy" if store.check_connection() else "unhealthy"
        }
    except Exception as e:
        checks["milvus"] = {"status": "unhealthy", "error": str(e)}

    # Neo4j
    try:
        from app.dependencies import get_graph_store

        store = get_graph_store()
        checks["neo4j"] = {
            "status": "healthy" if store.check_connection() else "unhealthy"
        }
    except Exception as e:
        checks["neo4j"] = {"status": "unhealthy", "error": str(e)}

    # Embedding
    try:
        from app.dependencies import get_embedding_model

        model = get_embedding_model()
        dim = model.get_dimension()
        checks["embedding"] = {"status": "healthy", "dimension": dim}
    except Exception as e:
        checks["embedding"] = {"status": "unhealthy", "error": str(e)}

    all_healthy = all(c.get("status") == "healthy" for c in checks.values())

    return {
        "status": "healthy" if all_healthy else "degraded",
        "checks": checks,
        "timestamp": datetime.now().isoformat(),
    }


# ===== 运行 =====


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        log_level=settings.LOG_LEVEL.lower(),
        reload=settings.DEBUG,
    )