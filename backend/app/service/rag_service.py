"""
RAG 服务层 - 生产级版本
真正的异步实现 + 依赖注入
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Optional

from app.config import get_settings
from app.dependencies import (
    get_vector_store,
    get_graph_store,
    get_embedding_model,
    get_fusion,
    get_llm,
    get_cache,
)
from app.exceptions import RAGException, VectorStoreError, GraphStoreError
from app.logging import get_logger, log_rag_query, log_llm_call
from app.service.rag_service_base import RAGServiceBase


logger = get_logger(__name__)

# 线程池用于 CPU 密集型任务
_executor = ThreadPoolExecutor(max_workers=4)


class RAGService(RAGServiceBase):
    """RAG 服务 - 生产级版本

    特性：
    - 真正的异步实现（用 run_in_executor）
    - 依赖注入
    - 并行检索
    - 缓存支持
    - 链路追踪
    """

    def __init__(self):
        settings = get_settings()
        self.top_k = settings.TOP_K
        self.max_context_k = settings.MAX_CONTEXT_K
        self.rrf_k = settings.RRF_K

    async def chat(
        self,
        question: str,
        user_id: Optional[str] = None,
        top_k: Optional[int] = None,
    ) -> dict:
        """RAG 问答流程"""
        start_time = time.time()
        top_k = top_k or self.top_k
        settings = get_settings()

        try:
            # ===== 1. 获取依赖 =====
            vector_store = get_vector_store()
            graph_store = get_graph_store()
            embedding_model = get_embedding_model()

            # ===== 2. 并行执行向量化和图谱扩展 =====
            # Embedding 是 CPU 密集型，用线程池
            loop = asyncio.get_event_loop()
            query_vector = await loop.run_in_executor(
                _executor, partial(embedding_model.embed_query, question)
            )

            # 并行检索
            milvus_task = loop.run_in_executor(
                _executor,
                partial(vector_store.search, query_vector, top_k),
            )
            graph_task = loop.run_in_executor(
                _executor,
                partial(graph_store.expand_entities, question),
            )

            milvus_results, graph_entities = await asyncio.gather(
                milvus_task, graph_task
            )

            # ===== 3. 图谱扩展检索 =====
            neo4j_results = []
            if graph_entities:
                # 并行查询相关文档
                tasks = []
                for entity in graph_entities[:5]:
                    task = loop.run_in_executor(
                        _executor,
                        partial(vector_store.search_by_text, entity.name, top_k=2),
                    )
                    tasks.append(task)

                results = await asyncio.gather(*tasks)
                for r in results:
                    neo4j_results.extend(r)

            # ===== 4. RRF 融合 =====
            fusion = get_fusion()
            fused_results = fusion.fuse(milvus_results, neo4j_results, k=self.rrf_k)

            # ===== 5. 构建上下文 =====
            context = "\n\n".join([
                r["content"]
                for r in fused_results[: self.max_context_k]
            ])

            # ===== 6. LLM 生成 =====
            llm = get_llm()
            llm_start = time.time()
            llm_response = await loop.run_in_executor(
                _executor,
                partial(llm.generate, question, context),
            )
            llm_latency = (time.time() - llm_start) * 1000

            log_llm_call(
                model=settings.LLM_MODEL,
                latency_ms=llm_latency,
                success=True,
            )

            # ===== 7. 构建响应 =====
            sources = [
                {
                    "content": r["content"],
                    "score": r["score"],
                    "metadata": r.get("metadata", {}),
                }
                for r in fused_results[:top_k]
            ]

            latency_ms = (time.time() - start_time) * 1000
            log_rag_query(
                question=question,
                sources_count=len(sources),
                latency_ms=latency_ms,
                success=True,
            )

            return {
                "answer": llm_response.content,
                "sources": sources,
                "graph_entities": [
                    {"name": e.name, "type": e.type}
                    for e in graph_entities
                ],
                "latency_ms": round(latency_ms, 2),
            }

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            logger.error(f"RAG chat failed: {e}", exc_info=True)
            log_rag_query(
                question=question,
                sources_count=0,
                latency_ms=latency_ms,
                success=False,
            )
            raise RAGException(
                message=f"RAG query failed: {str(e)}",
                details={"question": question[:50]} if get_settings().DEBUG else {},
            )

    async def chat_with_cache(
        self,
        question: str,
        user_id: Optional[str] = None,
        top_k: Optional[int] = None,
    ) -> dict:
        """带缓存的 RAG 问答"""
        cache = get_cache()
        settings = get_settings()

        # 检查缓存
        if cache:
            cache_key = f"rag:chat:{hash(question)}"
            cached = cache.get(cache_key)
            if cached:
                logger.info(f"Cache hit: {question[:30]}...")
                return cached

        # 执行查询
        result = await self.chat(question, user_id, top_k)

        # 存入缓存
        if cache and settings.CACHE_ENABLED:
            cache_key = f"rag:chat:{hash(question)}"
            cache.set(cache_key, result, settings.REDIS_CACHE_TTL)

        return result


# ===== 导出 =====
from app.service.rag_service_base import RAGServiceBase

__all__ = ["RAGService", "RAGServiceBase"]