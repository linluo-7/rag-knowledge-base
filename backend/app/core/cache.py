"""
缓存模块 - 多级缓存 + 一致性
"""

import hashlib
import json
import threading
import time
from typing import Any, Optional

from app.config import get_settings
from app.logging import get_logger


logger = get_logger(__name__)


class CacheKey:
    """缓存 Key 生成

    支持：
    - 内容 hash（解决 hash 碰撞）
    - 版本控制
    - 多租户隔离
    """

    @staticmethod
    def question_key(question: str, user_id: Optional[str] = None) -> str:
        """RAG 问答缓存 key"""
        # 使用问题内容的 SHA256 hash
        key = hashlib.sha256(question.encode()).hexdigest()

        # 添加用户前缀（多租户）
        if user_id:
            return f"rag:chat:{user_id}:{key}"
        return f"rag:chat:{key}"

    @staticmethod
    def document_key(file_id: str) -> str:
        """文档缓存 key"""
        return f"rag:doc:{file_id}"

    @staticmethod
    def graph_key() -> str:
        """图谱缓存 key"""
        return f"rag:graph:entities"


class MultiLevelCache:
    """多级缓存

    L1: 进程内缓存（dict）
    L2: Redis 分布式缓存
    """

    def __init__(self):
        settings = get_settings()
        self.ttl = settings.REDIS_CACHE_TTL
        self._l1_cache: dict = {}
        self._l1_lock = threading.RLock()
        self._redis = None

    def _get_redis(self):
        """获取 Redis"""
        if self._redis is None:
            from app.core.cache import RedisCache
            self._redis = RedisCache()
        return self._redis

    def get(self, key: str) -> Optional[Any]:
        """获取缓存（先 L1 再 L2）"""
        # L1 查找
        with self._l1_lock:
            entry = self._l1_cache.get(key)
            if entry:
                value, expiry = entry
                if time.time() < expiry:
                    logger.debug(f"L1 cache hit: {key[:30]}...")
                    return value
                else:
                    # 过期删除
                    del self._l1_cache[key]

        # L2 查找
        redis = self._get_redis()
        if not redis or not redis.ping():
            return None

        try:
            # 检查版本
            version_key = f"{key}:version"
            version = redis.get(version_key)
            if version is None:
                return None

            value = redis.get(key)
            if value:
                logger.debug(f"L2 cache hit: {key[:30]}...")

                # 回填 L1
                ttl = redis._client.ttl(key)
                expiry = time.time() + ttl if ttl > 0 else time.time() + self.ttl

                with self._l1_lock:
                    self._l1_cache[key] = (value, expiry)

                return value
        except Exception as e:
            logger.warning(f"Cache get error: {e}")

        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """设置缓存（同时写 L1 和 L2）"""
        ttl = ttl or self.ttl

        # 写 L1
        with self._l1_lock:
            self._l1_cache[key] = (value, time.time() + ttl)

        # 写 L2
        redis = self._self._get_redis()
        if not redis:
            return False

        try:
            # 版本控制
            version_key = f"{key}:version"
            version = redis.get(version_key) or 0
            redis.set(version_key, version + 1, ttl=ttl)

            return redis.set(key, value, ttl=ttl)
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
            return False

    def invalidate(self, key: str) -> bool:
        """失效缓存"""
        # 删 L1
        with self._l1_lock:
            self._l1_cache.pop(key, None)

        # 删 L2
        redis = self._get_redis()
        if not redis:
            return False

        try:
            version_key = f"{key}:version"
            redis.delete(key)
            redis.delete(version_key)
            return True
        except Exception as e:
            logger.warning(f"Cache invalidate error: {e}")
            return False

    def invalidate_pattern(self, pattern: str) -> int:
        """按模式失效"""
        count = 0

        # L1
        with self._l1_lock:
            keys_to_delete = [
                k for k in self._l1_cache.keys()
                if pattern.replace("*", "") in k
            ]
            for k in keys_to_delete:
                del self._l1_cache[k]
                count += 1

        # L2
        redis = self._get_redis()
        if redis:
            count += redis.clear_pattern(pattern)

        return count

    def clear(self) -> None:
        """清空所有缓存"""
        with self._l1_lock:
            self._l1_cache.clear()

        redis = self._get_redis()
        if redis:
            redis.clear_pattern("rag:*")


# 缓存实例
_cache: Optional[MultiLevelCache] = None


def get_cache() -> MultiLevelCache:
    """获取多级缓存"""
    global _cache
    if _cache is None:
        _cache = MultiLevelCache()
    return _cache


def invalidate_knowledge_base() -> int:
    """知识库更新时失效所有缓存"""
    return get_cache().invalidate_pattern("rag:chat:*")


def invalidate_document(file_id: str) -> bool:
    """文档删除时失效缓存"""
    key = CacheKey.document_key(file_id)
    return get_cache().invalidate(key)