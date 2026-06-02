"""产品配置 ORM 模型."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Enum, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database import Base


class Product(Base):
    """产品配置表."""

    __tablename__ = "products"
    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uk_user_product"),
        Index("idx_user_status", "user_id", "status"),
        {"comment": "产品配置表"},
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_uuid: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        unique=True,
        default=lambda: str(uuid.uuid4()),
        comment="业务 UUID",
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="所属用户",
    )
    product_id: Mapped[str] = mapped_column(String(64), nullable=False, comment="产品标识")
    product_name: Mapped[str] = mapped_column(String(200), nullable=False, comment="产品名称")
    brand: Mapped[str | None] = mapped_column(String(100), comment="品牌")
    material: Mapped[str | None] = mapped_column(String(200), comment="材质")
    shape: Mapped[str | None] = mapped_column(String(200), comment="形状")
    color: Mapped[str | None] = mapped_column(String(200), comment="颜色")
    size: Mapped[str | None] = mapped_column(String(50), comment="尺寸")
    lock_tags: Mapped[str] = mapped_column(Text, nullable=False, comment="产品外观锁定标签")
    selling_points: Mapped[list[str] | None] = mapped_column(JSON, comment="核心卖点列表")
    reference_image: Mapped[dict | None] = mapped_column(
        JSON, comment="参考图说明 {description, angle, lighting}"
    )
    material_keywords: Mapped[list[str] | None] = mapped_column(JSON, comment="材质关键词列表")
    brand_tone: Mapped[str | None] = mapped_column(String(200), comment="品牌调性")
    status: Mapped[str] = mapped_column(
        Enum("active", "archived", "deleted", name="product_status"),
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
    user: Mapped["User"] = relationship("User", back_populates="products")  # type: ignore[name-defined]
