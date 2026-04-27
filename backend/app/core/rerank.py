"""
两阶段检索 - Reranking
第一阶段：向量检索（粗排，top_k * 10）
第二阶段：Cross-Encoder（精排，返回 top_k）
"""

import threading
from typing import List, Optional

from sentence_transformers import CrossEncoder

from app.config import get_settings
from app.logging import get_logger
from app.core.vector_store.base import SearchResult


logger = get_logger(__name__)


class Reranker:
    """Cross-Encoder Reranker

    比密集向量检索更精确的相关性计算
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, model_name: str = None):
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._initialized = True

        # 默认模型
        model_name = model_name or "BAAI/bge-reranker-base"

        logger.info(f"Loading reranker model: {model_name}...")
        try:
            self.model = CrossEncoder(model_name, max_length=512)
            logger.info("Reranker loaded")
        except Exception as e:
            logger.warning(f"Reranker not available: {e}")
            self.model = None

    def rerank(
        self,
        query: str,
        candidates: List[SearchResult],
        top_k: int = 5,
    ) -> List[SearchResult]:
        """重排序

        Args:
            query: 查询文本
            candidates: 候选结果（来自向量检索）
            top_k: 返回数量

        Returns:
            重排序后的结果
        """
        if not self.model or not candidates:
            return candidates[:top_k]

        # 构建查询-文档对
        pairs = [(query, doc.content) for doc in candidates]

        # 批量计算分数
        try:
            scores = self.model.predict(pairs)

            # 按分数排序
            scored_docs = [
                (doc, score) for doc, score in zip(candidates, scores)
            ]
            scored_docs.sort(key=lambda x: x[1], reverse=True)

            # 返回 top_k
            results = []
            for doc, score in scored_docs[:top_k]:
                doc.score = float(score)
                results.append(doc)

            return results

        except Exception as e:
            logger.warning(f"Reranking failed: {e}")
            return candidates[:top_k]

    def compute_score(self, query: str, document: str) -> float:
        """计算单个查询-文档对的相关性分数"""
        if not self.model:
            return 0.0

        try:
            score = self.model.predict([(query, document)])
            return float(score[0])
        except Exception:
            return 0.0


class TwoStageRetriever:
    """两阶段检索器

    阶段1：向量检索 (Milvus) -> 粗排
    阶段2：Reranking -> 精排
    """

    def __init__(self, vector_store, reranker: Optional[Reranker] = None):
        self.vector_store = vector_store
        self.reranker = reranker or Reranker()

    def search(
        self,
        query_vector: List[float],
        query: str,
        coarse_k: int = 50,
        top_k: int = 5,
    ) -> List[SearchResult]:
        """两阶段检索

        Args:
            query_vector: 查询向量
            query: 原始查询文本
            coarse_k: 粗排数量（向量检索返回）
            top_k: 精排数量（最终返回）
        """
        # 阶段1：向量检索（粗排）
        coarse_results = self.vector_store.search(query_vector, top_k=coarse_k)

        if not coarse_results:
            return []

        # 阶段2：Reranking（精排）
        final_results = self.reranker.rerank(query, coarse_results, top_k=top_k)

        return final_results

    async def search_async(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """异步两阶段检索"""
        from app.factory import get_embedding_model, get_vector_store

        # 1. 向量化
        embedding_model = get_embedding_model()
        query_vector = embedding_model.embed_query(query)

        # 2. 粗排
        coarse_k = top_k * 10  # 扩大 10 倍
        coarse_results = self.vector_store.search(query_vector, top_k=coarse_k)

        if not coarse_results:
            return []

        # 3. 精排
        final_results = self.reranker.rerank(query, coarse_results, top_k=top_k)

        return final_results