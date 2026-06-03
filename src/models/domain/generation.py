"""生成任务与结果 ORM 模型."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database import Base


class GenerationJob(Base):
    """生成任务表 — 支持批量任务."""

    __tablename__ = "generation_jobs"
    __table_args__ = (
        Index("idx_job_user_status", "user_id", "status"),
        Index("idx_job_status_created", "status", "created_at"),
        Index("idx_job_uuid", "job_uuid"),
        {"comment": "生成任务表"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    job_uuid: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        unique=True,
        default=lambda: str(uuid.uuid4()),
        comment="任务 UUID",
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="提交用户",
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        comment="关联产品",
    )
    mode: Mapped[str] = mapped_column(
        Enum("template", "llm", name="generation_mode"),
        nullable=False,
        comment="生成模式",
    )
    scene_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, comment="目标场景 ID 列表")
    status: Mapped[str] = mapped_column(
        Enum("pending", "queued", "running", "partial", "completed", "failed", "cancelled", name="job_status"),
        default="pending",
        comment="任务状态",
    )
    total_tasks: Mapped[int] = mapped_column(Integer, default=0, comment="总子任务数")
    completed_tasks: Mapped[int] = mapped_column(Integer, default=0, comment="已完成子任务数")
    failed_tasks: Mapped[int] = mapped_column(Integer, default=0, comment="失败子任务数")
    llm_model: Mapped[str | None] = mapped_column(String(50), comment="使用的 LLM 模型")
    llm_temperature: Mapped[float] = mapped_column(default=0.70, comment="温度参数")
    parameters: Mapped[dict | None] = mapped_column(JSON, comment="额外参数")
    webhook_url: Mapped[str | None] = mapped_column(String(500), comment="完成回调 URL")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(3), comment="开始时间")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(3), comment="完成时间")
    error_message: Mapped[str | None] = mapped_column(Text, comment="错误信息")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(3), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(3),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class GenerationResult(Base):
    """生成结果表 — 原子级."""

    __tablename__ = "generation_results"
    __table_args__ = (
        Index("idx_job", "job_id"),
        Index("idx_user_product", "user_id", "product_id"),
        Index("idx_scene", "scene_id"),
        Index("idx_status", "status"),
        {"comment": "生成结果表"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    result_uuid: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        unique=True,
        default=lambda: str(uuid.uuid4()),
        comment="结果 UUID",
    )
    job_id: Mapped[int] = mapped_column(
        ForeignKey("generation_jobs.id", ondelete="CASCADE"),
        nullable=False,
        comment="所属任务",
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="所属用户",
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        comment="关联产品",
    )
    scene_id: Mapped[int] = mapped_column(
        ForeignKey("scenes.id", ondelete="CASCADE"),
        nullable=False,
        comment="关联场景",
    )
    status: Mapped[str] = mapped_column(
        Enum("pending", "running", "success", "failed", "cached", name="result_status"),
        default="pending",
        comment="子任务状态",
    )
    mode: Mapped[str] = mapped_column(
        Enum("template", "llm", name="generation_mode"),
        nullable=False,
    )
    prompt: Mapped[str | None] = mapped_column(Text, comment="正向提示词")
    negative_prompt: Mapped[str | None] = mapped_column(Text, comment="负向提示词")
    parameters: Mapped[dict | None] = mapped_column(JSON, comment="推荐参数")
    llm_raw_response: Mapped[str | None] = mapped_column(Text, comment="LLM 原始响应")
    cache_hit: Mapped[bool] = mapped_column(default=False, comment="是否命中缓存")
    error_message: Mapped[str | None] = mapped_column(Text, comment="错误信息")
    retry_count: Mapped[int] = mapped_column(Integer, default=0, comment="重试次数")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(3), comment="开始时间")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(3), comment="完成时间")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(3), default=lambda: datetime.now(timezone.utc)
    )
