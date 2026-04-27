"""
RAG 服务抽象基类
"""

from abc import ABC, abstractmethod
from typing import List, Optional


class RAGServiceBase(ABC):
    """RAG 服务抽象接口"""

    @abstractmethod
    async def chat(
        self,
        question: str,
        user_id: Optional[str] = None,
        top_k: Optional[int] = None,
    ) -> dict:
        """RAG 问答"""
        pass