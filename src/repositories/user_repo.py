"""用户数据访问层."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.domain.user import ApiKey, User
from src.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """用户 Repository."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)

    async def get_by_username(self, username: str) -> User | None:
        """根据用户名查询."""
        stmt = select(User).where(User.username == username)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """根据邮箱查询."""
        stmt = select(User).where(User.email == email)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def username_exists(self, username: str) -> bool:
        """检查用户名是否已存在."""
        stmt = select(User.id).where(User.username == username)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def email_exists(self, email: str) -> bool:
        """检查邮箱是否已存在."""
        stmt = select(User.id).where(User.email == email)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None


class ApiKeyRepository(BaseRepository[ApiKey]):
    """API Key Repository."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, ApiKey)

    async def get_by_hash(self, key_hash: str) -> ApiKey | None:
        """根据哈希查询."""
        stmt = select(ApiKey).where(ApiKey.key_hash == key_hash)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: int) -> list[ApiKey]:
        """查询用户的所有 API Key."""
        stmt = select(ApiKey).where(ApiKey.user_id == user_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
