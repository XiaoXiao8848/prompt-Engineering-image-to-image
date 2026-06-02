"""Celery 应用配置."""

from __future__ import annotations

from celery import Celery

from src.config import settings

celery_app = Celery(
    "prompt_engine",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["src.tasks.generation_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 分钟硬限制
    task_soft_time_limit=240,  # 4 分钟软限制
    worker_prefetch_multiplier=1,  # 公平调度
    result_expires=3600,  # 结果保留 1 小时
)
