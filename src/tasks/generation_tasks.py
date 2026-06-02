"""Celery 异步生成任务 — 批量 LLM 调用.

注意：Celery Worker 是同步环境，我们通过创建新事件循环来运行 async SQLAlchemy 代码。
生产环境建议考虑 arq 或 RQ 等原生支持 async 的任务队列。
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from asgiref.sync import async_to_sync
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config import settings
from src.engine.llm_engine import LLMPromptEngine
from src.engine.template_engine import TemplatePromptEngine
from src.models.domain.generation import GenerationJob, GenerationResult
from src.models.domain.product import Product
from src.models.domain.scene import Scene
from src.repositories.generation_repo import GenerationJobRepository, GenerationResultRepository
from src.repositories.product_repo import ProductRepository
from src.repositories.scene_repo import SceneRepository
from src.repositories.template_repo import TemplateRepository
from src.tasks.celery_app import celery_app

# Celery Worker 专用异步引擎
_celery_engine = create_async_engine(settings.database_url, pool_pre_ping=True, pool_size=5)
AsyncSessionLocal = async_sessionmaker(_celery_engine, class_=AsyncSession, expire_on_commit=False)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=10)
def execute_single_generation(self, result_id: int) -> dict:
    """执行单条生成任务.

    Celery 是同步的，我们用 async_to_sync 包装异步逻辑。
    """
    try:
        async_to_sync(_async_execute_single)(result_id, self.request.id)
        return {"status": "success", "result_id": result_id}
    except Exception as exc:
        # 指数退避重试
        countdown = (2 ** self.request.retries) * 5
        raise self.retry(exc=exc, countdown=countdown)


async def _async_execute_single(result_id: int, task_id: str) -> None:
    """异步执行单条生成."""
    async with AsyncSessionLocal() as session:
        result_repo = GenerationResultRepository(session)
        job_repo = GenerationJobRepository(session)
        product_repo = ProductRepository(session)
        scene_repo = SceneRepository(session)
        template_repo = TemplateRepository(session)

        # 获取结果记录（同时加载关联的 job）
        result = await result_repo.get_by_id(result_id)
        if not result:
            return

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

            # 获取 job 的 LLM 模型配置（避免懒加载）
            llm_model = None
            if result.job_id:
                job = await job_repo.get_by_id(result.job_id)
                if job:
                    llm_model = job.llm_model

            # 执行生成
            if result.mode == "template":
                engine = TemplatePromptEngine(template_repo)
            else:
                engine = LLMPromptEngine(model=llm_model)

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
                )
            )
            await session.commit()
            raise


async def _update_job_progress(
    session: AsyncSession, job_repo: GenerationJobRepository, job_id: int
) -> None:
    """更新任务进度."""
    # 统计成功和失败数量
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
            new_status = (
                "completed"
                if failed == 0
                else "partial"
                if completed > 0
                else "failed"
            )
        else:
            new_status = "running"

        await session.execute(
            update(GenerationJob)
            .where(GenerationJob.id == job_id)
            .values(
                completed_tasks=completed,
                failed_tasks=failed,
                status=new_status,
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
