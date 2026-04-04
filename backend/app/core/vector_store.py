"""
向量存储模块
与 Milvus 交互，实现向量的插入和检索
"""

from typing import List, Dict, Any, Optional
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, utility
from app.config import MILVUS_HOST, MILVUS_PORT, MILVUS_COLLECTION, MILVUS_DIM


class MilvusStore:
    """
    Milvus 向量数据库封装
    
    提供以下功能：
    - 初始化 Collection
    - 插入向量
    - 相似度检索
    """
    
    def __init__(self, host: str = MILVUS_HOST, port: int = MILVUS_PORT):
        self.host = host
        self.port = port
        self.collection_name = MILVUS_COLLECTION
        self.dim = MILVUS_DIM
        self.collection: Optional[Collection] = None
        self._connect()
    
    def _connect(self):
        """建立与 Milvus 的连接"""
        connections.connect(
            alias="default",
            host=self.host,
            port=self.port
        )
        print(f"✅ Milvus 连接成功: {self.host}:{self.port}")
    
    def check_connection(self):
        """检查 Milvus 连接状态"""
        connections.connect(
            alias="check",
            host=self.host,
            port=self.port
        )
        connections.disconnect("check")
    
    def init_collection(self, force: bool = False):
        """
        初始化 Collection
        
        Schema:
        - id: int64, 主键，自增
        - content: varchar, 文本内容
        - vector: float_vector, 向量
        - metadata: json, 元数据
        """
        if utility.has_collection(self.collection_name):
            if force:
                utility.drop_collection(self.collection_name)
                print(f"⚠️ 已删除旧 Collection: {self.collection_name}")
            else:
                self.collection = Collection(self.collection_name)
                self.collection.load()
                print(f"✅ Collection 已存在: {self.collection_name}")
                return
        
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=65535),
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=self.dim),
            FieldSchema(name="metadata", dtype=DataType.JSON),
        ]
        
        schema = CollectionSchema(
            fields=fields,
            description="RAG 知识库文档向量存储"
        )
        
        self.collection = Collection(name=self.collection_name, schema=schema)
        
        index_params = {
            "index_type": "IVF_FLAT",
            "metric_type": "COSINE",
            "params": {"nlist": 128}
        }
        
        self.collection.create_index(
            field_name="vector",
            index_params=index_params
        )
        
        self.collection.load()
        print(f"✅ Collection 创建成功: {self.collection_name}")
    
    def insert(self, documents: List[Dict[str, Any]], vectors: List[List[float]], metadata: Dict[str, Any] = None):
        """
        插入文档和向量
        """
        if not self.collection:
            self.init_collection()
        
        contents = [doc["content"] for doc in documents]
        metadatas = [metadata or {} for _ in documents]
        
        self.collection.insert({
            "content": contents,
            "vector": vectors,
            "metadata": metadatas
        })
        
        self.collection.flush()
        print(f"✅ 插入 {len(documents)} 条数据到 Milvus")
    
    def search(self, query_vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        向量相似度检索
        """
        if not self.collection:
            self.init_collection()
        
        search_params = {
            "metric_type": "COSINE",
            "params": {"nprobe": 10}
        }
        
        results = self.collection.search(
            data=[query_vector],
            anns_field="vector",
            param=search_params,
            limit=top_k,
            output_fields=["content", "metadata"]
        )
        
        formatted_results = []
        for hits in results:
            for hit in hits:
                formatted_results.append({
                    "content": hit.entity.get("content"),
                    "score": hit.score,
                    "metadata": hit.entity.get("metadata", {})
                })
        
        return formatted_results
    
    def search_by_entity(self, entity_name: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        通过实体名称检索相关文档
        """
        from app.core.embedding import EmbeddingModel
        
        embedding_model = EmbeddingModel()
        entity_vector = embedding_model.embed_query(entity_name)
        
        return self.search(entity_vector, top_k)
    
    def get_all(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """获取所有数据"""
        if not self.collection:
            self.init_collection()
        
        results = self.collection.query(
            expr="id >= 0",
            output_fields=["id", "content", "metadata"],
            limit=limit
        )
        
        return results
    
    def delete_by_file_id(self, file_id: str):
        """根据 file_id 删除数据"""
        if not self.collection:
            self.init_collection()
        
        self.collection.delete(f'metadata["file_id"] == "{file_id}"')
        self.collection.flush()
        print(f"✅ 已删除 file_id={file_id} 的数据")
    
    def close(self):
        """关闭连接"""
        connections.disconnect("default")
