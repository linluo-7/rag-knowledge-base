"""
限流中间件
基于 Redis 的分布式限流
"""

import time
from typing import Optional

from fastapi import HTTPException, Request, status

from app.config import get_settings
from app.logging import get_logger


logger = get_logger(__name__)


class RateLimiter:
    """限流器"""

    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        burst: int = 10,
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.burst = burst

        # 内存限流（单节点）
        self._minute_buckets: dict = {}
        self._hour_buckets: dict = {}

    def _get_client_key(self, request: Request) -> str:
        """获取客户端 key"""
        # 使用 IP + API Key
        client_ip = request.client.host if request.client else "unknown"
        api_key = request.headers.get("X-API-Key", "")
        return f"{client_ip}:{api_key}"

    def _check_rate(self, client_key: str) -> bool:
        """检查速率"""
        now = time.time()

        # 分钟限流
        minute_key = f"{client_key}:minute"
        minute_count = self._minute_buckets.get(minute_key, {"count": 0, "reset": 0})

        if now > minute_count["reset"]:
            minute_count = {"count": 0, "reset": now + 60}

        if minute_count["count"] >= self.requests_per_minute:
            return False

        minute_count["count"] += 1
        self._minute_buckets[minute_key] = minute_count

        # 小时限流
        hour_key = f"{client_key}:hour"
        hour_count = self._hour_buckets.get(hour_key, {"count": 0, "reset": 0})

        if now > hour_count["reset"]:
            hour_count = {"count": 0, "reset": now + 3600}

        if hour_count["count"] >= self.requests_per_hour:
            return False

        hour_count["count"] += 1
        self._hour_buckets[hour_key] = hour_count

        return True

    async def check(self, request: Request) -> bool:
        """检查限流"""
        settings = get_settings()

        # 不启用限流
        if not settings.AUTH_REQUIRED:
            return True

        # Redis 限流（分布式）
        if settings.CACHE_ENABLED:
            return await self._check_redis(request)

        # 内存限流（单节点）
        client_key = self._get_client_key(request)
        return self._check_rate(client_key)

    async def _check_redis(self, request: Request) -> bool:
        """Redis 限流"""
        from app.core.cache import RedisCache

        settings = get_settings()
        client_key = self._get_client_key(request)

        try:
            cache = RedisCache()

            # 每分钟限流
            minute_key = f"rate:minute:{client_key}"
            minute_count = cache.get(minute_key) or 0
            if minute_count >= self.requests_per_minute:
                return False

            # 每小时限流
            hour_key = f"rate:hour:{client_key}"
            hour_count = cache.get(hour_key) or 0
            if hour_count >= self.requests_per_hour:
                return False

            # 计数
            cache.set(minute_key, minute_count + 1, ttl=60)
            cache.set(hour_key, hour_count + 1, ttl=3600)

            return True

        except Exception as e:
            logger.warning(f"Rate limit check failed: {e}")
            return True  # 失败时放行

    def get_retry_after(self, request: Request) -> Optional[int]:
        """获取重试时间"""
        client_key = self._get_client_key(request)

        minute_key = f"{client_key}:minute"
        minute_bucket = self._minute_buckets.get(minute_key)

        if minute_bucket:
            remaining = self.requests_per_minute - minute_bucket["count"]
            if remaining <= 0:
                return max(0, int(minute_bucket["reset"] - time.time()))

        return None


# 全局限流器
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """获取限流器"""
    global _rate_limiter
    if _rate_limiter is None:
        settings = get_settings()
        _rate_limiter = RateLimiter(
            requests_per_minute=settings.RATE_LIMIT_PER_MINUTE,
            requests_per_hour=settings.RATE_LIMIT_PER_HOUR,
        )
    return _rate_limiter


async def check_rate_limit(request: Request) -> None:
    """检查限流"""
    settings = get_settings()

    if not settings.AUTH_REQUIRED:
        return

    limiter = get_rate_limiter()
    allowed = await limiter.check(request)

    if not allowed:
        retry_after = limiter.get_retry_after(request)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Rate limit exceeded",
                "retry_after": retry_after,
            },
            headers={
                "Retry-After": str(retry_after) if retry_after else "60",
            },
        )