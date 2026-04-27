"""
安全模块 - 渗透防护
"""

import hashlib
import re
import subprocess
from pathlib import Path
from typing import List, Optional, Set

from app.logging import get_logger


logger = get_logger(__name__)


class SecurityConfig:
    """安全配置"""

    # 允许的文件扩展名
    ALLOWED_EXTENSIONS: Set[str] = {".txt", ".docx", ".doc", ".pdf", ".md"}

    # 禁止的文件扩展名（危险）
    FORBIDDEN_EXTENSIONS: Set[str] = {
        ".exe", ".bat", ".cmd", ".ps1", ".sh", ".bash",
        ".jar", ".class", ".py", ".js", ".php", ".asp",
        ".htaccess", ".ini", ".conf", ".config",
        ".so", ".dll", ".dylib",
        ".zip", ".rar", ".7z", ".tar", ".gz",
        ".html", ".htm", ".php", ".jsp",
    }

    # 文件大小限制 (10MB)
    MAX_FILE_SIZE: int = 10 * 1024 * 1024

    # MIME 类型白名单
    ALLOWED_MIME_TYPES: Set[str] = {
        "text/plain",
        "application/msword",
        "application/pdf",
        "text/markdown",
    }

    # 危险文件特征
    DANGEROUS_PATTERNS: List[bytes] = [
        b"MZ",  # PE header
        b"#!",  # Shebang
        b"#!/bin/sh",
        b"<?php",
        b"<%",
        b"<script",
        b"eval(",
        b"exec(",
    ]


class FileSecurity:
    """文件安全检查"""

    @staticmethod
    def is_safe_filename(filename: str) -> bool:
        """检查文件名安全"""
        # 获取扩展名
        ext = Path(filename).suffix.lower()

        # 检查是否在白名单
        if ext in SecurityConfig.ALLOWED_EXTENSIONS:
            return True

        # 检查是否在黑名单
        if ext in SecurityConfig.FORBIDDEN_EXTENSIONS:
            logger.warning(f"Forbidden file extension: {ext}")
            return False

        # 未知扩展名，报错
        logger.warning(f"Unknown file extension: {ext}")
        return False

    @staticmethod
    def is_safe_content(content: bytes) -> bool:
        """检查文件内容安全"""
        # 检查危险特征
        for pattern in SecurityConfig.DANGEROUS_PATTERNS:
            if pattern in content[:512]:  # 只检查开头
                logger.warning(f"Dangerous pattern found: {pattern}")
                return False

        # 检查文件大小
        if len(content) > SecurityConfig.MAX_FILE_SIZE:
            logger.warning(f"File too large: {len(content)} bytes")
            return False

        return True

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """清理文件名"""
        # 移除路径遍历
        filename = filename.replace("..", "")
        filename = filename.replace("/", "")
        filename = filename.replace("\\", "")

        # 移除特殊字符
        filename = re.sub(r"[^\w\s.-]", "", filename)

        # 限制长度
        if len(filename) > 255:
            filename = filename[:255]

        return filename

    @staticmethod
    def get_mime_type(filename: str, content: bytes) -> Optional[str]:
        """简单 MIME 类型检测"""
        ext = Path(filename).suffix.lower()

        mime_map = {
            ".txt": "text/plain",
            ".doc": "application/msword",
            ".docx": "application/msword",
            ".pdf": "application/pdf",
            ".md": "text/markdown",
        }

        return mime_map.get(ext)


class PromptInjectionProtection:
    """Prompt 注入防护"""

    # 危险指令模式
    DANGEROUS_PATTERNS = [
        r"ignore\s+(previous|above|all)",
        r"disregard\s+(previous|above|all)",
        r"forget\s+(everything|all|your)",
        r"new\s+(instruction|rules?|prompt)",
        r"system\s*:",
        r"assistant\s*:",
        r"#!\s*",
        r"<!--",
        r"<\?php",
        r"<script",
    ]

    @classmethod
    def sanitize_input(cls, text: str) -> str:
        """清理输入，移除危险指令"""
        result = text

        for pattern in cls.DANGEROUS_PATTERNS:
            result = re.sub(pattern, "[FILTERED]", result, flags=re.IGNORECASE)

        return result

    @classmethod
    def detect_injection(cls, text: str) -> bool:
        """检测是否有注入"""
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning(f"Potential prompt injection detected: {pattern}")
                return True
        return False


class SSRFProtection:
    """SSRF 防护

    防止请求内部服务
    """

    # 内部网络 CIDR
    INTERNAL_RANGES: List[tuple] = [
        ("127.0.0.0", "255.0.0.0"),      # 127.0.0.0/8
        ("10.0.0.0", "255.0.0.0"),       # 10.0.0.0/8
        ("172.16.0.0", "255.240.0.0"),  # 172.16.0.0/12
        ("192.168.0.0", "255.255.0.0"),  # 192.168.0.0/16
        ("169.254.0.0", "255.255.0.0"),  # Link-local
    ]

    # 内部域名
    INTERNAL_HOSTS: Set[str] = {
        "localhost",
        "milvus",
        "milvus-standalone",
        "neo4j",
        "redis",
        "mongo",
        "elasticsearch",
        "grafana",
        "prometheus",
    }

    @classmethod
    def is_internal_request(cls, host: str) -> bool:
        """检查是否是内部请求"""
        import ipaddress

        host = host.lower()

        # 检查内部域名
        if host in cls.INTERNAL_HOSTS:
            return True

        # 检查 IP
        try:
            ip = ipaddress.ip_address(host)
            for network, mask in cls.INTERNAL_RANGES:
                net = ipaddress.ip_network(f"{network}/{mask}", strict=False)
                if ip in net:
                    logger.warning(f"Blocked internal IP: {host}")
                    return True
        except Exception:
            pass

        return False

    @classmethod
    def validate_url(cls, url: str) -> bool:
        """验证 URL"""
        from urllib.parse import urlparse

        try:
            parsed = urlparse(url)
            if parsed.hostname and cls.is_internal_request(parsed.hostname):
                logger.warning(f"Blocked internal URL: {url}")
                return False
        except Exception:
            pass

        return True


class EmbeddingSecurity:
    """Embedding 安全 - 防止投毒

    恶意输入可能导致模型行为异常
    """

    # 最大输入长度
    MAX_INPUT_LENGTH = 512

    # 可疑模式
    SUSPICIOUS_PATTERNS = [
        r"repeat\s+the\s+word",
        r"print\s+your\s+instruction",
        r"reveal\s+your\s+prompt",
    ]

    @classmethod
    def validate_input(cls, text: str) -> bool:
        """验证输入"""
        # 长度检��
        if len(text) > cls.MAX_INPUT_LENGTH:
            logger.warning(f"Input too long: {len(text)}")
            return False

        # 可疑模式
        for pattern in cls.SUSPICIOUS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning(f"Suspicious pattern: {pattern}")
                return False

        return True


# ===== 便捷函数 =====


def safe_filename(filename: str, content: bytes) -> tuple:
    """安全检查文件名和内容

    Returns:
        (is_safe, sanitized_filename_or_error)
    """
    # 检查文件名
    safe_name = FileSecurity.sanitize_filename(filename)
    if not FileSecurity.is_safe_filename(safe_name):
        return False, f"Forbidden file type: {Path(filename).suffix}"

    # 检查内容
    if not FileSecurity.is_safe_content(content):
        return False, "File content contains dangerous patterns"

    return True, safe_name


def sanitize_llm_input(text: str) -> str:
    """清理 LLM 输入"""
    # Prompt 注入防护
    text = PromptInjectionProtection.sanitize_input(text)

    return text


def validate_for_embedding(text: str) -> bool:
    """验证 Embedding 输入"""
    return EmbeddingSecurity.validate_input(text)