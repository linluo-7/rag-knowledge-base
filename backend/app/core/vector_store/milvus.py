"""
Milvus 向量存储实现
"""

import threading
from typing import Any, Dict, List, Optional
from contextlib import contextmanager

from pymilvus import (
    connections,
    Collection,
    FieldSchema,
    CollectionSchema,
    DataType,
    utility,
)

from app.config import get_settings
from app.logging import get_logger
from app.exceptions import VectorStoreError, VectorStoreConnectionError
from app.core.vector_store.base import VectorStore as BaseVectorStore
from app.core.vector_store.base import SearchResult, VectorDocument


logger = get_logger(__name__)


class MilvusVectorStore(BaseVectorStore):
    """Milvus 向量数据库实现"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, host: str = None, port: int = None):
        # 避免重复初始化
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._initialized = True

        settings = get_settings()
        self.host = host or settings.MILVUS_HOST
        self.port = port or settings.MILVUS_PORT
        self.collection_name = settings.MILVUS_COLLECTION
        self.dim = settings.MILVUS_DIM

        self._connection_name = "default"
        self._collection: Optional[Collection] = None
        self._connect()

    def _connect(self) -> None:
        """建立与 Milvus 的连接"""
        try:
            connections.connect(
                alias=self._connection_name,
                host=self.host,
                port=self.port,
            )
            logger.info(f"Milvus connected: {self.host}:{self.port}")
        except Exception as e:
            logger.error(f"Milvus connection failed: {e}")
            raise VectorStoreConnectionError(
                details={"host": self.host, "port": self.port, "error": str(e)}
            )

    def check_connection(self) -> bool:
        """检查 Milvus 连接状态"""
        try:
            connections.connect(
                alias=f"{self._connection_name}_check",
                host=self.host,
                port=self.port,
            )
            connections.disconnect(f"{self._connection_name}_check")
            return True
        except Exception:
            return False

    def init_collection(self, force: bool = False) -> None:
        """初始化 Collection"""
        if utility.has_collection(self.collection_name):
            if force:
                utility.drop_collection(self.collection_name)
                logger.warning(f"Dropped collection: {self.collection_name}")
            else:
                self._collection = Collection(self.collection_name)
                self._collection.load()
                logger.info(f"Collection already exists: {self.collection_name}")
                return

        # 创建 Schema
        fields = [
            FieldSchema(
                name="id",
                dtype=DataType.INT64,
                is_primary=True,
                auto_id=True,
            ),
            FieldSchema(
                name="content",
                dtype=DataType.VARCHAR,
                max_length=65535,
            ),
            FieldSchema(
                name="vector",
                dtype=DataType.FLOAT_VECTOR,
                dim=self.dim,
            ),
            FieldSchema(
                name="metadata",
                dtype=DataType.JSON,
            ),
        ]

        schema = CollectionSchema(
            fields=fields,
            description="RAG 知识库文档向量存储",
        )

        self._collection = Collection(
            name=self.collection_name,
            schema=schema,
        )

        # 创建索引
        index_params = {
            "index_type": "IVF_FLAT",
            "metric_type": "COSINE",
            "params": {"nlist": 128},
        }

        self._collection.create_index(
            field_name="vector",
            index_params=index_params,
        )

        self._collection.load()
        logger.info(f"Collection created: {self.collection_name}")

    def insert(self, documents: List[VectorDocument]) -> None:
        """插入文档"""
        if not self._collection:
            self.init_collection()

        contents = [doc.content for doc in documents]
        vectors = [doc.vector for doc in documents]
        metadata = [
            doc.metadata or {} for _ in documents
        ]

        self._collection.insert({
            "content": contents,
            "vector": vectors,
            "metadata": metadata,
        })

        self._collection.flush()
        logger.info(f"Inserted {len(documents)} documents")

    def search(
        self, query_vector: List[float], top_k: int = 5
    ) -> List[SearchResult]:
        """向量相似度检索"""
        if not self._collection:
            self.init_collection()

        search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 10},
        }

        results = self._collection.search(
            data=[query_vector],
            anns_field="vector",
            param=search_params,
            limit=top_k,
            output_fields=["content", "metadata"],
        )

        formatted_results = []
        for hits in results:
            for hit in hits:
                formatted_results.append(SearchResult(
                    content=hit.entity.get("content"),
                    score=hit.score,
                    metadata=hit.entity.get("metadata", {}),
                ))

        return formatted_results

    def search_by_text(self, text: str, top_k: int = 5) -> List[SearchResult]:
        """文本检索（自动向量化）"""
        from app.core.embedding import EmbeddingModel
        from app.factory import get_embedding_model

        embedding_model = get_embedding_model()
        query_vector = embedding_model.embed_query(text)

        return self.search(query_vector, top_k)

    def get_all(self, limit: int = 1000) -> List[VectorDocument]:
        """获取所有文档"""
        if not self._collection:
            self.init_collection()

        results = self._collection.query(
            expr="id >= 0",
            output_fields=["content", "metadata"],
            limit=limit,
        )

        return [
            VectorDocument(
                content=r["content"],
                vector=[],  # 不返回向量以节省内存
                metadata=r.get("metadata"),
            )
            for r in results
        ]

    def delete_by_file_id(self, file_id: str) -> None:
        """根据 file_id 删除数据"""
        if not self._collection:
            self.init_collection()

        self._collection.delete(f'metadata["file_id"] == "{file_id}"')
        self._collection.flush()
        logger.info(f"Deleted documents with file_id: {file_id}")

    def close(self) -> None:
        """关闭��接"""
        try:
            connections.disconnect(self._connection_name)
            logger.info("Milvus connection closed")
        except Exception as e:
            logger.warning(f"Failed to close Milvus connection: {e}")