"""
敏感信息脱敏模块
"""

import logging
import re
from typing import Any, Dict, Optional


logger = logging.getLogger(__name__)


# 敏感字段
SENSITIVE_FIELDS = {
    "password",
    "api_key",
    "secret",
    "token",
    "credential",
    "private_key",
    "access_key",
    "auth",
}

# 敏感值模式
SENSITIVE_PATTERNS = [
    (r"sk-[a-zA-Z0-9]{20,}", "sk-***"),  # OpenAI
    (r"eyJ[a-zA-Z0-9_-]*\.eyJ[a-zA-Z0-9_-]*\.[a-zA-Z0-9_-]*", "jwt***"),  # JWT
    (r"[a-zA-Z0-9]{32,}", "***"),  # 通用长字符串
]


def mask_sensitive_value(value: str) -> str:
    """脱敏值"""
    if not value or not isinstance(value, str):
        return value

    for pattern, replacement in SENSITIVE_PATTERNS:
        if re.search(pattern, value):
            return replacement

    # 保留前4位和后4位
    if len(value) > 8:
        return f"{value[:4]}***{value[-4:]}"
    return "***"


def sanitize_dict(data: Dict[str, Any], depth: int = 0) -> Dict[str, Any]:
    """脱敏字典

    递归脱敏敏感字段
    """
    if depth > 5:  # 防止无限递归
        return data

    if not isinstance(data, dict):
        return data

    result = {}
    for key, value in data.items():
        # 检查字段名
        key_lower = key.lower()
        is_sensitive = any(
            s in key_lower for s in SENSITIVE_FIELDS
        )

        if is_sensitive and value:
            result[key] = "***"
        elif isinstance(value, dict):
            result[key] = sanitize_dict(value, depth + 1)
        elif isinstance(value, list):
            result[key] = [
                sanitize_dict(item, depth + 1) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[key] = value

    return result


def sanitize_error(error: Exception, include_trace: bool = False) -> Dict[str, Any]:
    """脱敏错误信息

    生产环境使用
    """
    error_dict = {
        "type": type(error).__name__,
        "message": str(error),
    }

    if include_trace:
        import traceback
        error_dict["traceback"] = traceback.format_exc()

    return sanitize_dict(error_dict)


def sanitize_for_log(
    message: str,
    extra: Optional[Dict[str, Any]] = None,
) -> tuple:
    """脱敏日志消息

    Returns:
        (sanitized_message, sanitized_extra)
    """
    sanitized_extra = {}
    if extra:
        sanitized_extra = sanitize_dict(extra)

    # 检查消息是否包含敏感信息
    message_lower = message.lower()
    for field in SENSITIVE_FIELDS:
        if field in message_lower:
            message = re.sub(
                rf"{field}[=:]\s*[^\s]+",
                f"{field}=***",
                message,
                flags=re.IGNORECASE,
            )

    return message, sanitized_extra