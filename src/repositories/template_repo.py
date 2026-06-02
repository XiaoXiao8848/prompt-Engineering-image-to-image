"""模板数据访问层."""

from __future__ import annotations

from sqlalchemy import asc, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.domain.template import Template, TemplateVersion
from src.repositories.base import BaseRepository


class TemplateRepository(BaseRepository[Template]):
    """模板 Repository."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Template)

    async def get_by_uuid(self, template_uuid: str) -> Template | None:
        """根据 UUID 查询."""
        stmt = select(Template).where(Template.template_uuid == template_uuid)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_default_by_scene(
        self, scene_id: int, template_type: str
    ) -> Template | None:
        """查询场景的默认模板."""
        stmt = select(Template).where(
            Template.scene_id == scene_id,
            Template.template_type == template_type,
            Template.is_default == True,
            Template.status == "active",
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_scene(
        self,
        scene_id: int,
        *,
        template_type: str | None = None,
        skip: int = 0,
        limit: int = 20,
    ) -> list[Template]:
        """查询场景下的模板列表."""
        stmt = select(Template).where(
            Template.scene_id == scene_id,
            Template.status == "active",
        )
        if template_type:
            stmt = stmt.where(Template.template_type == template_type)

        stmt = stmt.order_by(asc(Template.template_type), desc(Template.created_at))
        stmt = stmt.offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_all_active(
        self,
        *,
        scene_id: int | None = None,
        template_type: str | None = None,
        skip: int = 0,
        limit: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Template], int]:
        """查询所有活跃模板，返回 (列表, 总数)."""
        stmt = select(Template).where(Template.status == "active")

        if scene_id is not None:
            stmt = stmt.where(Template.scene_id == scene_id)
        if template_type:
            stmt = stmt.where(Template.template_type == template_type)

        total = await self.count(stmt)

        sort_column = getattr(Template, sort_by, Template.created_at)
        order_func = desc if sort_order == "desc" else asc
        stmt = stmt.order_by(order_func(sort_column))
        stmt = stmt.offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total


class TemplateVersionRepository(BaseRepository[TemplateVersion]):
    """模板版本 Repository."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, TemplateVersion)

    async def get_latest_version(self, template_id: int) -> int:
        """获取模板最新版本号."""
        from sqlalchemy import func

        stmt = select(func.max(TemplateVersion.version)).where(
            TemplateVersion.template_id == template_id
        )
        result = await self._session.execute(stmt)
        max_version = result.scalar_one_or_none()
        return max_version or 0

    async def list_by_template(
        self, template_id: int, skip: int = 0, limit: int = 20
    ) -> list[TemplateVersion]:
        """查询模板版本历史."""
        stmt = (
            select(TemplateVersion)
            .where(TemplateVersion.template_id == template_id)
            .order_by(desc(TemplateVersion.version))
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
