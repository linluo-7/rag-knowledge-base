"""
自定义异常类
"""

from typing import Any, Optional


class RAGException(Exception):
    """RAG 系统基础异常"""

    def __init__(
        self,
        message: str = "RAG system error",
        code: str = "RAG_ERROR",
        status_code: int = 500,
        details: Optional[dict] = None,
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }


class DocumentParseError(RAGException):
    """文档解析异常"""

    def __init__(
        self,
        message: str = "Failed to parse document",
        details: Optional[dict] = None,
    ):
        super().__init__(
            message=message,
            code="DOCUMENT_PARSE_ERROR",
            status_code=400,
            details=details,
        )


class UnsupportedFormatError(DocumentParseError):
    """不支持的文件格式"""

    def __init__(self, format: str):
        super().__init__(
            message=f"Unsupported file format: {format}",
            details={"format": format},
        )


class VectorStoreError(RAGException):
    """向量存储异常"""

    def __init__(
        self,
        message: str = "Vector store error",
        details: Optional[dict] = None,
    ):
        super().__init__(
            message=message,
            code="VECTOR_STORE_ERROR",
            status_code=500,
            details=details,
        )


class VectorStoreConnectionError(VectorStoreError):
    """向量存储连接异常"""

    def __init__(self, details: Optional[dict] = None):
        super().__init__(
            message="Failed to connect to vector store",
            details=details,
        )


class GraphStoreError(RAGException):
    """图存储异常"""

    def __init__(
        self,
        message: str = "Graph store error",
        details: Optional[dict] = None,
    ):
        super().__init__(
            message=message,
            code="GRAPH_STORE_ERROR",
            status_code=500,
            details=details,
        )


class GraphStoreConnectionError(GraphStoreError):
    """图存储连接异常"""

    def __init__(self, details: Optional[dict] = None):
        super().__init__(
            message="Failed to connect to graph store",
            details=details,
        )


class LLMError(RAGException):
    """LLM 调用异常"""

    def __init__(
        self,
        message: str = "LLM call failed",
        details: Optional[dict] = None,
    ):
        super().__init__(
            message=message,
            code="LLM_ERROR",
            status_code=502,
            details=details,
        )


class LLMAuthError(LLMError):
    """LLM 认证异常"""

    def __init__(self, details: Optional[dict] = None):
        super().__init__(
            message="LLM API key is invalid or expired",
            details=details,
        )


class LLMQuotaError(LLMError):
    """LLM 配额异常"""

    def __init__(self, details: Optional[dict] = None):
        super().__init__(
            message="LLM API quota exceeded",
            details=details,
        )


class EmbeddingError(RAGException):
    """Embedding 异常"""

    def __init__(
        self,
        message: str = "Embedding failed",
        details: Optional[dict] = None,
    ):
        super().__init__(
            message=message,
            code="EMBEDDING_ERROR",
            status_code=500,
            details=details,
        )


class AuthenticationError(RAGException):
    """认证异常"""

    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[dict] = None,
    ):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            status_code=401,
            details=details,
        )


class RateLimitError(RAGException):
    """限流异常"""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        details: Optional[dict] = None,
    ):
        details = details or {}
        if retry_after:
            details["retry_after"] = retry_after
        super().__init__(
            message=message,
            code="RATE_LIMIT_ERROR",
            status_code=429,
            details=details,
        )


class ValidationError(RAGException):
    """验证异常"""

    def __init__(
        self,
        message: str = "Validation failed",
        details: Optional[dict] = None,
    ):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            status_code=400,
            details=details,
        )


class ResourceNotFoundError(RAGException):
    """资源不存在"""

    def __init__(
        self,
        resource: str,
        resource_id: Any = None,
        details: Optional[dict] = None,
    ):
        details = details or {}
        if resource_id:
            details["resource_id"] = str(resource_id)
        super().__init__(
            message=f"{resource} not found",
            code="RESOURCE_NOT_FOUND",
            status_code=404,
            details=details,
        )