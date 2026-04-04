"""
Embedding 模块
使用 BGE 模型生成文本向量
"""

from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from app.config import EMBEDDING_MODEL, EMBEDDING_DEVICE


class EmbeddingModel:
    """
    BGE Embedding 模型封装
    
    使用 shibing624/text2vec-base-chinese 模型生成中文文本的向量表示。
    """
    
    def __init__(self, model_name: str = EMBEDDING_MODEL, device: str = EMBEDDING_DEVICE):
        self.model_name = model_name
        self.device = device
        print(f"正在加载 Embedding 模型: {model_name}...")
        self.model = SentenceTransformer(model_name, device=device)
        print(f"✅ Embedding 模型加载完成，设备: {device}")
    
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
    
    def embed_documents(self, documents: List[Dict[str, Any]]) -> List[List[float]]:
        """
        将多个文档文本转换为向量
        
        Args:
            documents: 文档列表，每个元素包含 "content" 字段
            
        Returns:
            List[List[float]]: 向量列表
        """
        texts = [doc["content"] for doc in documents]
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()
    
    def get_dimension(self) -> int:
        """获取向量维度"""
        return self.model.get_sentence_embedding_dimension()
