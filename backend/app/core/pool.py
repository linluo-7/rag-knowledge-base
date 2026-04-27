"""
线程安全的连接池管理
"""

import asyncio
import threading
from contextlib import asynccontextmanager, contextmanager
from typing import Any, Callable, Generic, TypeVar
from weakref import WeakValueDictionary

from app.logging import get_logger


logger = get_logger(__name__)

T = TypeVar("T")


class PooledConnection:
    """连接池"""

    def __init__(self, factory: Callable[[], Any]):
        self._factory = factory
        self._lock = threading.Lock()
        self._connections: list = []
        self._semaphore: asyncio.Semaphore = None
        self._max_size = 10
        self._created = 0

    def acquire(self) -> Any:
        """获取连接（同步）"""
        with self._lock:
            if self._connections:
                return self._connections.pop()
            if self._created < self._max_size:
                self._created += 1
                return self._factory()
        # 等待或新建
        return self._factory()

    def release(self, conn: Any) -> None:
        """释放连接回池"""
        with self._lock:
            if len(self._connections) < self._max_size:
                self._connections.append(conn)

    @async def acquire_async(self) -> Any:
        """获取连接（异步）"""
        if self._semaphore is None:
            self._semaphore = asyncio.Semaphore(self._max_size)
        await self._semaphore.acquire()

        if self._connections:
            conn = self._connections.pop()
            return conn

        self._created += 1
        return self._factory()

    @async def release_async(self, conn: Any) -> None:
        """释放连接（异步）"""
        self._semaphore.release()
        with self._lock:
            if len(self._connections) < self._max_size:
                self._connections.append(conn)


class ThreadSafeSingleton(Generic[T]):
    """线程安全的单例基类

    使用双重检查锁定 + 进程内锁，确保线程安全
    """

    _instances: "WeakValueDictionary[str, T]" = WeakValueDictionary()
    _lock = threading.RLock()

    @classmethod
    def get_instance(cls, key: str = "default") -> T:
        """获取单例实例"""
        with cls._lock:
            if key not in cls._instances or cls._instances.get(key) is None:
                instance = cls._create_instance(key)
                cls._instances[key] = instance
            return cls._instances[key]

    @classmethod
    def _create_instance(cls, key: str) -> T:
        """子类实现创建逻辑"""
        raise NotImplementedError

    @classmethod
    def reset(cls, key: str = "default") -> None:
        """重置实例（测试用）"""
        with cls._lock:
            if key in cls._instances:
                instance = cls._instances.pop(key)
                if hasattr(instance, "close"):
                    try:
                        instance.close()
                    except Exception:
                        pass


class PerRequestInstance:
    """请求级实例 - 每次请求创建新的

    适用于需要保持状态的实例
    """

    @classmethod
    def get_instance(cls) -> T:
        return cls()


def get_async_pool(factory: Callable[[], Any]) -> PooledConnection:
    """创建异步连接池"""
    pool = PooledConnection(factory)
    return pool


@contextmanager
def use_connection(pool: PooledConnection):
    """同步使用连接"""
    conn = pool.acquire()
    try:
        yield conn
    finally:
        pool.release(conn)


@asynccontextmanager
async def use_connection_async(pool: PooledConnection):
    """异步使用连接"""
    conn = pool.acquire_async()
    try:
        yield conn
    finally:
        await pool.release_async(conn)