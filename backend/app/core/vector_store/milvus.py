"""
Milvus 向量存储实现 - 生产级版本
"""

import asyncio
import threading
from contextlib import asynccontextmanager, contextmanager
from typing import Any, Dict, List, Optional

import aiohttp
from pymilvus import (
    connections,
    Collection,
    FieldSchema,
    CollectionSchema,
    DataType,
    utility,
)

from app.config import get_settings
from app.exceptions import VectorStoreConnectionError, VectorStoreError
from app.logging import get_logger
from app.core.pool import PooledConnection
from app.core.vector_store.base import VectorStore as BaseVectorStore
from app.core.vector_store.base import SearchResult, VectorDocument


logger = get_logger(__name__)


class MilvusConnectionPool:
    """Milvus 连接池"""

    _pools: Dict[str, "MilvusConnectionPool"] = {}
    _lock = threading.Lock()

    def __init__(self, host: str, port: int, pool_size: int = 5):
        self.host = host
        self.port = port
        self.pool_size = pool_size
        self._available: List[str] = []
        self._in_use: set = set()
        self._lock = threading.Lock()

    def get_connection(self) -> str:
        """获取连接"""
        with self._lock:
            if self._available:
                alias = self._available.pop()
                self._in_use.add(alias)
                return alias

            # 创建新连接
            alias = f"milvus_{threading.current_thread().ident}_{len(self._in_use)}"
            connections.connect(alias=alias, host=self.host, port=self.port)
            self._in_use.add(alias)
            return alias

    def release_connection(self, alias: str) -> None:
        """释放连接"""
        with self._lock:
            if alias in self._in_use:
                self._in_use.remove(alias)
                if len(self._available) < self.pool_size:
                    self._available.append(alias)
                else:
                    try:
                        connections.disconnect(alias)
                    except Exception:
                        pass

    @classmethod
    def get_pool(cls, host: str, port: int, pool_size: int = 5) -> "MilvusConnectionPool":
        """获取连接池单例"""
        key = f"{host}:{port}"
        with cls._lock:
            if key not in cls._pools:
                cls._pools[key] = cls(host, port, pool_size)
            return cls._pools[key]

    @classmethod
    def close_all(cls) -> None:
        """关闭所有连接"""
        with cls._lock:
            for pool in cls._pools.values():
                pool.close()
            cls._pools.clear()

    def close(self) -> None:
        """关闭连接池"""
        with self._lock:
            for alias in list(self._available) + list(self._in_use):
                try:
                    connections.disconnect(alias)
                except Exception:
                    pass
            self._available.clear()
            self._in_use.clear()


@contextmanager
def use_milvus_connection(host: str = None, port: int = None):
    """同步使用 Milvus 连接"""
    settings = get_settings()
    host = host or settings.MILVUS_HOST
    port = port or settings.MILVUS_PORT
    pool_size = settings.MILVUS_POOL_SIZE

    pool = MilvusConnectionPool.get_pool(host, port, pool_size)
    alias = pool.get_connection()
    try:
        yield alias
    finally:
        pool.release_connection(alias)


class MilvusVectorStore(BaseVectorStore):
    """Milvus 向量数据库实现 - 生产级

    特性���
    - 连接池管理
    - 线程安全
    - 异步支持
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, host: str = None, port: int = None):
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._initialized = True

        settings = get_settings()
        self.host = host or settings.MILVUS_HOST
        self.port = port or settings.MILVUS_PORT
        self.collection_name = settings.MILVUS_COLLECTION
        self.dim = settings.MILVUS_DIM
        self.pool_size = settings.MILVUS_POOL_SIZE

        self._pool: Optional[MilvusConnectionPool] = None
        self._connect()

    def _connect(self) -> None:
        """建立连接"""
        try:
            self._pool = MilvusConnectionPool.get_pool(
                self.host, self.port, self.pool_size
            )
            # 测试连接
            with use_milvus_connection(self.host, self.port) as alias:
                pass
            logger.info(f"Milvus connection pool: {self.host}:{self.port} (size={self.pool_size})")
        except Exception as e:
            logger.error(f"Milvus connection failed: {e}")
            raise VectorStoreConnectionError(
                details={"host": self.host, "port": self.port, "error": str(e)}
            )

    def check_connection(self) -> bool:
        """检查连接状态"""
        try:
            with use_milvus_connection(self.host, self.port) as alias:
                connections.connect(alias=f"check_{id(self)}", host=self.host, port=self.port)
                connections.disconnect(f"check_{id(self)}")
            return True
        except Exception:
            return False

    def init_collection(self, force: bool = False) -> None:
        """初始化 Collection"""
        with use_milvus_connection(self.host, self.port) as alias:
            if utility.has_collection(self.collection_name):
                if force:
                    utility.drop_collection(self.collection_name)
                    logger.warning(f"Dropped collection: {self.collection_name}")
                else:
                    self._collection = Collection(self.collection_name)
                    self._collection.load()
                    logger.info(f"Collection exists: {self.collection_name}")
                    return

            fields = [
                FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
                FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
                FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=self.dim),
                FieldSchema(name="metadata", dtype=DataType.JSON),
            ]

            schema = CollectionSchema(fields=fields, description="RAG 文档向量存储")
            self._collection = Collection(name=self.collection_name, schema=schema)

            index_params = {
                "index_type": "IVF_FLAT",
                "metric_type": "COSINE",
                "params": {"nlist": 128},
            }

            self._collection.create_index(field_name="vector", index_params=index_params)
            self._collection.load()
            logger.info(f"Collection created: {self.collection_name}")

    def insert(self, documents: List[VectorDocument]) -> None:
        """插入文档"""
        if not self._collection:
            self.init_collection()

        with use_milvus_connection(self.host, self.port) as alias:
            collection = Collection(self.collection_name)
            contents = [doc.content for doc in documents]
            vectors = [doc.vector for doc in documents]
            metadata = [doc.metadata or {} for _ in documents]

            collection.insert({
                "content": contents,
                "vector": vectors,
                "metadata": metadata,
            })
            collection.flush()
            logger.info(f"Inserted {len(documents)} documents")

    def search(
        self, query_vector: List[float], top_k: int = 5
    ) -> List[SearchResult]:
        """向量检索"""
        if not self._collection:
            self.init_collection()

        with use_milvus_connection(self.host, self.port) as alias:
            collection = Collection(self.collection_name)
            search_params = {
                "metric_type": "COSINE",
                "params": {"nprobe": 10},
            }

            results = collection.search(
                data=[query_vector],
                anns_field="vector",
                param=search_params,
                limit=top_k,
                output_fields=["content", "metadata"],
            )

            formatted = []
            for hits in results:
                for hit in hits:
                    formatted.append(SearchResult(
                        content=hit.entity.get("content"),
                        score=hit.score,
                        metadata=hit.entity.get("metadata", {}),
                    ))
            return formatted

    async def search_async(
        self, query_vector: List[float], top_k: int = 5
    ) -> List[SearchResult]:
        """异步向量检索 - 实际调用"""
        # Milvus Python SDK 本身是同步的，我们用 run_in_executor 包装
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.search, query_vector, top_k
        )

    def search_by_text(self, text: str, top_k: int = 5) -> List[SearchResult]:
        """文本检索"""
        from app.factory import get_embedding_model
        model = get_embedding_model()
        query_vector = model.embed_query(text)
        return self.search(query_vector, top_k)

    def get_all(self, limit: int = 1000) -> List[VectorDocument]:
        """获取所有文档"""
        if not self._collection:
            self.init_collection()

        with use_milvus_connection(self.host, self.port) as alias:
            collection = Collection(self.collection_name)
            results = collection.query(
                expr="id >= 0",
                output_fields=["content", "metadata"],
                limit=limit,
            )
            return [
                VectorDocument(
                    content=r["content"],
                    vector=[],
                    metadata=r.get("metadata"),
                )
                for r in results
            ]

    def delete_by_file_id(self, file_id: str) -> None:
        """删除数据"""
        if not self._collection:
            self.init_collection()

        with use_milvus_connection(self.host, self.port) as alias:
            collection = Collection(self.collection_name)
            collection.delete(f'metadata["file_id"] == "{file_id}"')
            collection.flush()
            logger.info(f"Deleted file_id: {file_id}")

    def close(self) -> None:
        """关闭连接"""
        if self._pool:
            self._pool.close()
            logger.info("Milvus pool closed")