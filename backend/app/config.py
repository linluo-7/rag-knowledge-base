"""
配置管理模块
使用 Pydantic Settings 实现配置中心化
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置类"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore",
    )

    # ===== 环境配置 =====
    ENV: str = Field(default="development", description="运行环境")
    DEBUG: bool = Field(default=False, description="调试模式")

    # ===== API 配置 =====
    API_HOST: str = Field(default="0.0.0.0", description="API 主机")
    API_PORT: int = Field(default=5003, description="API 端口")
    API_V1_PREFIX: str = Field(default="/api/v1", description="API 前缀")

    # ===== 认证配置 =====
    API_KEYS: List[str] = Field(default=[], description="API Key 列表")
    AUTH_REQUIRED: bool = Field(default=False, description="是否需要认证")

    # ===== 限流配置 =====
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, description="每分钟请求限制")
    RATE_LIMIT_PER_HOUR: int = Field(default=1000, description="每小时请求限制")

    # ===== MiniMax LLM 配置 =====
    MINIMAX_API_KEY: str = Field(default="", description="MiniMax API Key")
    MINIMAX_API_KEYS: List[str] = Field(default=[], description="API Key 列表(轮换)")
    MINIMAX_BASE_URL: str = Field(
        default="https://api.minimax.chat/v", description="MiniMax 基础 URL"
    )
    LLM_MODEL: str = Field(default="abab6.5s-chat", description="LLM 模型")
    LLM_TEMPERATURE: float = Field(default=0.7, description="LLM 温度")
    LLM_MAX_TOKENS: int = Field(default=1024, description="LLM 最大 token 数")
    LLM_TIMEOUT: int = Field(default=120, description="LLM 超时时间(秒)")
    LLM_RETRY_TIMES: int = Field(default=3, description="LLM 重试次数")

    # ===== Neo4j 配置 =====
    NEO4J_URI: str = Field(default="bolt://localhost:7687", description="Neo4j URI")
    NEO4J_USER: str = Field(default="neo4j", description="Neo4j 用户名")
    NEO4J_PASSWORD: str = Field(default="neo4j123456", description="Neo4j 密码")
    NEO4J_DATABASE: str = Field(default="neo4j", description="Neo4j 数据库")
    NEO4J_POOL_SIZE: int = Field(default=10, description="Neo4j 连接池大小")
    NEO4J_CONNECTION_TIMEOUT: int = Field(default=30, description="连接超时时间")

    # ===== Milvus 配置 =====
    MILVUS_HOST: str = Field(default="localhost", description="Milvus 主机")
    MILVUS_PORT: int = Field(default=19530, description="Milvus 端口")
    MILVUS_USER: str = Field(default="", description="Milvus 用户名")
    MILVUS_PASSWORD: str = Field(default="", description="Milvus 密码")
    MILVUS_COLLECTION: str = Field(default="documents", description="Collection 名称")
    MILVUS_DIM: int = Field(default=768, description="向量维度")
    MILVUS_POOL_SIZE: int = Field(default=10, description="连接池大小")
    MILVUS_TIMEOUT: int = Field(default=30, description="超时时间")

    # ===== Embedding 配置 =====
    EMBEDDING_MODEL: str = Field(
        default="shibing624/text2vec-base-chinese",
        description="Embedding 模型名称",
    )
    EMBEDDING_DEVICE: str = Field(default="cpu", description="Embedding 设备")
    EMBEDDING_POOL_SIZE: int = Field(default=5, description="模型实例池大小")

    # ===== 文本分块配置 =====
    CHUNK_SIZE: int = Field(default=256, description="文本块大小")
    CHUNK_OVERLAP: int = Field(default=64, description="文本块重叠大小")

    # ===== RRF 融合配置 =====
    RRF_K: int = Field(default=60, description="RRF K 值")
    TOP_K: int = Field(default=5, description="返回结果数量")
    MAX_CONTEXT_K: int = Field(default=3, description="最大上下文块数")

    # ===== 缓存配置 =====
    REDIS_HOST: str = Field(default="localhost", description="Redis 主机")
    REDIS_PORT: int = Field(default=6379, description="Redis 端口")
    REDIS_PASSWORD: str = Field(default="", description="Redis 密码")
    REDIS_DB: int = Field(default=0, description="Redis 数据库编号")
    REDIS_CACHE_TTL: int = Field(default=3600, description="缓存过期时间(秒)")
    CACHE_ENABLED: bool = Field(default=False, description="是否启用缓存")

    # ===== 上传配置 =====
    UPLOAD_DIR: str = Field(default="./uploads", description="上传文件目录")
    MAX_UPLOAD_SIZE: int = Field(default=10 * 1024 * 1024, description="最大上传文件大小")
    ALLOWED_EXTENSIONS: List[str] = Field(
        default=[".txt", ".docx"], description="允许的文件扩展名"
    )

    # ===== 日志配置 =====
    LOG_LEVEL: str = Field(default="INFO", description="日志级别")
    LOG_FORMAT: str = Field(
        default="json", description="日志格式 (json/text)"
    )
    LOG_FILE: str = Field(default="./logs/app.log", description="日志文件路径")
    LOG_MAX_SIZE: int = Field(default=100, description="日志文件最大大小(MB)")
    LOG_BACKUP_COUNT: int = Field(default=10, description="日志文件保留数量")

    # ===== 监控配置 =====
    METRICS_ENABLED: bool = Field(default=True, description="是否启用监控")
    TRACE_ENABLED: bool = Field(default=False, description="是否启用链路追踪")

    @property
    def is_production(self) -> bool:
        """判断是否为生产环境"""
        return self.ENV.lower() in ["prod", "production"]

    @property
    def is_development(self) -> bool:
        """判断是否为开发环境"""
        return self.ENV.lower() in ["dev", "development"]


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()