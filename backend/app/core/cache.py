"""
Redis 缓存模块
"""

import json
import threading
from typing import Any, Optional

import redis

from app.config import get_settings
from app.logging import get_logger


logger = get_logger(__name__)


class RedisCache:
    """Redis 缓存实现"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # 避免重复初始化
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._initialized = True

        settings = get_settings()
        self._client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD or None,
            db=settings.REDIS_DB,
            decode_responses=True,
        )
        self._ttl = settings.REDIS_CACHE_TTL

    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        try:
            value = self._client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.warning(f"Cache get failed: {e}")
            return None

    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> bool:
        """设置缓存"""
        try:
            ttl = ttl or self._ttl
            serialized = json.dumps(value, ensure_ascii=False)
            return self._client.setex(key, ttl, serialized)
        except Exception as e:
            logger.warning(f"Cache set failed: {e}")
            return False

    def delete(self, key: str) -> bool:
        """删除缓存"""
        try:
            return bool(self._client.delete(key))
        except Exception as e:
            logger.warning(f"Cache delete failed: {e}")
            return False

    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            return bool(self._client.exists(key))
        except Exception as e:
            logger.warning(f"Cache exists failed: {e}")
            return False

    def clear_pattern(self, pattern: str) -> int:
        """清除匹配模式的所有键"""
        try:
            keys = self._client.keys(pattern)
            if keys:
                return self._client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Cache clear_pattern failed: {e}")
            return 0

    def ping(self) -> bool:
        """检查连接"""
        try:
            return self._client.ping()
        except Exception:
            return False

    def close(self) -> None:
        """关闭连接"""
        try:
            self._client.close()
        except Exception as e:
            logger.warning(f"Cache close failed: {e}")