"""
限流中间件 - Redis 分布式限流
滑动窗口 + 令牌桶
"""

import hashlib
import time
from typing import Optional

from fastapi import HTTPException, Request, status

from app.config import get_settings
from app.logging import get_logger


logger = get_logger(__name__)


class DistributedRateLimiter:
    """分布式限流器

    支持：
    - 滑动窗口精确限流
    - Redis 分布式计数
    - 按用户/IP 多维度
    """

    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        requests_per_day: int = 10000,
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.requests_per_day = requests_per_day
        self._redis = None

    def _get_redis(self):
        """获取 Redis"""
        if self._redis is None:
            from app.core.cache import RedisCache
            self._redis = RedisCache()
        return self._redis

    def _get_client_key(self, request: Request) -> str:
        """获取客户端 key"""
        # 按 IP + API Key
        client_ip = request.client.host if request.client else "unknown"
        api_key = request.headers.get("X-API-Key", "")
        return f"{client_ip}:{api_key}"

    def _sliding_window_count(
        self, key: str, window_seconds: int, limit: int
    ) -> tuple:
        """滑动窗口计数

        Returns:
            (allowed, remaining, reset_seconds)
        """
        redis = self._get_redis()
        if not redis or not redis.ping():
            # Redis 不可用，放行
            return True, limit, window_seconds

        now = time.time()
        window_key = f"rate:sw:{key}:{window_seconds}"

        try:
            # 获取当前窗口内的请求
            pipe_key = f"{window_key}:{int(now // window_seconds)}"

            # 使用 Redis 管道批量操作
            pipe = redis._client.pipeline()
            pipe.zremrangebyscore(pipe_key, 0, now - window_seconds)  # 清除过期
            pipe.zadd(pipe_key, {str(now): now})  # 添加当前请求
            pipe.zcard(pipe_key)  # 计数
            pipe.expire(pipe_key, window_seconds + 1)  # 设置过期

            results = pipe.execute()
            count = results[2]  # zcard 结果

            remaining = limit - count
            reset_seconds = window_seconds - int(now % window_seconds)

            if remaining < 0:
                return False, 0, reset_seconds
            return True, max(0, remaining), reset_seconds

        except Exception as e:
            logger.warning(f"Redis rate limit error: {e}")
            return True, limit, window_seconds

    def _token_bucket_refill(
        self, key: str, capacity: int, refill_rate: float
    ) -> tuple:
        """令牌桶算法

        Returns:
            (tokens_available, wait_time)
        """
        redis = self._get_redis()
        if not redis or not redis.ping():
            return capacity, 0

        bucket_key = f"rate:tb:{key}"

        try:
            now = time.time()
            data = redis._client.hgetall(bucket_key)

            if not data:
                # 新桶
                redis._client.hset(bucket_key, mapping={
                    "tokens": str(capacity),
                    "last_refill": str(now),
                })
                redis._client.expire(bucket_key, int(capacity / refill_rate) + 60)
                return capacity, 0

            tokens = float(data.get(b"tokens", capacity))
            last_refill = float(data.get(b"last_refill", now))

            # 补充令牌
            elapsed = now - last_refill
            new_tokens = min(capacity, tokens + elapsed * refill_rate)

            if new_tokens < 1:
                wait_time = (1 - new_tokens) / refill_rate
                return 0, wait_time

            # 消耗令牌
            new_tokens -= 1
            redis._client.hset(bucket_key, mapping={
                "tokens": str(new_tokens),
                "last_refill": str(now),
            })

            return new_tokens, 0

        except Exception as e:
            logger.warning(f"Token bucket error: {e}")
            return capacity, 0

    async def check(self, request: Request) -> tuple:
        """检查限流

        Returns:
            (allowed: bool, remaining: int, reset: int)
        """
        settings = get_settings()
        if not settings.AUTH_REQUIRED:
            return True, self.requests_per_minute, 60

        client_key = self._get_client_key(request)

        # 多层限流
        # 1. 分钟级滑动窗口
        allowed, remaining, reset = self._sliding_window_count(
            f"{client_key}:min", 60, self.requests_per_minute
        )
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded (per minute)",
                    "retry_after": reset,
                },
                headers={"Retry-After": str(reset)},
            )

        # 2. 小时级
        allowed, remaining, reset = self._sliding_window_count(
            f"{client_key}:hour", 3600, self.requests_per_hour
        )
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded (per hour)",
                    "retry_after": reset,
                },
                headers={"Retry-After": str(reset)},
            )

        # 3. 天级（可选）
        if self.requests_per_day:
            allowed, remaining, reset = self._sliding_window_count(
                f"{client_key}:day", 86400, self.requests_per_day
            )
            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "Rate limit exceeded (per day)",
                        "retry_after": reset,
                    },
                    headers={"Retry-After": str(reset)},
                )

        return True, remaining, 60


# 全局限流器
_rate_limiter: Optional[DistributedRateLimiter] = None


def get_rate_limiter() -> DistributedRateLimiter:
    """获取限流器"""
    global _rate_limiter
    if _rate_limiter is None:
        settings = get_settings()
        _rate_limiter = DistributedRateLimiter(
            requests_per_minute=settings.RATE_LIMIT_PER_MINUTE,
            requests_per_hour=settings.RATE_LIMIT_PER_HOUR,
        )
    return _rate_limiter


async def check_rate_limit(request: Request) -> None:
    """限流检查（中间件用）"""
    settings = get_settings()
    if not settings.AUTH_REQUIRED:
        return

    limiter = get_rate_limiter()
    await limiter.check(request)