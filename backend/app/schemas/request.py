"""
请求数据模型
"""

from typing import List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """问答请求"""

    question: str = Field(..., description="问题", min_length=1, max_length=2000)
    top_k: Optional[int] = Field(default=5, description="返回结果数量", ge=1, le=20)
    user_id: Optional[str] = Field(default=None, description="用户ID")


class UploadRequest(BaseModel):
    """上传请求"""

    filename: str = Field(..., description="文件名")
    file_id: Optional[str] = Field(default=None, description="文件ID")


class GraphSearchRequest(BaseModel):
    """图谱搜索请求"""

    keyword: str = Field(..., description="搜索关键词", min_length=1)
    limit: Optional[int] = Field(default=10, description="返回数量", ge=1, le=100)