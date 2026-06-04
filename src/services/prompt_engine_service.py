"""提示词生成核心服务 — 单条同步 + 批量异步任务提交."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.core.exceptions import NotFoundException, QuotaExceededException
from src.engine.llm_engine import LLMPromptEngine
from src.engine.template_engine import TemplatePromptEngine
from src.models.domain.generation import GenerationJob, GenerationResult
from src.models.domain.product import Product
from src.models.domain.scene import Scene
from src.repositories.generation_repo import GenerationJobRepository, GenerationResultRepository
from src.repositories.product_repo import ProductRepository
from src.repositories.scene_repo import SceneRepository
from src.repositories.template_repo import TemplateRepository
from src.repositories.user_repo import UserRepository
from src.schemas.prompt import (
    BatchGenerateRequest,
    BatchGenerateResponse,
    GeneratePromptRequest,
    GeneratedPromptOut,
)
from src.services.cache_service import CacheService


class PromptEngineService:
    """提示词生成服务."""

    def __init__(
        self,
        session: AsyncSession,
        cache_service: CacheService,
    ) -> None:
        self._session = session
        self._cache = cache_service
        self._product_repo = ProductRepository(session)
        self._scene_repo = SceneRepository(session)
        self._template_repo = TemplateRepository(session)
        self._job_repo = GenerationJobRepository(session)
        self._result_repo = GenerationResultRepository(session)

    async def _check_and_deduct_quota(self, user_id: int, amount: int = 1) -> None:
        """检查并扣减用户配额."""
        user_repo = UserRepository(self._session)
        user = await user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundException("用户不存在")
        if user.quota_used_today + amount > user.quota_daily:
            raise QuotaExceededException(
                f"今日配额已用完 ({user.quota_used_today}/{user.quota_daily})"
            )
        await user_repo.update(user, quota_used_today=user.quota_used_today + amount)

    async def generate_single(
        self,
        user_id: int,
        data: GeneratePromptRequest,
    ) -> GeneratedPromptOut:
        """单条同步生成提示词."""
        # 0. 检查配额
        await self._check_and_deduct_quota(user_id, amount=1)

        # 1. 加载产品
        product = await self._product_repo.get_by_uuid(data.product_uuid)
        if not product or product.user_id != user_id:
            raise NotFoundException("产品不存在")

        # 2. 加载场景
        scene = await self._scene_repo.get_by_scene_id(data.scene_id)
        if not scene:
            raise NotFoundException("场景不存在")

        # 3. LLM 模式检查缓存
        if data.mode == "llm" and data.use_cache:
            cached = await self._cache.get_llm_result(
                product_id=product.product_uuid,
                scene_id=scene.scene_id,
                mode=data.mode,
                model=data.llm_model or settings.llm_model,
                temperature=data.llm_temperature or settings.llm_temperature,
            )
            if cached:
                cached.cache_hit = True
                return cached

        # 4. 准备数据
        product_data = self._product_to_dict(product)
        scene_data = self._scene_to_dict(scene)

        # 5. 根据模式选择引擎并生成
        if data.mode == "template":
            engine = TemplatePromptEngine(self._template_repo)
        else:
            engine = LLMPromptEngine(
                model=data.llm_model,
                temperature=data.llm_temperature,
            )

        result = await engine.generate(product_data, scene_data)

        # 6. LLM 模式写入缓存
        if data.mode == "llm" and data.use_cache:
            await self._cache.set_llm_result(
                product_id=product.product_uuid,
                scene_id=scene.scene_id,
                mode=data.mode,
                model=data.llm_model or settings.llm_model,
                temperature=data.llm_temperature or settings.llm_temperature,
                result=result,
            )

        # 7. 保存结果到数据库
        gen_result = GenerationResult(
            user_id=user_id,
            product_id=product.id,
            scene_id=scene.id,
            job_id=0,  # 单条生成无 job
            status="success",
            mode=data.mode,
            prompt=result.prompt,
            negative_prompt=result.negative_prompt,
            parameters=result.parameters,
            cache_hit=result.cache_hit,
        )
        await self._result_repo.create(gen_result)

        return result

    async def submit_batch_job(
        self,
        user_id: int,
        data: BatchGenerateRequest,
    ) -> BatchGenerateResponse:
        """提交批量异步任务."""
        # 0. 检查配额
        await self._check_and_deduct_quota(user_id, amount=len(data.scene_ids))

        # 1. 加载产品
        product = await self._product_repo.get_by_uuid(data.product_uuid)
        if not product or product.user_id != user_id:
            raise NotFoundException("产品不存在")

        # 2. 加载场景
        scenes = await self._scene_repo.list_by_ids(data.scene_ids)
        found_ids = {s.scene_id for s in scenes}
        invalid = [sid for sid in data.scene_ids if sid not in found_ids]
        if invalid:
            raise NotFoundException(f"以下场景不存在: {', '.join(invalid)}")

        # 3. 创建 Job
        job = GenerationJob(
            user_id=user_id,
            product_id=product.id,
            mode=data.mode,
            scene_ids=data.scene_ids,
            status="pending",
            total_tasks=len(scenes),
            completed_tasks=0,
            failed_tasks=0,
            llm_model=data.llm_model or settings.llm_model,
            llm_temperature=data.llm_temperature or settings.llm_temperature,
            webhook_url=data.webhook_url,
        )
        await self._job_repo.create(job)

        # 4. 创建子任务
        for scene in scenes:
            result = GenerationResult(
                job_id=job.id,
                user_id=user_id,
                product_id=product.id,
                scene_id=scene.id,
                status="pending",
                mode=data.mode,
            )
            await self._result_repo.create(result)

        # 5. 发送 Celery 任务到队列
        from src.tasks.generation_tasks import process_generation_job
        process_generation_job.delay(job.id)

        return BatchGenerateResponse(
            job_uuid=job.job_uuid,
            status=job.status,
            total_tasks=job.total_tasks,
        )

    @staticmethod
    def _product_to_dict(product: Product) -> dict[str, Any]:
        """将 Product ORM 对象转换为模板变量字典."""
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

    @staticmethod
    def _scene_to_dict(scene: Scene) -> dict[str, Any]:
        """将 Scene ORM 对象转换为模板变量字典."""
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
