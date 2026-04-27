"""
依赖注入工厂
单例模式管理所有服务实例
"""

import threading
from functools import lru_cache
from typing import Optional

from app.config import get_settings


class Factory:
    """依赖注入工厂"""

    _lock = threading.Lock()
    _instances: dict = {}

    @classmethod
    def get_vector_store(cls) -> "VectorStore":
        """获取向量存储实例"""
        from app.core.vector_store import MilvusVectorStore

        return cls._get_instance(MilvusVectorStore, "vector_store")

    @classmethod
    def get_graph_store(cls) -> "GraphStore":
        """获取图存储实例"""
        from app.core.graph_store import Neo4jGraphStore

        return cls._get_instance(Neo4jGraphStore, "graph_store")

    @classmethod
    def get_llm(cls) -> "LLM":
        """获取 LLM 实例"""
        from app.core.llm import MiniMaxLLM

        return cls._get_instance(MiniMaxLLM, "llm")

    @classmethod
    def get_embedding_model(cls) -> "EmbeddingModel":
        """获取 Embedding 模型实例"""
        from app.core.embedding import EmbeddingModel

        return cls._get_instance(EmbeddingModel, "embedding")

    @classmethod
    def get_fusion(cls) -> "RRFFusion":
        """获取 RRF 融合实例"""
        from app.core.fusion import RRFFusion

        return cls._get_instance(RRFFusion, "fusion")

    @classmethod
    def get_document_parser(cls) -> "DocumentParser":
        """获取文档解析器实例"""
        from app.core.document import DocumentParser

        return cls._get_instance(DocumentParser, "document_parser")

    @classmethod
    def get_chunker(cls) -> "TextChunker":
        """获取文本分块器实例"""
        from app.core.chunker import TextChunker

        return cls._get_instance(TextChunker, "chunker")

    @classmethod
    def get_cache(cls) -> Optional["Cache"]:
        """获取缓存实例"""
        settings = get_settings()
        if not settings.CACHE_ENABLED:
            return None

        from app.core.cache import RedisCache

        return cls._get_instance(RedisCache, "cache")

    @classmethod
    def get_rag_service(cls) -> "RAGService":
        """获取 RAG 服务实例"""
        from app.service.rag_service import RAGService

        return cls._get_instance(RAGService, "rag_service")

    @classmethod
    def get_document_service(cls) -> "DocumentService":
        """获取文档服务实例"""
        from app.service.document_service import DocumentService

        return cls._get_instance(DocumentService, "document_service")

    @classmethod
    def _get_instance(cls, instance_class, name: str):
        """获取或创建实例（线程安全）"""
        if name not in cls._instances:
            with cls._lock:
                if name not in cls._instances:
                    cls._instances[name] = instance_class()
        return cls._instances[name]

    @classmethod
    def reset_all(cls):
        """重置所有实例（测试用）"""
        with cls._lock:
            for instance in cls._instances.values():
                if hasattr(instance, "close"):
                    instance.close()
            cls._instances.clear()


@lru_cache()
def get_vector_store() -> "VectorStore":
    """获取向量存储（兼容旧代码）"""
    return Factory.get_vector_store()


@lru_cache()
def get_graph_store() -> "GraphStore":
    """获取图存储（兼容旧代码）"""
    return Factory.get_graph_store()


@lru_cache()
def get_llm() -> "LLM":
    """获取 LLM（兼容旧代码）"""
    return Factory.get_llm()


@lru_cache()
def get_embedding_model() -> "EmbeddingModel":
    """获取 Embedding 模型（兼容旧代码）"""
    return Factory.get_embedding_model()


@lru_cache()
def get_fusion() -> "RRFFusion":
    """获取 RRF 融合（兼容旧代码）"""
    return Factory.get_fusion()