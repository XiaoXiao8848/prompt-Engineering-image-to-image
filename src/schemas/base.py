"""Pydantic Schema 基础类和通用混入."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    """所有 Schema 的基类."""

    model_config = ConfigDict(
        from_attributes=True,  # 允许从 ORM 对象创建
        populate_by_name=True,
        json_encoders={
            datetime: lambda v: v.isoformat(),
        },
    )


class TimestampMixin(BaseSchema):
    """时间戳混入 — 包含 created_at 和 updated_at."""

    created_at: datetime = Field(description="创建时间")
    updated_at: datetime = Field(description="更新时间")


class IDMixin(BaseSchema):
    """ID 混入 — 包含数据库主键."""

    id: int = Field(description="数据库 ID")


class UUIDMixin(BaseSchema):
    """UUID 混入 — 包含业务 UUID."""

    uuid: str = Field(description="业务 UUID")


class PaginationParams(BaseSchema):
    """分页查询参数."""

    page: int = Field(default=1, ge=1, description="页码")
    page_size: int = Field(default=20, ge=1, le=100, description="每页数量")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


class ListQueryParams(PaginationParams):
    """列表查询通用参数."""

    keyword: str | None = Field(default=None, description="搜索关键词")
    sort_by: str = Field(default="created_at", description="排序字段")
    sort_order: str = Field(default="desc", pattern=r"^(asc|desc)$", description="排序方向")
