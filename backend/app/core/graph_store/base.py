"""
图存储抽象接口
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class EntityNode:
    """实体节点"""

    id: str
    name: str
    type: str
    properties: Dict[str, Any]


@dataclass
class RelationEdge:
    """关系边"""

    from_node: str
    to_node: str
    type: str
    properties: Dict[str, Any]


class GraphStore(ABC):
    """图存储抽象接口"""

    @abstractmethod
    def init_schema(self) -> None:
        """初始化 Schema"""
        pass

    @abstractmethod
    def create_entity(
        self, name: str, entity_type: str, properties: Optional[Dict[str, Any]] = None
    ) -> None:
        """创建实体节点"""
        pass

    @abstractmethod
    def create_relation(
        self,
        from_entity: str,
        to_entity: str,
        relation_type: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> None:
        """创建关系边"""
        pass

    @abstractmethod
    def get_all_nodes(self) -> List[EntityNode]:
        """获取所有节点"""
        pass

    @abstractmethod
    def get_all_relations(self) -> List[RelationEdge]:
        """获取所有关系"""
        pass

    @abstractmethod
    def search_nodes(self, keyword: str) -> List[EntityNode]:
        """搜索节点"""
        pass

    @abstractmethod
    def get_node(self, name: str) -> Optional[EntityNode]:
        """获取指定节点"""
        pass

    @abstractmethod
    def get_node_relations(self, name: str) -> List[RelationEdge]:
        """获取节点的所有关系"""
        pass

    @abstractmethod
    def expand_entities(self, query: str) -> List[EntityNode]:
        """根据查询扩展相关实体"""
        pass

    @abstractmethod
    def clear_all(self) -> None:
        """清空所有数据"""
        pass

    @abstractmethod
    def check_connection(self) -> bool:
        """检查连接状态"""
        pass

    @abstractmethod
    def close(self) -> None:
        """关闭连接"""
        pass