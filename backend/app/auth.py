"""
认证中间件
API Key 认证
"""

import hashlib
import time
from typing import Optional

from fastapi import Header, HTTPException, status
from fastapi.security import APIKey

from app.config import get_settings
from app.logging import get_logger


logger = get_logger(__name__)


class APIKeyAuth(APIKey):
    """API Key 认证"""

    name = "X-API-Key"
    auto_error = False

    async def __call__(self, request: Request) -> Optional[str]:
        # 从 header 获取
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            # 从 query 获取
            api_key = request.query_params.get("api_key")

        return api_key


async def verify_api_key(api_key: Optional[str]) -> str:
    """验证 API Key"""
    settings = get_settings()

    # 不需要认证
    if not settings.AUTH_REQUIRED:
        return "anonymous"

    if not api_key:
        if settings.AUTH_REQUIRED:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"error": "Missing API key"},
                headers={"WWW-Authenticate": "ApiKey"},
            )
        return "anonymous"

    # 验证 API Key
    valid_keys = settings.API_KEYS
    if not valid_keys:
        logger.warning("No API keys configured")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Invalid API key"},
        )

    # 支持 hash 后的 key
    api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    if api_key not in valid_keys and api_key_hash not in valid_keys:
        logger.warning(f"Invalid API key attempted: {api_key[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Invalid API key"},
        )

    return api_key


# ===== 便捷函数 =====


async def get_current_user(x_api_key: Optional[str] = Header(None)) -> str:
    """获取当前用户"""
    return await verify_api_key(x_api_key)


# ===== 依赖 =====


async def require_auth(x_api_key: Optional[str] = Header(None)) -> str:
    """需要认证的依赖"""
    return await verify_api_key(x_api_key)


def create_api_key() -> str:
    """创建 API Key"""
    import secrets
    return secrets.token_urlsafe(32)