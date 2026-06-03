"""场景定义 ORM 模型."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database import Base


class SceneCategory(Base):
    """场景分类表."""

    __tablename__ = "scene_categories"
    __table_args__ = ({"comment": "场景分类表"},)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="分类名称")
    description: Mapped[str | None] = mapped_column(String(200), comment="描述")
    sort_order: Mapped[int] = mapped_column(default=0, comment="排序")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(3), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    scenes: Mapped[list["Scene"]] = relationship("Scene", back_populates="category")


class Scene(Base):
    """场景定义表."""

    __tablename__ = "scenes"
    __table_args__ = (
        UniqueConstraint("scene_id", name="uk_scene_id"),
        Index("idx_category", "category_id"),
        Index("idx_status_public", "status", "is_public"),
        {"comment": "场景定义表"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    scene_uuid: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        unique=True,
        default=lambda: str(uuid.uuid4()),
        comment="业务 UUID",
    )
    scene_id: Mapped[str] = mapped_column(String(64), nullable=False, comment="场景标识")
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="场景名称")
    description: Mapped[str | None] = mapped_column(Text, comment="场景描述")
    lighting: Mapped[str | None] = mapped_column(Text, comment="光线描述")
    background: Mapped[str | None] = mapped_column(Text, comment="背景描述")
    props: Mapped[list[str] | None] = mapped_column(JSON, comment="道具列表")
    atmosphere: Mapped[str | None] = mapped_column(String(200), comment="氛围")
    keywords: Mapped[list[str] | None] = mapped_column(JSON, comment="关键词列表")
    category_id: Mapped[int | None] = mapped_column(
        ForeignKey("scene_categories.id"), comment="所属分类"
    )
    is_builtin: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否内置场景")
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否公开")
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), comment="创建者"
    )
    status: Mapped[str] = mapped_column(
        Enum("active", "inactive", "deleted", name="scene_status"),
        default="active",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(3), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(3),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    category: Mapped["SceneCategory"] = relationship("SceneCategory", back_populates="scenes")
    templates: Mapped[list["Template"]] = relationship("Template", back_populates="scene")  # type: ignore[name-defined]
