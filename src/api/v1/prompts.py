"""提示词生成 API 路由."""

from __future__ import annotations

from fastapi import APIRouter

from src.api.deps import CurrentUserOrApiKey, DBSession, RedisDep
from src.core.exceptions import NotFoundException, QuotaExceededException, ValidationException, exception_to_http
from src.core.responses import success
from src.schemas.prompt import (
    BatchGenerateRequest,
    GeneratePromptRequest,
    GeneratedPromptOut,
    PromptWorkflowOut,
)
from src.services.cache_service import CacheService
from src.services.prompt_engine_service import PromptEngineService

router = APIRouter(prefix="/prompts", tags=["提示词生成"])


@router.post("/generate", response_model=dict)
async def generate_prompt(
    data: GeneratePromptRequest,
    user: CurrentUserOrApiKey,
    db: DBSession,
    redis: RedisDep,
) -> dict:
    """单条同步生成提示词."""
    try:
        cache_service = CacheService(redis)
        service = PromptEngineService(db, cache_service)
        result = await service.generate_single(user_id=user["id"], data=data)
        return success(data=result.model_dump(), message="生成成功")
    except (NotFoundException, QuotaExceededException, ValidationException) as e:
        raise exception_to_http(e) from e


@router.post("/generate/batch", response_model=dict)
async def batch_generate(
    data: BatchGenerateRequest,
    user: CurrentUserOrApiKey,
    db: DBSession,
    redis: RedisDep,
) -> dict:
    """提交批量异步生成任务."""
    try:
        cache_service = CacheService(redis)
        service = PromptEngineService(db, cache_service)
        job = await service.submit_batch_job(user_id=user["id"], data=data)
        return success(
            data={
                "job_uuid": job.job_uuid,
                "status": job.status,
                "total_tasks": job.total_tasks,
                "message": "批量任务已提交",
            },
            message="提交成功",
        )
    except (NotFoundException, ValidationException) as e:
        raise exception_to_http(e) from e


@router.post("/generate/workflow", response_model=dict)
async def generate_workflow(
    data: GeneratePromptRequest,
    user: CurrentUserOrApiKey,
    db: DBSession,
    redis: RedisDep,
) -> dict:
    """生成 ComfyUI / SD WebUI 兼容格式."""
    try:
        cache_service = CacheService(redis)
        service = PromptEngineService(db, cache_service)
        result = await service.generate_single(user_id=user["id"], data=data)
        workflow = PromptWorkflowOut(
            scene_id=result.scene_id,
            scene_name=result.scene_name,
            positive=result.prompt,
            negative=result.negative_prompt,
            img2img_params=result.parameters,
        )
        return success(data=workflow.model_dump(), message="生成成功")
    except (NotFoundException, QuotaExceededException, ValidationException) as e:
        raise exception_to_http(e) from e
