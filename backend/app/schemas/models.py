"""
Pydantic 数据模型
定义 API 请求和响应的数据结构
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# ============ 文档上传 ============

class UploadResponse(BaseModel):
    """文档上传响应"""
    file_id: str
    filename: str
    status: str
    message: str


# ============ 问答 ============

class ChatRequest(BaseModel):
    """问答请求"""
    question: str = Field(..., description="用户问题", min_length=1)
    top_k: Optional[int] = Field(5, description="返回的结果数量")


class SourceDocument(BaseModel):
    """来源文档"""
    content: str
    score: float
    metadata: Dict[str, Any]


class ChatResponse(BaseModel):
    """问答响应"""
    answer: str
    sources: List[SourceDocument]
    graph_entities: Optional[List[Dict[str, Any]]] = None


# ============ 知识图谱 ============

class GraphNode(BaseModel):
    """图谱节点"""
    id: str
    name: str
    type: str
    properties: Dict[str, Any] = {}


class GraphRelation(BaseModel):
    """图谱关系"""
    source: str
    target: str
    type: str
    properties: Dict[str, Any] = {}


class GraphData(BaseModel):
    """图谱数据"""
    nodes: List[GraphNode]
    relations: List[GraphRelation]


class GraphResponse(BaseModel):
    """图谱查询响应"""
    data: GraphData
    total_nodes: int
    total_relations: int


# ============ 健康检查 ============

class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    milvus: str
    neo4j: str
    timestamp: datetime
