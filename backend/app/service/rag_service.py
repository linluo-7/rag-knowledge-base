"""
RAG 服务层
封装 RAG 问答的核心业务逻辑
"""

import time
import asyncio
from typing import List, Optional

from app.config import get_settings
from app.logging import get_logger, log_rag_query, log_llm_call
from app.exceptions import RAGException, VectorStoreError, GraphStoreError
from app.service.rag_service_base import RAGServiceBase


logger = get_logger(__name__)


class RAGService(RAGServiceBase):
    """RAG 服务实现"""

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
        """
        RAG 问答流程

        步骤：
        1. 问题向量化
        2. Milvus 向量检索
        3. Neo4j 图谱扩展
        4. RRF 融合
        5. LLM 生成答案
        """
        start_time = time.time()
        top_k = top_k or self.top_k

        try:
            # ===== 1. 并行执行向量检索和图谱检索 =====
            vector_store = self._get_vector_store()
            graph_store = self._get_graph_store()
            embedding_model = self._get_embedding_model()

            # 向量化
            query_vector = embedding_model.embed_query(question)

            # 并行检索
            milvus_task = asyncio.create_task(
                self._async_search_vector(vector_store, query_vector, top_k)
            )
            graph_task = asyncio.create_task(
                self._async_expand_graph(graph_store, question)
            )

            milvus_results, graph_entities = await asyncio.gather(
                milvus_task, graph_task
            )

            # ===== 2. 图谱扩展检索 =====
            neo4j_results = []
            if graph_entities:
                neo4j_task = asyncio.create_task(
                    self._async_search_by_entities(vector_store, graph_entities, top_k=2)
                )
                neo4j_results = await neo4j_task

            # ===== 3. RRF 融合 =====
            fusion = self._get_fusion()
            fused_results = fusion.fuse(
                milvus_results, neo4j_results, k=self.rrf_k
            )

            # ===== 4. 构建上下文 =====
            context = "\n\n".join([
                r["content"]
                for r in fused_results[: self.max_context_k]
            ])

            # ===== 5. LLM 生成 =====
            llm = self._get_llm()
            llm_start = time.time()
            llm_response = llm.generate(question, context)
            llm_latency = (time.time() - llm_start) * 1000

            log_llm_call(
                model=settings.LLM_MODEL,
                latency_ms=llm_latency,
                success=True,
            )

            # ===== 6. 构建响应 =====
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
            logger.error(f"RAG chat failed: {e}")
            log_rag_query(
                question=question,
                sources_count=0,
                latency_ms=latency_ms,
                success=False,
            )
            raise RAGException(message=f"RAG query failed: {e}")

    async def _async_search_vector(self, store, query_vector, top_k):
        """异步向量检索"""
        return store.search(query_vector, top_k)

    async def _async_expand_graph(self, store, query):
        """异步图谱扩展"""
        return store.expand_entities(query)

    async def _async_search_by_entities(self, store, entities, top_k):
        """异步实体检索"""
        results = []
        for entity in entities[:5]:
            task = asyncio.create_task(
                self._async_search_vector(store, entity.name, top_k)
            )
            result = await task
            results.extend(result)
        return results

    def _get_vector_store(self):
        from app.factory import get_vector_store

        return get_vector_store()

    def _get_graph_store(self):
        from app.factory import get_graph_store

        return get_graph_store()

    def _get_embedding_model(self):
        from app.factory import get_embedding_model

        return get_embedding_model()

    def _get_fusion(self):
        from app.factory import get_fusion

        return get_fusion()

    def _get_llm(self):
        from app.factory import get_llm

        return get_llm()


# 抽象基类（保持向后兼容）
from app.service.rag_service_base import RAGServiceBase