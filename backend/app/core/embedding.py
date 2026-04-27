"""
Embedding 模型 - 优化版
GPU 批处理 + Dynamic Batching
"""

import asyncio
import threading
import time
from collections import deque
from typing import List, Optional

from sentence_transformers import SentenceTransformer

from app.config import get_settings
from app.logging import get_logger


logger = get_logger(__name__)


class BatchingConfig:
    """批处理配置"""

    # 批次大小
    BATCH_SIZE: int = 32

    # 最大等待时间 (毫秒)
    MAX_WAIT_TIME_MS: int = 100

    # 最大队列长度
    MAX_QUEUE_SIZE: int = 1000


class EmbeddingTask:
    """Embedding 任务"""

    def __init__(self, text: str, future: asyncio.Future):
        self.text = text
        self.future = future
        self.submit_time = time.time()


class DynamicBatcher:
    """动态批处理器

    累积一定数量的请求后批量处理，提高 GPU 利用率
    """

    def __init__(self, batch_size: int = 32, max_wait_ms: int = 100):
        self.batch_size = batch_size
        self.max_wait_ms = max_wait_ms / 1000  # 转换为秒

        self._queue: deque = deque()
        self._lock = threading.Lock()
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self, processor_fn):
        """启动批处理器"""
        self._running = True
        self._processor = processor_fn

        self._thread = threading.Thread(target=self._batch_loop, daemon=True)
        self._thread.start()

    def _batch_loop(self):
        """批处理循环"""
        while self._running:
            time.sleep(0.01)  # 10ms 检查一次

            with self._lock:
                if len(self._queue) < self.batch_size:
                    # 检查是否超时
                    if not self._queue:
                        continue

                    oldest = self._queue[0]
                    if time.time() - oldest.submit_time < self.max_wait_ms:
                        continue

                # 收集批次
                if not self._queue:
                    continue

                batch = []
                for _ in range(min(self.batch_size, len(self._queue))):
                    if self._queue:
                        batch.append(self._queue.popleft())

            if batch:
                texts = [task.text for task in batch]
                try:
                    results = self._processor(texts)
                    for task, result in zip(batch, results):
                        task.future.set_result(result)
                except Exception as e:
                    for task in batch:
                        task.future.set_exception(e)

    def submit(self, text: str) -> asyncio.Future:
        """提交任务"""
        future = asyncio.Future()
        task = EmbeddingTask(text, future)

        with self._lock:
            if len(self._queue) >= BatchingConfig.MAX_QUEUE_SIZE:
                # 队列满，拒绝
                future.set_exception(Exception("Queue full"))
            else:
                self._queue.append(task)

        return future

    def stop(self):
        """停止"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1)


class EmbeddingModel:
    """优化版 Embedding 模型

    特性：
    - GPU 批处理
    - FP16 推理
    - 预热
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, model_name: str = None, device: str = None):
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._initialized = True

        settings = get_settings()
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.device = device or settings.EMBEDDING_DEVICE

        logger.info(f"Loading Embedding model: {self.model_name}...")

        # 加载模型
        self.model = SentenceTransformer(self.model_name, device=self.device)

        # FP16 优化
        if self.device == "cuda":
            try:
                self.model = self.model.half()  # FP16
                logger.info("FP16 optimization enabled")
            except Exception as e:
                logger.warning(f"FP16 not supported: {e}")

        # 启动批处理器
        self._batcher = DynamicBatcher(
            batch_size=BatchingConfig.BATCH_SIZE,
            max_wait_ms=BatchingConfig.MAX_WAIT_TIME_MS,
        )

        logger.info(f"Embedding model loaded, device: {self.device}")

    def embed_query(self, query: str) -> List[float]:
        """单条查询（同步）"""
        embedding = self.model.encode(query, normalize_embeddings=True)
        return embedding.tolist()

    def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """批量文档向量化（同步）"""
        embeddings = self.model.encode(documents, normalize_embeddings=True)
        return embeddings.tolist()

    async def embed_query_async(self, query: str) -> List[float]:
        """单条异步查询"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.embed_query, query)

    async def embed_documents_async(self, documents: List[str]) -> List[List[float]]:
        """批量异步向量化"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.embed_documents, documents)

    def warmup(self, num: int = 10):
        """预热"""
        dummy_texts = ["warmup text"] * num
        logger.info(f"Warming up with {num} texts...")
        self.embed_documents(dummy_texts)
        logger.info("Warmup complete")

    def get_dimension(self) -> int:
        """获取维度"""
        return self.model.get_sentence_embedding_dimension()