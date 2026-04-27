"""
FastAPI 依赖注入提供者
使用 Depends 实现真正的依赖注入
"""

from typing import AsyncGenerator, Generator, Optional

from fastapi import Depends

from app.config import get_settings
from app.logging import get_logger
from app.core.vector_store import MilvusVectorStore
from app.core.graph_store import Neo4jGraphStore
from app.core.embedding import EmbeddingModel
from app.core.chunker import TextChunker
from app.core.fusion import RRFFusion
from app.core.llm import MiniMaxLLM
from app.core.cache import RedisCache


logger = get_logger(__name__)


# ===== 基础依赖 =====


def get_settings_dep():
    """配置依赖"""
    return get_settings()


# ===== 存储依赖 =====


_vector_store: Optional[MilvusVectorStore] = None
_graph_store: Optional[Neo4jGraphStore] = None
_embedding: Optional[EmbeddingModel] = None


def get_vector_store() -> MilvusVectorStore:
    """向量存储依赖 - 请求级单例"""
    global _vector_store
    if _vector_store is None:
        _vector_store = MilvusVectorStore()
    return _vector_store


def get_graph_store() -> Neo4jGraphStore:
    """图存储依赖 - 请求级单例"""
    global _graph_store
    if _graph_store is None:
        _graph_store = Neo4jGraphStore()
    return _graph_store


def get_embedding_model() -> EmbeddingModel:
    """Embedding 模型依赖 - 应用级单例"""
    global _embedding
    if _embedding is None:
        _embedding = EmbeddingModel()
    return _embedding


def get_chunker() -> TextChunker:
    """文本分块依赖"""
    return TextChunker()


def get_fusion() -> RRFFusion:
    """RRF 融合依赖"""
    return RRFFusion()


def get_llm() -> MiniMaxLLM:
    """LLM 依赖"""
    return MiniMaxLLM()


def get_cache() -> Optional[RedisCache]:
    """缓存依赖"""
    settings = get_settings()
    if not settings.CACHE_ENABLED:
        return None
    return RedisCache()


# ===== 依赖标记类 =====


class VectorStoreDep:
    """向量存储依赖标记"""

    def __init__(self, store: MilvusVectorStore = Depends(get_vector_store)):
        self.store = store


class GraphStoreDep:
    """图存储依赖标记"""

    def __init__(self, store: Neo4jGraphStore = Depends(get_graph_store)):
        self.store = store


class EmbeddingDep:
    """Embedding 依赖标记"""

    def __init__(self, model: EmbeddingModel = Depends(get_embedding_model)):
        self.model = model


class LLMDep:
    """LLM 依赖标记"""

    def __init__(self, llm: MiniMaxLLM = Depends(get_llm)):
        self.llm = llm


class CacheDep:
    """缓存依赖标记"""

    def __init__(self, cache: RedisCache = Depends(get_cache)):
        self.cache = cache


# ===== 便捷类型 =====


VectorStore = Depends(get_vector_store)
GraphStore = Depends(get_graph_store)
EmbeddingModel = Depends(get_embedding_model)
TextChunker = Depends(get_chunker)
RRFFusion = Depends(get_fusion)
LLM = Depends(get_llm)
Cache = Depends(get_cache)