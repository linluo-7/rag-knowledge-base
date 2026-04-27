"""
混合检索
BM25 (关键词) + 向量检索 (语义) 融合
"""

import threading
from typing import List, Optional

from app.config import get_settings
from app.logging import get_logger
from app.core.vector_store.base import SearchResult


logger = get_logger(__name__)


class BM25Scorer:
    """BM25 关键词检索器

    基于 TF-IDF 的关键词检索
    使用简单实现，生产环境可用 rank_bm25 库
    """

    def __init__(self):
        self._indexed = False

    def index(self, documents: List[dict]):
        """构建索引"""
        # 简单实现：分词 + 统计
        self.documents = documents
        self.doc_tokens = []

        import re
        for doc in documents:
            # 简单中文分词
            tokens = re.findall(r"[\w]+", doc["content"])
            self.doc_tokens.append(tokens)

        self._indexed = True
        logger.info(f"Indexed {len(documents)} documents")

    def score(self, query: str) -> List[float]:
        """计算 BM25 分数"""
        if not self._indexed:
            return []

        import re
        query_tokens = set(re.findall(r"[\w]+", query.lower()))

        scores = []
        for tokens in self.doc_tokens:
            # 简单 TF
            tf = sum(1 for t in tokens if t.lower() in query_tokens)
            # 简化 BM25
            score = tf / (len(tokens) + 1)
            scores.append(score)

        return scores


class HybridSearcher:
    """混合搜索器

    结合 BM25（关键词）和向量检索（语义）
    """

    def __init__(
        self,
        vector_store,
        alpha: float = 0.5,
    ):
        """
        Args:
            vector_store: 向量存储
            alpha: 向量权重 (1-alpha = BM25 权重)
        """
        self.vector_store = vector_store
        self.alpha = alpha  # 0.5 表示两者各占 50%
        self.bm25 = BM25Scorer()

    def search(
        self,
        query: str,
        query_vector: List[float],
        top_k: int = 5,
    ) -> List[SearchResult]:
        """混合检索

        1. 向量检索
        2. BM25 检索（可选）
        3. 分数融合
        """
        # 向量检索
        vector_results = self.vector_store.search(query_vector, top_k=top_k * 2)

        if not vector_results:
            return []

        # 构建分数映射
        vector_scores = {
            r.content: r.score for r in vector_results
        }

        # BM25 分数（如果已建索引）
        bm25_scores = {}
        if self.bm25._indexed:
            bm25_raw = self.bm25.score(query)
            if bm25_raw:
                # 归一化
                max_score = max(bm25_raw) if max(bm25_raw) > 0 else 1
                bm25_scores = {
                    self.bm25.documents[i]["content"]: s / max_score
                    for i, s in enumerate(bm25_raw)
                }

        # 融合分数
        fused = []
        for result in vector_results:
            vector_score = result.score
            bm25_score = bm25_scores.get(result.content, 0)

            # 加权融合
            final_score = (
                self.alpha * vector_score +
                (1 - self.alpha) * bm25_score
            )

            fused.append({
                "content": result.content,
                "score": final_score,
                "metadata": result.metadata,
                "sources": {
                    "vector": vector_score,
                    "bm25": bm25_score,
                }
            })

        # 按融合分数排序
        fused.sort(key=lambda x: x["score"], reverse=True)

        return fused[:top_k]

    def set_index(self, documents: List[dict]):
        """设置 BM25 索引"""
        self.bm25.index(documents)