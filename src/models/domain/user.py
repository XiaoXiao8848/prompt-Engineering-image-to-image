"""用户与认证相关 ORM 模型."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database import Base


class User(Base):
    """用户表."""

    __tablename__ = "users"
    __table_args__ = (
        Index("idx_email", "email"),
        Index("idx_status_role", "status", "role"),
        {"comment": "用户表"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, comment="登录名")
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, comment="邮箱")
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False, comment="bcrypt 哈希")
    display_name: Mapped[str | None] = mapped_column(String(100), comment="显示名称")
    avatar_url: Mapped[str | None] = mapped_column(String(500), comment="头像")
    role: Mapped[str] = mapped_column(
        Enum("admin", "user", "api", name="user_role"),
        default="user",
        comment="角色",
    )
    status: Mapped[str] = mapped_column(
        Enum("active", "inactive", "banned", name="user_status"),
        default="active",
    )
    quota_daily: Mapped[int] = mapped_column(Integer, default=100, comment="每日生成配额")
    quota_used_today: Mapped[int] = mapped_column(Integer, default=0, comment="今日已用配额")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(3),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(3),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    api_keys: Mapped[list["ApiKey"]] = relationship("ApiKey", back_populates="user", cascade="all, delete-orphan")
    products: Mapped[list["Product"]] = relationship("Product", back_populates="user", cascade="all, delete-orphan")  # type: ignore[name-defined]


class ApiKey(Base):
    """API Key 表 — 支持多 Key、权限细分."""

    __tablename__ = "api_keys"
    __table_args__ = (
        Index("idx_key_hash", "key_hash"),
        Index("idx_user_id", "user_id"),
        {"comment": "API Key 表"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="所属用户",
    )
    key_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, comment="Key 的 SHA256 哈希")
    key_prefix: Mapped[str] = mapped_column(String(16), nullable=False, comment="Key 前缀，用于展示")
    name: Mapped[str | None] = mapped_column(String(100), comment="Key 名称")
    permissions: Mapped[dict | None] = mapped_column(JSON, comment='权限列表 ["prompt:read", "prompt:write"]')
    rate_limit: Mapped[int] = mapped_column(Integer, default=60, comment="每分钟限制请求数")
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(3), comment="最后使用时间")
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(3), comment="过期时间")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(3),
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="api_keys")
