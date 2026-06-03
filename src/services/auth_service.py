"""认证服务层 — 注册、登录、Token 管理."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import AlreadyExistsException, AuthenticationException
from src.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    hash_api_key,
    verify_password,
)
from src.models.domain.user import ApiKey, User
from src.repositories.user_repo import ApiKeyRepository, UserRepository


class AuthService:
    """认证服务."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._user_repo = UserRepository(session)
        self._api_key_repo = ApiKeyRepository(session)

    async def register(
        self,
        username: str,
        email: str,
        password: str,
        display_name: str | None = None,
    ) -> User:
        """用户注册."""
        if await self._user_repo.username_exists(username):
            raise AlreadyExistsException(f"用户名 '{username}' 已被使用")
        if await self._user_repo.email_exists(email):
            raise AlreadyExistsException(f"邮箱 '{email}' 已被注册")

        user = User(
            username=username,
            email=email,
            password_hash=get_password_hash(password),
            display_name=display_name or username,
            role="user",
            status="active",
        )
        await self._user_repo.create(user)
        return user

    async def login(self, username: str, password: str) -> dict:
        """用户登录，返回 Token."""
        user = await self._user_repo.get_by_username(username)
        if not user:
            # 尝试用邮箱登录
            user = await self._user_repo.get_by_email(username)

        if not user or not verify_password(password, user.password_hash):
            raise AuthenticationException("用户名或密码错误")

        if user.status != "active":
            raise AuthenticationException("用户已被禁用")

        access_token = create_access_token(
            subject=user.id,
            extra_claims={"username": user.username, "role": user.role},
        )
        refresh_token = create_refresh_token(subject=user.id)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 3600,
        }

    async def refresh_token(self, refresh_token: str) -> dict:
        """刷新 Access Token."""
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise AuthenticationException("刷新令牌无效")

        user_id = int(payload["sub"])
        user = await self._user_repo.get_by_id(user_id)
        if not user or user.status != "active":
            raise AuthenticationException("用户不存在或已被禁用")

        access_token = create_access_token(
            subject=user.id,
            extra_claims={"username": user.username, "role": user.role},
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,  # 复用原 refresh token
            "token_type": "bearer",
            "expires_in": 3600,
        }

    async def update_user(
        self,
        user_id: int,
        display_name: str | None = None,
        avatar_url: str | None = None,
    ) -> User:
        """更新用户信息."""
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise AuthenticationException("用户不存在")

        update_data: dict[str, Any] = {}
        if display_name is not None:
            update_data["display_name"] = display_name
        if avatar_url is not None:
            update_data["avatar_url"] = avatar_url

        if update_data:
            await self._user_repo.update(user, **update_data)
        return user

    async def create_api_key(
        self,
        user_id: int,
        name: str,
        permissions: list[str] | None = None,
        rate_limit: int | None = None,
        expires_at: datetime | None = None,
    ) -> tuple[ApiKey, str]:
        """创建 API Key，返回 (ApiKey对象, 原始Key).

        注意：原始 Key 仅返回一次，需立即保存给客户端。
        """
        from src.core.security import generate_api_key

        raw_key = generate_api_key()
        key_hash = hash_api_key(raw_key)
        key_prefix = raw_key[:10]

        api_key = ApiKey(
            user_id=user_id,
            key_hash=key_hash,
            key_prefix=key_prefix,
            name=name,
            permissions=permissions or ["prompt:read", "prompt:write"],
            rate_limit=rate_limit or 60,
            expires_at=expires_at,
        )
        await self._api_key_repo.create(api_key)
        return api_key, raw_key
