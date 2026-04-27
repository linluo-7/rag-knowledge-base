"""
LLM 抽象接口
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class ChatMessage:
    """聊天消息"""

    role: str  # system, user, assistant
    content: str


@dataclass
class ChatResponse:
    """聊天响应"""

    content: str
    usage: Optional[Dict[str, Any]] = None
    model: str = ""


@dataclass
class Entity:
    """实体"""

    name: str
    type: str
    description: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None


@dataclass
class Relation:
    """关系"""

    from_node: str
    to_node: str
    type: str
    description: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None


class LLM(ABC):
    """LLM 抽象接口"""

    @abstractmethod
    def generate(
        self, question: str, context: str, messages: Optional[List[ChatMessage]] = None
    ) -> ChatResponse:
        """根据上下文生成回答"""
        pass

    @abstractmethod
    def extract_entities_and_relations(
        self, text: str
    ) -> Tuple[List[Entity], List[Relation]:
        """从文本中提取实体和关系"""
        pass

    @abstractmethod
    def summarize(
        self, text: str, max_length: int = 200
    ) -> str:
        """文本摘要"""
        pass

    @abstractmethod
    def close(self) -> None:
        """关闭连接"""
        pass