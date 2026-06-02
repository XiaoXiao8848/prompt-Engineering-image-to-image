"""Celery 异步生成任务 — 批量 LLM 调用."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.config import settings
from src.engine.llm_engine import LLMPromptEngine
from src.engine.template_engine import TemplatePromptEngine
from src.infrastructure.database import Base
from src.models.domain.generation import GenerationJob, GenerationResult
from src.models.domain.product import Product
from src.models.domain.scene import Scene
from src.repositories.generation_repo import GenerationJobRepository, GenerationResultRepository
from src.repositories.product_repo import ProductRepository
from src.repositories.scene_repo import SceneRepository
from src.repositories.template_repo import TemplateRepository
from src.tasks.celery_app import celery_app


# 创建同步引擎用于 Celery Worker（Celery 是同步的）
# 注意：实际生产环境中，Celery Worker 应使用 async_to_sync 或异步支持
engine = create_async_engine(settings.database_url, pool_pre_ping=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def _get_session():
    """获取数据库会话."""
    async with AsyncSessionLocal() as session:
        yield session


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def execute_single_generation(self, result_id: int):
    """执行单条生成任务.

    注意：此为同步包装，实际逻辑在 _async_execute 中。
    """
    asyncio.run(_async_execute_single(result_id, self.request.id))


async def _async_execute_single(result_id: int, task_id: str) -> None:
    """异步执行单条生成."""
    async with AsyncSessionLocal() as session:
        result_repo = GenerationResultRepository(session)
        job_repo = GenerationJobRepository(session)
        product_repo = ProductRepository(session)
        scene_repo = SceneRepository(session)
        template_repo = TemplateRepository(session)

        # 获取结果记录
        result = await result_repo.get_by_id(result_id)
        if not result:
            return

        # 获取分布式锁
        # TODO: Redis 锁（需要同步 Redis 客户端）

        # 更新状态为 running
        await session.execute(
            update(GenerationResult)
            .where(GenerationResult.id == result_id)
            .values(status="running", started_at=datetime.now(timezone.utc))
        )
        await session.commit()

        try:
            # 加载产品和场景
            product = await product_repo.get_by_id(result.product_id)
            scene = await scene_repo.get_by_id(result.scene_id)

            if not product or not scene:
                raise ValueError("产品或场景不存在")

            # 准备数据
            product_data = _product_to_dict(product)
            scene_data = _scene_to_dict(scene)

            # 执行生成
            if result.mode == "template":
                engine = TemplatePromptEngine(template_repo)
            else:
                engine = LLMPromptEngine(model=result.job.llm_model if result.job else None)

            generated = await engine.generate(product_data, scene_data)

            # 保存结果
            await session.execute(
                update(GenerationResult)
                .where(GenerationResult.id == result_id)
                .values(
                    status="success",
                    prompt=generated.prompt,
                    negative_prompt=generated.negative_prompt,
                    parameters=generated.parameters,
                    completed_at=datetime.now(timezone.utc),
                )
            )

            # 更新 Job 进度
            if result.job_id:
                await _update_job_progress(session, job_repo, result.job_id)

            await session.commit()

        except Exception as exc:
            await session.execute(
                update(GenerationResult)
                .where(GenerationResult.id == result_id)
                .values(
                    status="failed",
                    error_message=str(exc)[:500],
                    retry_count=GenerationResult.retry_count + 1,
                )
            )
            await session.commit()
            raise


async def _update_job_progress(
    session: AsyncSession, job_repo: GenerationJobRepository, job_id: int
) -> None:
    """更新任务进度."""
    results = await session.execute(
        update(GenerationResult)
        .where(GenerationResult.job_id == job_id)
        .values(status=GenerationResult.status)
    )

    # 统计
    from sqlalchemy import func, select

    stmt = select(
        func.count().filter(GenerationResult.status == "success"),
        func.count().filter(GenerationResult.status == "failed"),
    ).where(GenerationResult.job_id == job_id)

    result = await session.execute(stmt)
    completed, failed = result.one()

    job = await job_repo.get_by_id(job_id)
    if job:
        total = job.total_tasks
        if completed + failed >= total:
            status = "completed" if failed == 0 else "partial" if completed > 0 else "failed"
        else:
            status = "running"

        await session.execute(
            update(GenerationJob)
            .where(GenerationJob.id == job_id)
            .values(
                completed_tasks=completed,
                failed_tasks=failed,
                status=status,
                completed_at=datetime.now(timezone.utc) if completed + failed >= total else None,
            )
        )


def _product_to_dict(product: Product) -> dict:
    return {
        "product_id": product.product_id,
        "product_name": product.product_name,
        "brand": product.brand or "",
        "material": product.material or "",
        "shape": product.shape or "",
        "color": product.color or "",
        "size": product.size or "",
        "lock_tags": product.lock_tags.strip(),
        "selling_points": ", ".join(product.selling_points or []),
        "material_keywords": ", ".join(product.material_keywords or []),
        "brand_tone": product.brand_tone or "",
        "reference_description": (product.reference_image or {}).get("description", ""),
        "reference_angle": (product.reference_image or {}).get("angle", ""),
        "reference_lighting": (product.reference_image or {}).get("lighting", ""),
    }


def _scene_to_dict(scene: Scene) -> dict:
    return {
        "db_id": scene.id,
        "scene_id": scene.scene_id,
        "scene_name": scene.name,
        "scene_description": scene.description or "",
        "lighting": scene.lighting or "",
        "background": scene.background or "",
        "props": ", ".join(scene.props or []),
        "atmosphere": scene.atmosphere or "",
        "scene_keywords": ", ".join(scene.keywords or []),
    }
