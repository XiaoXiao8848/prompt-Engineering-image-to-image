"""批量任务 API 路由."""

from __future__ import annotations

from fastapi import APIRouter

from src.api.deps import CurrentUser, DBSession
from src.core.exceptions import NotFoundException, exception_to_http
from src.core.responses import success
from src.repositories.generation_repo import GenerationJobRepository, GenerationResultRepository
from src.schemas.job import JobListQuery, JobProgressOut

router = APIRouter(prefix="/jobs", tags=["批量任务"])


@router.get("/{job_uuid}", response_model=dict)
async def get_job(job_uuid: str, user: CurrentUser, db: DBSession) -> dict:
    """查询任务详情."""
    try:
        repo = GenerationJobRepository(db)
        job = await repo.get_by_uuid(job_uuid)
        if not job or job.user_id != user["id"]:
            raise NotFoundException("任务不存在")

        return success(data={
            "job_uuid": job.job_uuid,
            "product_id": job.product_id,
            "mode": job.mode,
            "scene_ids": job.scene_ids,
            "status": job.status,
            "total_tasks": job.total_tasks,
            "completed_tasks": job.completed_tasks,
            "failed_tasks": job.failed_tasks,
            "llm_model": job.llm_model,
            "llm_temperature": float(job.llm_temperature) if job.llm_temperature else None,
            "webhook_url": job.webhook_url,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "error_message": job.error_message,
            "created_at": job.created_at.isoformat(),
        })
    except NotFoundException as e:
        raise exception_to_http(e) from e


@router.get("/{job_uuid}/progress", response_model=dict)
async def get_job_progress(job_uuid: str, user: CurrentUser, db: DBSession) -> dict:
    """查询任务进度."""
    try:
        repo = GenerationJobRepository(db)
        job = await repo.get_by_uuid(job_uuid)
        if not job or job.user_id != user["id"]:
            raise NotFoundException("任务不存在")

        progress = (
            (job.completed_tasks + job.failed_tasks) / job.total_tasks * 100
            if job.total_tasks > 0 else 0
        )

        return success(data={
            "job_uuid": job.job_uuid,
            "status": job.status,
            "total_tasks": job.total_tasks,
            "completed_tasks": job.completed_tasks,
            "failed_tasks": job.failed_tasks,
            "progress_percent": round(progress, 2),
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "error_message": job.error_message,
        })
    except NotFoundException as e:
        raise exception_to_http(e) from e


@router.get("/{job_uuid}/results", response_model=dict)
async def get_job_results(job_uuid: str, user: CurrentUser, db: DBSession) -> dict:
    """查询任务结果."""
    try:
        job_repo = GenerationJobRepository(db)
        job = await job_repo.get_by_uuid(job_uuid)
        if not job or job.user_id != user["id"]:
            raise NotFoundException("任务不存在")

        result_repo = GenerationResultRepository(db)
        results = await result_repo.list_by_job(job.id)

        return success(data=[
            {
                "result_uuid": r.result_uuid,
                "scene_id": r.scene_id,
                "status": r.status,
                "prompt": r.prompt,
                "negative_prompt": r.negative_prompt,
                "parameters": r.parameters,
                "cache_hit": r.cache_hit,
                "error_message": r.error_message,
                "completed_at": r.completed_at.isoformat() if r.completed_at else None,
            }
            for r in results
        ])
    except NotFoundException as e:
        raise exception_to_http(e) from e


@router.get("", response_model=dict)
async def list_jobs(
    query: JobListQuery = Depends(),  # type: ignore[assignment]
    user: CurrentUser = Depends(),  # type: ignore[assignment]
    db: DBSession = Depends(),  # type: ignore[assignment]
) -> dict:
    """查询任务列表."""
    repo = GenerationJobRepository(db)
    items, total = await repo.list_by_user(
        user_id=user["id"],
        status=query.status,
        page=query.page,
        page_size=query.page_size,
        sort_by=query.sort_by,
        sort_order=query.sort_order,
    )
    total_pages = (total + query.page_size - 1) // query.page_size

    return {
        "code": "SUCCESS",
        "message": "查询成功",
        "data": [
            {
                "job_uuid": j.job_uuid,
                "mode": j.mode,
                "status": j.status,
                "total_tasks": j.total_tasks,
                "completed_tasks": j.completed_tasks,
                "failed_tasks": j.failed_tasks,
                "created_at": j.created_at.isoformat(),
            }
            for j in items
        ],
        "pagination": {
            "page": query.page,
            "page_size": query.page_size,
            "total": total,
            "total_pages": total_pages,
            "has_next": query.page < total_pages,
            "has_prev": query.page > 1,
        },
    }
