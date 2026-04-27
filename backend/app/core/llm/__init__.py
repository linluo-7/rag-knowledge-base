"""
LLM 模块初始化
"""

from app.core.llm.base import LLM, ChatMessage, ChatResponse, Entity, Relation
from app.core.llm.minimax import MiniMaxLLM

__all__ = ["LLM", "ChatMessage", "ChatResponse", "Entity", "Relation", "MiniMaxLLM"]