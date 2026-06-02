"""批量任务相关 Pydantic Schema."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from src.schemas.base import BaseSchema, IDMixin, ListQueryParams, TimestampMixin
from src.schemas.prompt import GeneratedPromptOut


class JobProgressOut(BaseSchema):
    """任务进度响应."""

    job_uuid: str
    status: str
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    progress_percent: float = Field(description="进度百分比")
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None


class JobResultOut(BaseSchema):
    """任务结果响应."""

    result_uuid: str
    scene_id: str
    scene_name: str
    status: str
    prompt: str | None
    negative_prompt: str | None
    parameters: dict[str, Any] | None
    cache_hit: bool
    error_message: str | None
    completed_at: datetime | None


class JobDetailOut(IDMixin, TimestampMixin):
    """任务详情响应."""

    job_uuid: str
    product_id: int
    mode: str
    scene_ids: list[str]
    status: str
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    llm_model: str | None
    llm_temperature: float
    webhook_url: str | None
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None


class JobListQuery(ListQueryParams):
    """任务列表查询参数."""

    status: str | None = Field(default=None, description="状态筛选")
    product_uuid: str | None = Field(default=None, description="产品筛选")
