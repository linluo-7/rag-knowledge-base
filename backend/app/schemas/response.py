"""
响应数据模型
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SourceDocument(BaseModel):
    """检索来源文档"""

    content: str = Field(..., description="文档内容")
    score: float = Field(..., description="相似度分数")
    metadata: Dict[str, Any] = Field(default={}, description="元数据")


class ChatResponse(BaseModel):
    """问答响应"""

    answer: str = Field(..., description="回答内容")
    sources: List[SourceDocument] = Field(default=[], description="检索来源")
    graph_entities: List[Dict[str, str]] = Field(
        default=[], description="相关实体"
    )
    latent_ms: float = Field(..., description="延迟(毫秒)")


class UploadResponse(BaseModel):
    """上传响应"""

    file_id: str = Field(..., description="文件ID")
    filename: str = Field(..., description="文件名")
    status: str = Field(..., description="状态")
    message: str = Field(..., description="消息")
    chunks_count: int = Field(default=0, description="文本块数量")
    entities_count: int = Field(default=0, description="实体数量")
    relations_count: int = Field(default=0, description="关系数量")


class EntityData(BaseModel):
    """实体数据"""

    id: str
    name: str
    type: str
    properties: Dict[str, Any] = Field(default={})


class RelationData(BaseModel):
    """关系数据"""

    from_node: str = Field(..., alias="from")
    to_node: str = Field(..., alias="to")
    type: str
    properties: Dict[str, Any] = Field(default={})

    class Config:
        populate_by_name = True


class GraphData(BaseModel):
    """图谱数据"""

    nodes: List[EntityData] = Field(default=[], description="实体节点")
    links: List[RelationData] = Field(default=[], description="关系边")


class HealthResponse(BaseModel):
    """健康检查响应"""

    status: str = Field(..., description="状态")
    milvus: str = Field(..., description="Milvus 状态")
    neo4j: str = Field(..., description="Neo4j 状态")
    timestamp: str = Field(..., description="时间戳")


class ErrorResponse(BaseModel):
    """错误响应"""

    error: Dict[str, Any] = Field(..., description="错误信息")