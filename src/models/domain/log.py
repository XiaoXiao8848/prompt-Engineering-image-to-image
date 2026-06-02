"""日志与审计相关 ORM 模型."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import JSON, Enum, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.infrastructure.database import Base


class PromptHistory(Base):
    """提示词历史去重表 — 用于相似推荐、版本对比."""

    __tablename__ = "prompt_histories"
    __table_args__ = (
        Index("idx_user_scene", "user_id", "scene_id"),
        Index("idx_last_used", "last_used_at"),
        {"comment": "提示词历史去重表"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
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
    prompt_hash: Mapped[str] = mapped_column(
        String(64), nullable=False, unique=True, comment="提示词 SHA256 哈希"
    )
    prompt: Mapped[str] = mapped_column(Text, nullable=False, comment="提示词全文")
    negative_prompt: Mapped[str | None] = mapped_column(Text, comment="负向提示词")
    parameters: Mapped[dict | None] = mapped_column(JSON, comment="参数")
    generation_count: Mapped[int] = mapped_column(default=1, comment="被生成次数")
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(3), comment="最后使用时间")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(3), default=lambda: datetime.now(timezone.utc)
    )


class RateLimitLog(Base):
    """限流日志表."""

    __tablename__ = "rate_limit_logs"
    __table_args__ = (
        Index("idx_user_time", "user_id", "created_at"),
        Index("idx_ip_time", "client_ip", "created_at"),
        {"comment": "限流日志"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), comment="用户 ID")
    api_key_id: Mapped[int | None] = mapped_column(ForeignKey("api_keys.id"), comment="API Key ID")
    endpoint: Mapped[str] = mapped_column(String(200), nullable=False, comment="请求端点")
    request_method: Mapped[str] = mapped_column(String(10), nullable=False)
    client_ip: Mapped[str] = mapped_column(String(45), nullable=False, comment="客户端 IP")
    result: Mapped[str] = mapped_column(
        Enum("allowed", "blocked", name="rate_limit_result"),
        nullable=False,
        comment="限流结果",
    )
    blocked_reason: Mapped[str | None] = mapped_column(String(200), comment="拦截原因")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(3), default=lambda: datetime.now(timezone.utc)
    )


class OperationLog(Base):
    """操作审计日志表."""

    __tablename__ = "operation_logs"
    __table_args__ = (
        Index("idx_user_action", "user_id", "action"),
        Index("idx_resource", "resource_type", "resource_id"),
        Index("idx_created", "created_at"),
        {"comment": "操作审计日志"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), comment="操作用户")
    action: Mapped[str] = mapped_column(String(50), nullable=False, comment="操作类型")
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="资源类型")
    resource_id: Mapped[str | None] = mapped_column(String(100), comment="资源 ID")
    details: Mapped[dict | None] = mapped_column(JSON, comment="操作详情")
    client_ip: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(3), default=lambda: datetime.now(timezone.utc)
    )
