"""场景数据访问层."""

from __future__ import annotations

from sqlalchemy import asc, desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.models.domain.scene import Scene, SceneCategory
from src.repositories.base import BaseRepository


class SceneCategoryRepository(BaseRepository[SceneCategory]):
    """场景分类 Repository."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, SceneCategory)

    async def list_all_ordered(self) -> list[SceneCategory]:
        """查询所有分类（按排序字段）."""
        stmt = select(SceneCategory).order_by(asc(SceneCategory.sort_order))
        result = await self._session.execute(stmt)
        return list(result.scalars().all())


class SceneRepository(BaseRepository[Scene]):
    """场景 Repository."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Scene)

    async def get_by_scene_id(self, scene_id: str) -> Scene | None:
        """根据场景标识查询."""
        stmt = select(Scene).where(Scene.scene_id == scene_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_uuid(self, scene_uuid: str) -> Scene | None:
        """根据 UUID 查询（含分类信息）."""
        stmt = select(Scene).options(
            joinedload(Scene.category)
        ).where(Scene.scene_uuid == scene_uuid)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_scenes(
        self,
        *,
        category_id: int | None = None,
        is_public: bool | None = None,
        status: str | None = None,
        keyword: str | None = None,
        skip: int = 0,
        limit: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Scene], int]:
        """查询场景列表，返回 (列表, 总数)."""
        # 先构建基础查询（不带 joinedload，用于 count）
        base_stmt = select(Scene)

        if category_id is not None:
            base_stmt = base_stmt.where(Scene.category_id == category_id)
        if is_public is not None:
            base_stmt = base_stmt.where(Scene.is_public == is_public)
        if status:
            base_stmt = base_stmt.where(Scene.status == status)
        else:
            base_stmt = base_stmt.where(Scene.status != "deleted")
        if keyword:
            base_stmt = base_stmt.where(
                Scene.name.contains(keyword)
                | Scene.scene_id.contains(keyword)
            )

        # 计算总数（在添加 joinedload 之前）
        total = await self.count(base_stmt)

        # 添加排序、joinedload 和分页
        sort_column = getattr(Scene, sort_by, Scene.created_at)
        order_func = desc if sort_order == "desc" else asc
        stmt = base_stmt.order_by(order_func(sort_column)).options(
            joinedload(Scene.category)
        ).offset(skip).limit(limit)

        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total

    async def list_by_ids(self, scene_ids: list[str]) -> list[Scene]:
        """根据场景标识列表查询."""
        stmt = select(Scene).where(
            Scene.scene_id.in_(scene_ids),
            Scene.status == "active",
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
