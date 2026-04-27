"""
重试策略模块
指数退避 + 熔断器
"""

import asyncio
import functools
import threading
import time
from collections import defaultdict
from typing import Any, Callable, Optional, TypeVar, Union

from app.logging import get_logger


logger = get_logger(__name__)

T = TypeVar("T")


class CircuitBreaker:
    """熔断器

    防止下游故障时持续调用
    状态：CLOSED（正常）-> OPEN（熔断）-> HALF_OPEN（尝试）
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout: float = 30.0,
        half_max_calls: int = 3,
    ):
        self.failure_threshold = failure_threshold  # 连续失败次数阈值
        self.success_threshold = success_threshold  # 半开恢复需要的成功次数
        self.timeout = timeout  # 熔断超时时间
        self.half_max_calls = half_max_calls

        self._failures = 0
        self._successes = 0
        self._state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self._last_failure_time = 0.0
        self._lock = threading.Lock()

    @property
    def state(self) -> str:
        """当前状态"""
        with self._lock:
            if self._state == "OPEN":
                # 检查超时
                if time.time() - self._last_failure_time > self.timeout:
                    self._state = "HALF_OPEN"
                    self._successes = 0
            return self._state

    def is_available(self) -> bool:
        """是否允许调用"""
        return self.state != "OPEN"

    def record_success(self) -> None:
        """记录成功"""
        with self._lock:
            if self._state == "HALF_OPEN":
                self._successes += 1
                if self._successes >= self.success_threshold:
                    self._state = "CLOSED"
                    self._failures = 0
                    logger.info("Circuit breaker CLOSED")

    def record_failure(self) -> None:
        """记录失败"""
        with self._lock:
            self._failures += 1
            self._last_failure_time = time.time()

            if self._state == "HALF_OPEN":
                self._state = "OPEN"
                logger.warning("Circuit breaker OPEN (half-open failure)")
            elif self._failures >= self.failure_threshold:
                self._state = "OPEN"
                logger.warning(f"Circuit breaker OPEN (failures: {self._failures})")


class ExponentialBackoff:
    """指数退避

    每��次重试间隔递增
    """

    def __init__(
        self,
        base: float = 1.0,
        max_delay: float = 60.0,
        multiplier: float = 2.0,
        jitter: float = 0.1,
    ):
        self.base = base
        self.max_delay = max_delay
        self.multiplier = multiplier
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        """获取延迟"""
        delay = min(self.base * (self.multiplier ** attempt), self.max_delay)

        # 添加抖动
        if self.jitter > 0:
            import random
            jitter_amount = delay * self.jitter * random.random()
            delay += jitter_amount

        return delay


def retry_with_backoff(
    max_attempts: int = 3,
    backoff: Optional[ExponentialBackoff] = None,
    exceptions: tuple = (Exception,),
    circuit_breaker: Optional[CircuitBreaker] = None,
):
    """重试装饰器

    用法：
        @retry_with_backoff(max_attempts=3)
        def fetch_data():
            ...
    """
    if backoff is None:
        backoff = ExponentialBackoff()

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_attempts):
                # 熔断检查
                if circuit_breaker and not circuit_breaker.is_available():
                    raise Exception(f"Circuit breaker OPEN, call failed")

                try:
                    result = func(*args, **kwargs)
                    if circuit_breaker:
                        circuit_breaker.record_success()
                    return result

                except exceptions as e:
                    last_exception = e
                    if circuit_breaker:
                        circuit_breaker.record_failure()

                    if attempt < max_attempts - 1:
                        delay = backoff.get_delay(attempt)
                        logger.warning(
                            f"Retry {attempt + 1}/{max_attempts} after {delay:.2f}s: {e}"
                        )
                        time.sleep(delay)
                    else:
                        logger.error(f"All attempts failed: {e}")

            raise last_exception

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_attempts):
                if circuit_breaker and not circuit_breaker.is_available():
                    raise Exception(f"Circuit breaker OPEN, call failed")

                try:
                    result = await func(*args, **kwargs)
                    if circuit_breaker:
                        circuit_breaker.record_success()
                    return result

                except exceptions as e:
                    last_exception = e
                    if circuit_breaker:
                        circuit_breaker.record_failure()

                    if attempt < max_attempts - 1:
                        delay = backoff.get_delay(attempt)
                        logger.warning(
                            f"Retry {attempt + 1}/{max_attempts} after {delay:.2f}s: {e}"
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"All attempts failed: {e}")

            raise last_exception

        # 根据函数类型返回同步或异步包装
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# 全局熔断器
_llm_circuit = CircuitBreaker(
    failure_threshold=5,
    success_threshold=2,
    timeout=30.0,
)

_milvus_circuit = CircuitBreaker(
    failure_threshold=3,
    success_threshold=1,
    timeout=15.0,
)

_neo4j_circuit = CircuitBreaker(
    failure_threshold=3,
    success_threshold=1,
    timeout=15.0,
)


def get_llm_circuit() -> CircuitBreaker:
    """获取 LLM 熔断器"""
    return _llm_circuit


def get_milvus_circuit() -> CircuitBreaker:
    """获取 Milvus 熔断器"""
    return _milvus_circuit


def get_neo4j_circuit() -> CircuitBreaker:
    """获取 Neo4j 熔断器"""
    return _neo4j_circuit


# 异步支持
import asyncio