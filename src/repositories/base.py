"""通用 CRUD Repository 基类 — 封装常见的数据库操作."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """通用数据访问层基类.

    子类只需指定 model 类即可使用基础 CRUD。
    """

    def __init__(self, session: AsyncSession, model: type[ModelType]) -> None:
        self._session = session
        self._model = model

    async def get_by_id(self, pk: int) -> ModelType | None:
        """根据主键查询."""
        stmt = select(self._model).where(self._model.id == pk)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_ids(self, pks: list[int]) -> list[ModelType]:
        """根据主键列表批量查询."""
        stmt = select(self._model).where(self._model.id.in_(pks))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_all(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        order_by: Any | None = None,
    ) -> list[ModelType]:
        """查询列表（支持分页和排序）."""
        stmt = select(self._model)
        if order_by is not None:
            stmt = stmt.order_by(order_by)
        stmt = stmt.offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count(self, stmt: Select | None = None) -> int:
        """统计记录数.

        注意：如果 stmt 包含 joinedload 等 eager loader，此方法会失败。
        调用方应在添加 joinedload 之前先调用 count()。
        """
        if stmt is None:
            stmt = select(func.count()).select_from(self._model)
        else:
            stmt = select(func.count()).select_from(stmt.subquery())
        result = await self._session.execute(stmt)
        return result.scalar_one() or 0

    async def create(self, obj: ModelType) -> ModelType:
        """创建记录."""
        self._session.add(obj)
        await self._session.flush()
        await self._session.refresh(obj)
        return obj

    async def create_many(self, objs: list[ModelType]) -> list[ModelType]:
        """批量创建记录（避免 N+1 refresh）."""
        self._session.add_all(objs)
        await self._session.flush()
        return objs

    async def update(self, obj: ModelType, **kwargs: Any) -> ModelType:
        """更新记录（局部更新）.

        支持更新为 None、空字符串、False 等 falsy 值。
        只有显式传入的键才会被更新。
        """
        for key, value in kwargs.items():
            if hasattr(obj, key):
                setattr(obj, key, value)
        await self._session.flush()
        await self._session.refresh(obj)
        return obj

    async def delete(self, obj: ModelType) -> None:
        """硬删除记录."""
        await self._session.delete(obj)
        await self._session.flush()

    async def soft_delete(self, obj: ModelType, status_field: str = "status") -> ModelType:
        """软删除（将状态标记为 deleted）."""
        setattr(obj, status_field, "deleted")
        await self._session.flush()
        await self._session.refresh(obj)
        return obj
