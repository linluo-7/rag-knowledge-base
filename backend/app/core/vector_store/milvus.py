"""
Milvus 向量存储实现 - 生产级版本 v2
长连接复用 + 正确的连接池管理
"""

import asyncio
import threading
from contextlib import asynccontextmanager, contextmanager
from typing import Any, Dict, List, Optional

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
from app.core.vector_store.base import VectorStore as BaseVectorStore
from app.core.vector_store.base import SearchResult, VectorDocument


logger = get_logger(__name__)


class MilvusConnection:
    """Milvus 长连接 - 保持连接不释放

    特性：
    - 复用连接，不反复创建/销毁
    - 线程安全
    - 健康检查，断线重连
    """

    def __init__(self, host: str, port: int, alias: str = "default"):
        self.host = host
        self.port = port
        self.alias = alias
        self._lock = threading.Lock()
        self._closed = False
        self._healthy = False

    def connect(self) -> None:
        """建立连接"""
        with self._lock:
            if self._closed:
                raise RuntimeError("Connection closed")

            try:
                # 检查是否已连接
                connections.connect(
                    alias=self.alias,
                    host=self.host,
                    port=self.port,
                )
                self._healthy = True
                logger.info(f"Milvus connected: {self.alias} -> {self.host}:{self.port}")
            except Exception as e:
                logger.warning(f"Milvus connect failed: {e}")
                self._healthy = False
                raise VectorStoreConnectionError(
                    details={"host": self.host, "port": self.port, "error": str(e)}
                )

    def is_healthy(self) -> bool:
        """检查连接健康"""
        try:
            # 简单查询验证连接
            utility.has_collection("_health_check")
            return True
        except Exception:
            self._healthy = False
            return False

    def ensure_healthy(self) -> None:
        """确保连接健康，必要时重连"""
        if not self._healthy or not self.is_healthy():
            logger.warning("Milvus connection unhealthy, reconnecting...")
            self.connect()

    def close(self) -> None:
        """关闭连接"""
        with self._lock:
            if not self._closed:
                try:
                    connections.disconnect(self.alias)
                except Exception:
                    pass
                self._closed = True
                self._healthy = False


class MilvusConnectionPool:
    """Milvus 连接池 - 管理多个长连接

    和传统连接池不同：
    - 这里是管理多个 Milvus Connection 对象
    - 每个 Connection 保持长连接
    - 实际场景 Milvus 一组连接够用，这里简化管理
    """

    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self._connections: Dict[str, MilvusConnection] = {}
        self._lock = threading.Lock()
        self._current = 0

    @classmethod
    def get_instance(cls) -> "MilvusConnectionPool":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def get_connection(self, host: str = None, port: int = None) -> MilvusConnection:
        """获取连接（复用一个）"""
        settings = get_settings()
        host = host or settings.MILVUS_HOST
        port = port or settings.MILVUS_PORT
        key = f"{host}:{port}"

        with self._lock:
            if key not in self._connections:
                conn = MilvusConnection(host, port, alias=f"rag_{key}")
                conn.connect()
                self._connections[key] = conn
                logger.info(f"Created Milvus connection: {key}")
            else:
                conn = self._connections[key]
                conn.ensure_healthy()

            return conn

    def close_all(self) -> None:
        """关闭所有连接"""
        with self._lock:
            for conn in self._connections.values():
                conn.close()
            self._connections.clear()
            logger.info("All Milvus connections closed")


@contextmanager
def use_milvus():
    """获取 Milvus 连接（推荐用法）

    用法：
        with use_milvus() as conn:
            collection = Collection("documents", using=conn.alias)
    """
    pool = MilvusConnectionPool.get_instance()
    conn = pool.get_connection()
    try:
        yield conn
    except Exception:
        conn.ensure_healthy()
        raise


class MilvusVectorStore(BaseVectorStore):
    """Milvus 向量数据库 - 生产级 v2

    改进：
    - 长连接复用
    - 连接池统一管理
    - 健康检查 + 自动重连
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

        self._pool = MilvusConnectionPool.get_instance()

    def check_connection(self) -> bool:
        """检查连接"""
        try:
            conn = self._pool.get_connection()
            return conn.is_healthy()
        except Exception:
            return False

    def init_collection(self, force: bool = False) -> None:
        """初始化 Collection"""
        conn = self._pool.get_connection()

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
        """插入"""
        if not self._collection:
            self.init_collection()

        conn = self._pool.get_connection()
        collection = Collection(self.collection_name, using=conn.alias)

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

    def search(self, query_vector: List[float], top_k: int = 5) -> List[SearchResult]:
        """检索"""
        if not self._collection:
            self.init_collection()

        conn = self._pool.get_connection()
        conn.ensure_healthy()  # 确保连接健康

        collection = Collection(self.collection_name, using=conn.alias)
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

    def search_by_text(self, text: str, top_k: int = 5) -> List[SearchResult]:
        """文本检索"""
        from app.factory import get_embedding_model
        model = get_embedding_model()
        query_vector = model.embed_query(text)
        return self.search(query_vector, top_k)

    def get_all(self, limit: int = 1000) -> List[VectorDocument]:
        """获取所有"""
        if not self._collection:
            self.init_collection()

        conn = self._pool.get_connection()
        collection = Collection(self.collection_name, using=conn.alias)

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
        """删除"""
        if not self._collection:
            self.init_collection()

        conn = self._pool.get_connection()
        collection = Collection(self.collection_name, using=conn.alias)

        collection.delete(f'metadata["file_id"] == "{file_id}"')
        collection.flush()
        logger.info(f"Deleted file_id: {file_id}")

    def close(self) -> None:
        """关闭（池由应用退出时统一关闭）"""
        pass