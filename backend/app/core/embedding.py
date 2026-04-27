"""
Embedding 模块
使用 BGE 模型生成文本向量
"""

import threading
from typing import List

from sentence_transformers import SentenceTransformer

from app.config import get_settings
from app.logging import get_logger


logger = get_logger(__name__)


class EmbeddingModel:
    """BGE Embedding 模型封装（单例）"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, model_name: str = None, device: str = None):
        # 避免重复初始化
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._initialized = True

        settings = get_settings()
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.device = device or settings.EMBEDDING_DEVICE

        logger.info(f"Loading Embedding model: {self.model_name}...")
        self.model = SentenceTransformer(self.model_name, device=self.device)
        logger.info(f"Embedding model loaded, device: {self.device}")

    def embed_query(self, query: str) -> List[float]:
        """
        将单个查询文本转换为向量

        Args:
            query: 查询文本

        Returns:
            List[float]: 向量
        """
        embedding = self.model.encode(query, normalize_embeddings=True)
        return embedding.tolist()

    def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """
        将多个文档文本转换为向量

        Args:
            documents: 文档列表

        Returns:
            List[List[float]]: 向量列表
        """
        embeddings = self.model.encode(documents, normalize_embeddings=True)
        return embeddings.tolist()

    def get_dimension(self) -> int:
        """获取向量维度"""
        return self.model.get_sentence_embedding_dimension()