"""FastAPI 依赖注入 — 数据库会话、认证用户、Redis 客户端等."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Header, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import AuthenticationException, AuthorizationException
from src.core.responses import error
from src.core.security import decode_token
from src.infrastructure.database import get_db_session
from src.infrastructure.redis_client import get_redis, RedisCache
from src.repositories.user_repo import UserRepository

# OAuth2 密码流（用于 Swagger UI 测试）
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_db() -> AsyncSession:
    """获取数据库会话（兼容命名）."""
    async for session in get_db_session():
        yield session


DBSession = Annotated[AsyncSession, Depends(get_db)]


async def get_redis_cache() -> RedisCache:
    """获取 Redis 缓存实例."""
    return RedisCache(get_redis())


RedisDep = Annotated[RedisCache, Depends(get_redis_cache)]


async def get_current_user(
    request: Request,
    db: DBSession,
    authorization: Annotated[str | None, Header()] = None,
    token: Annotated[str | None, Depends(oauth2_scheme)] = None,
) -> dict:
    """获取当前认证用户.

    支持两种方式：
    1. Bearer Token (Authorization: Bearer <token>)
    2. OAuth2 Password Flow (Swagger UI)
    """
    # 优先从 Header 提取 Token
    auth_token = token
    if authorization and not auth_token:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            auth_token = parts[1]

    if not auth_token:
        raise AuthenticationException("未提供认证令牌")

    payload = decode_token(auth_token)
    if not payload:
        raise AuthenticationException("令牌无效或已过期")

    token_type = payload.get("type")
    if token_type != "access":
        raise AuthenticationException("令牌类型错误")

    user_id = payload.get("sub")
    if not user_id:
        raise AuthenticationException("令牌中未包含用户信息")

    # 查询用户
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(int(user_id))
    if not user:
        raise AuthenticationException("用户不存在")

    if user.status != "active":
        raise AuthenticationException("用户已被禁用")

    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "quota_daily": user.quota_daily,
        "quota_used_today": user.quota_used_today,
    }


CurrentUser = Annotated[dict, Depends(get_current_user)]


async def get_current_active_user(user: CurrentUser) -> dict:
    """确保用户处于活跃状态."""
    if user.get("status") == "banned":
        raise AuthorizationException("用户已被封禁")
    return user


ActiveUser = Annotated[dict, Depends(get_current_active_user)]


async def require_admin(user: CurrentUser) -> dict:
    """要求管理员权限."""
    if user.get("role") != "admin":
        raise AuthorizationException("需要管理员权限")
    return user


AdminUser = Annotated[dict, Depends(require_admin)]


async def get_optional_user(
    request: Request,
    db: DBSession,
    authorization: Annotated[str | None, Header()] = None,
) -> dict | None:
    """可选认证 — 未登录返回 None，不抛异常."""
    if not authorization:
        return None
    try:
        return await get_current_user(request, db, authorization)
    except AuthenticationException:
        return None


OptionalUser = Annotated[dict | None, Depends(get_optional_user)]
