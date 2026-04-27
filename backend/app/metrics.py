"""
Prometheus 监控指标
"""

import time
from functools import wraps
from typing import Callable, Optional

from fastapi import Request, Response
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    Summary,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

from app.config import get_settings


# ===== 请求指标 =====

REQUEST_COUNT = Counter(
    "rag_api_requests_total",
    "Total API requests",
    ["method", "endpoint", "status_code"],
)

REQUEST_LATENCY = Histogram(
    "rag_api_request_duration_seconds",
    "API request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

ACTIVE_REQUESTS = Gauge(
    "rag_api_active_requests",
    "Number of active API requests",
)


# ===== 业务指标 =====

CHAT_COUNT = Counter(
    "rag_chat_requests_total",
    "Total chat requests",
    ["status"],
)

CHAT_LATENCY = Histogram(
    "rag_chat_duration_seconds",
    "Chat request latency in seconds",
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
)

UPLOAD_COUNT = Counter(
    "rag_upload_requests_total",
    "Total upload requests",
    ["status"],
)


# ===== LLM 指标 =====

LLM_CALL_COUNT = Counter(
    "rag_llm_calls_total",
    "Total LLM calls",
    ["model", "status"],
)

LLM_CALL_LATENCY = Histogram(
    "rag_llm_call_duration_seconds",
    "LLM call latency in seconds",
    ["model"],
    buckets=[1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0],
)

LLM_TOKEN_USAGE = Counter(
    "rag_llm_tokens_total",
    "Total LLM tokens used",
    ["model", "type"],  # type: prompt/completion
)


# ===== Embedding 指标 =====

EMBEDDING_COUNT = Counter(
    "rag_embedding_requests_total",
    "Total embedding requests",
    ["model", "status"],
)

EMBEDDING_LATENCY = Histogram(
    "rag_embedding_duration_seconds",
    "Embedding latency in seconds",
    ["model"],
    buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

EMBEDDING_TEXT_COUNT = Counter(
    "rag_embedding_texts_total",
    "Total texts embedded",
    ["model"],
)


# ===== 向量存储指标 =====

VECTOR_SEARCH_COUNT = Counter(
    "rag_vector_search_total",
    "Total vector search requests",
    ["status"],
)

VECTOR_SEARCH_LATENCY = Histogram(
    "rag_vector_search_duration_seconds",
    "Vector search latency in seconds",
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25],
)

VECTOR_INSERT_COUNT = Counter(
    "rag_vector_insert_total",
    "Total vector insert requests",
    ["status"],
)


# ===== 图存储指标 =====

GRAPH_QUERY_COUNT = Counter(
    "rag_graph_query_total",
    "Total graph queries",
    ["type", "status"],
)

GRAPH_QUERY_LATENCY = Histogram(
    "rag_graph_query_duration_seconds",
    "Graph query latency in seconds",
    ["type"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0],
)


# ===== 缓存指标 =====

CACHE_HIT_COUNT = Counter(
    "rag_cache_hits_total",
    "Total cache hits",
    ["type"],
)

CACHE_MISS_COUNT = Counter(
    "rag_cache_misses_total",
    "Total cache misses",
    ["type"],
)


# ===== 连接指标 =====

MILVUS_CONNECTIONS = Gauge(
    "rag_milvus_connections",
    "Number of Milvus connections",
)

NEO4J_CONNECTIONS = Gauge(
    "rag_neo4j_connections",
    "Number of Neo4j connections",
)


# ===== 工具函数 =====


def track_request(method: str, endpoint: str):
    """请求追踪装饰器"""

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            ACTIVE_REQUESTS.inc()
            start_time = time.time()
            status_code = 500

            try:
                response = await func(*args, **kwargs)
                status_code = 200 if response else 500
                return response
            except Exception as e:
                status_code = 500
                raise
            finally:
                duration = time.time() - start_time
                REQUEST_COUNT.labels(
                    method=method,
                    endpoint=endpoint,
                    status_code=str(status_code),
                ).inc()
                REQUEST_LATENCY.labels(
                    method=method,
                    endpoint=endpoint,
                ).observe(duration)
                ACTIVE_REQUESTS.dec()

        return wrapper

    return decorator


def track_chat():
    """聊天追踪装饰器"""

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                CHAT_COUNT.labels(status=status).inc()
                CHAT_LATENCY.observe(duration)

        return wrapper

    return decorator


def track_llm_call(model: str):
    """LLM 调用追踪"""

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                LLM_CALL_COUNT.labels(model=model, status=status).inc()
                LLM_CALL_LATENCY.labels(model=model).observe(duration)

        return wrapper

    return decorator


def track_embedding(model: str):
    """Embedding 追踪"""

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            texts_count = 0

            try:
                result = func(*args, **kwargs)
                # 尝试获取文本数量
                if args and hasattr(args[0], "__len__"):
                    texts_count = len(args[0])
                elif "texts" in kwargs:
                    texts_count = len(kwargs["texts"])
                return result
            except Exception as e:
                status = "error"
                raise
            finally:
                duration = time.time() - start_time
                EMBEDDING_COUNT.labels(model=model, status=status).inc()
                EMBEDDING_LATENCY.labels(model=model).observe(duration)
                if texts_count > 0:
                    EMBEDDING_TEXT_COUNT.labels(model=model).inc(texts_count)

        return wrapper

    return decorator


# ===== 指标端点 =====


async def metrics():
    """Prometheus 指标端点"""
    from starlette.responses import Response

    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


async def stats():
    """自定义统计端点"""
    settings = get_settings()
    return {
        "version": "2.0.0",
        "environment": settings.ENV,
        "metrics_enabled": settings.METRICS_ENABLED,
    }