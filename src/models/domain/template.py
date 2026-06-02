"""模板系统 ORM 模型."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database import Base


class Template(Base):
    """提示词模板表."""

    __tablename__ = "templates"
    __table_args__ = (
        Index("idx_scene_type", "scene_id", "template_type"),
        {"comment": "提示词模板表"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    template_uuid: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        unique=True,
        default=lambda: str(uuid.uuid4()),
        comment="业务 UUID",
    )
    scene_id: Mapped[int] = mapped_column(
        ForeignKey("scenes.id", ondelete="CASCADE"),
        nullable=False,
        comment="关联场景",
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False, comment="模板名称")
    template_type: Mapped[str] = mapped_column(
        Enum("system", "positive", "negative", "meta", name="template_type"),
        nullable=False,
        comment="模板类型",
    )
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="模板内容（Jinja2）")
    variables: Mapped[list[str] | None] = mapped_column(comment="所需变量列表")
    is_default: Mapped[bool] = mapped_column(default=False, comment="是否默认模板")
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), comment="创建者"
    )
    status: Mapped[str] = mapped_column(
        Enum("active", "inactive", "deleted", name="template_status"),
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
    scene: Mapped["Scene"] = relationship("Scene", back_populates="templates")  # type: ignore[name-defined]
    versions: Mapped[list["TemplateVersion"]] = relationship(
        "TemplateVersion", back_populates="template", cascade="all, delete-orphan"
    )


class TemplateVersion(Base):
    """模板版本历史表."""

    __tablename__ = "template_versions"
    __table_args__ = (
        UniqueConstraint("template_id", "version", name="uk_template_version"),
        Index("idx_template_id", "template_id"),
        {"comment": "模板版本历史"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    template_id: Mapped[int] = mapped_column(
        ForeignKey("templates.id", ondelete="CASCADE"),
        nullable=False,
        comment="关联模板",
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, comment="版本号")
    content: Mapped[str] = mapped_column(Text, nullable=False, comment="该版本内容")
    changed_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), comment="修改者"
    )
    change_note: Mapped[str | None] = mapped_column(String(500), comment="变更说明")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(3), default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    template: Mapped["Template"] = relationship("Template", back_populates="versions")
