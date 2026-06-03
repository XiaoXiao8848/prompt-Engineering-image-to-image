"""生成任务与结果数据访问层."""

from __future__ import annotations

from sqlalchemy import asc, desc, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.domain.generation import GenerationJob, GenerationResult
from src.repositories.base import BaseRepository


class GenerationJobRepository(BaseRepository[GenerationJob]):
    """生成任务 Repository."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, GenerationJob)

    async def get_by_uuid(self, job_uuid: str) -> GenerationJob | None:
        """根据 UUID 查询任务."""
        stmt = select(GenerationJob).where(GenerationJob.job_uuid == job_uuid)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: int,
        *,
        status: str | None = None,
        skip: int = 0,
        limit: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[GenerationJob], int]:
        """查询用户的任务列表，返回 (列表, 总数)."""
        stmt = select(GenerationJob).where(GenerationJob.user_id == user_id)

        if status:
            stmt = stmt.where(GenerationJob.status == status)

        total = await self.count(stmt)

        sort_column = getattr(GenerationJob, sort_by, GenerationJob.created_at)
        order_func = desc if sort_order == "desc" else asc
        stmt = stmt.order_by(order_func(sort_column))
        stmt = stmt.offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total

    async def update_progress(
        self,
        job_id: int,
        completed: int | None = None,
        failed: int | None = None,
        status: str | None = None,
    ) -> None:
        """更新任务进度."""
        values: dict = {}
        if completed is not None:
            values["completed_tasks"] = completed
        if failed is not None:
            values["failed_tasks"] = failed
        if status:
            values["status"] = status

        if values:
            stmt = update(GenerationJob).where(GenerationJob.id == job_id).values(**values)
            await self._session.execute(stmt)
            await self._session.flush()


class GenerationResultRepository(BaseRepository[GenerationResult]):
    """生成结果 Repository."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, GenerationResult)

    async def get_by_uuid(self, result_uuid: str) -> GenerationResult | None:
        """根据 UUID 查询结果."""
        stmt = select(GenerationResult).where(GenerationResult.result_uuid == result_uuid)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_job(self, job_id: int) -> list[GenerationResult]:
        """查询任务的所有结果."""
        stmt = (
            select(GenerationResult)
            .where(GenerationResult.job_id == job_id)
            .order_by(asc(GenerationResult.id))
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_pending_by_job(self, job_id: int) -> list[GenerationResult]:
        """查询任务下所有 pending 状态的结果."""
        stmt = (
            select(GenerationResult)
            .where(
                GenerationResult.job_id == job_id,
                GenerationResult.status == "pending",
            )
            .order_by(asc(GenerationResult.id))
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_by_user_product(
        self, user_id: int, product_id: int, skip: int = 0, limit: int = 20
    ) -> list[GenerationResult]:
        """查询用户某产品下的生成结果."""
        stmt = (
            select(GenerationResult)
            .where(
                GenerationResult.user_id == user_id,
                GenerationResult.product_id == product_id,
            )
            .order_by(desc(GenerationResult.created_at))
            .offset(skip)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
