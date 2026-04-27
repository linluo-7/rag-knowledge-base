"""
日志配置模块
结构化日志 + 多级别输出
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from app.config import get_settings


class JSONFormatter(logging.Formatter):
    """JSON 格式日志formatter"""

    def __init__(self, include_extra: bool = True):
        super().__init__()
        self.include_extra = include_extra

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # 添加额外字段
        if self.include_extra:
            extra_fields = {
                k: v
                for k, v in record.__dict__.items()
                if not k.startswith("_")
                and k not in ["name", "msg", "args", "created", "filename", "funcName", "levelname", "levelno", "lineno", "module", "msecs", "pathname", "process", "processName", "relativeCreated", "thread", "threadName", "exc_info", "exc_text", "stack_info"]
            }
            log_data.update(extra_fields)

        return json.dumps(log_data, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    """文本格式日志formatter"""

    def __init__(self, fmt: str = None):
        super().__init__(fmt)

    def format(self, record: logging.LogRecord) -> str:
        if not record.args:
            return record.getMessage()

        try:
            return record.getMessage() % record.args
        except (TypeError, ValueError):
            return record.getMessage()


def setup_logging() -> None:
    """配置日志系统"""
    settings = get_settings()

    # 创建日志目录
    log_file = Path(settings.LOG_FILE)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # 获取根 logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))

    # 清除现有 handlers
    logger.handlers.clear()

    # 控制台 Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    if settings.LOG_FORMAT == "json":
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(
            TextFormatter(
                fmt="%(asctime)s | %(level)-8s | %(name)s | %(message)s"
            )
        )
    logger.addHandler(console_handler)

    # 文件 Handler（生产环境）
    if settings.is_production or settings.LOG_FILE:
        file_handler = logging.handlers.RotatingFileHandler(
            filename=settings.LOG_FILE,
            maxBytes=settings.LOG_MAX_SIZE * 1024 * 1024,
            backupCount=settings.LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.INFO)
        if settings.LOG_FORMAT == "json":
            file_handler.setFormatter(JSONFormatter(include_extra=False))
        else:
            file_handler.setFormatter(
                TextFormatter(
                    fmt="%(asctime)s | %(level)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s"
                )
            )
        logger.addHandler(file_handler)

    # 设置第三方库日志级别
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    logging.getLogger("pymilvus").setLevel(logging.WARNING)
    logging.getLogger("neo4j").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """获取指定名称的 logger"""
    return logging.getLogger(name)


# ============ 便捷日志函数 ============


def log_request(
    method: str,
    path: str,
    status_code: int,
    latency_ms: float,
    user_id: Optional[str] = None,
) -> None:
    """记录 HTTP 请求日志"""
    logger = logging.getLogger("request")
    logger.info(
        f"{method} {path} {status_code}",
        extra={
            "method": method,
            "path": path,
            "status_code": status_code,
            "latency_ms": latency_ms,
            "user_id": user_id,
        },
    )


def log_rag_query(
    question: str,
    sources_count: int,
    latency_ms: float,
    success: bool = True,
) -> None:
    """记录 RAG 查询日志"""
    logger = logging.getLogger("rag")
    logger.info(
        f"RAG query: {question[:50]}... (sources: {sources_count})",
        extra={
            "question": question,
            "sources_count": sources_count,
            "latency_ms": latency_ms,
            "success": success,
        },
    )


def log_llm_call(
    model: str,
    latency_ms: float,
    success: bool = True,
    error: Optional[str] = None,
) -> None:
    """记录 LLM 调用日志"""
    logger = logging.getLogger("llm")
    logger.info(
        f"LLM call: {model}",
        extra={
            "model": model,
            "latency_ms": latency_ms,
            "success": success,
            "error": error,
        },
    )


def log_embedding(
    model: str,
    texts_count: int,
    latency_ms: float,
    success: bool = True,
) -> None:
    """记录 Embedding 日志"""
    logger = logging.getLogger("embedding")
    logger.info(
        f"Embedding: {model} ({texts_count} texts)",
        extra={
            "model": model,
            "texts_count": texts_count,
            "latency_ms": latency_ms,
            "success": success,
        },
    )


# ============ 初始化 ============
if __name__ != "__main__":
    setup_logging()