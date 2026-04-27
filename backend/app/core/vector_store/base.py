"""
向量存储抽象接口
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class SearchResult:
    """检索结果"""

    content: str
    score: float
    metadata: Dict[str, Any]


@dataclass
class VectorDocument:
    """向量文档"""

    content: str
    vector: List[float]
    metadata: Optional[Dict[str, Any]] = None


class VectorStore(ABC):
    """向量存储抽象接口"""

    @abstractmethod
    def init_collection(self, force: bool = False) -> None:
        """初始化 Collection"""
        pass

    @abstractmethod
    def insert(self, documents: List[VectorDocument]) -> None:
        """插入文档"""
        pass

    @abstractmethod
    def search(
        self, query_vector: List[float], top_k: int = 5
    ) -> List[SearchResult]:
        """向量相似度检索"""
        pass

    @abstractmethod
    def search_by_text(self, text: str, top_k: int = 5) -> List[SearchResult]:
        """文本检索（自动向量化）"""
        pass

    @abstractmethod
    def get_all(self, limit: int = 1000) -> List[VectorDocument]:
        """获取所有文档"""
        pass

    @abstractmethod
    def delete_by_file_id(self, file_id: str) -> None:
        """根据 file_id 删除数据"""
        pass

    @abstractmethod
    def check_connection(self) -> bool:
        """检查连接状态"""
        pass

    @abstractmethod
    def close(self) -> None:
        """关闭连接"""
        pass