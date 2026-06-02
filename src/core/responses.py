"""统一响应格式 — 所有 API 返回结构一致."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    """统一 API 响应结构."""

    code: str = Field(default="SUCCESS", description="业务状态码")
    message: str = Field(default="操作成功", description="提示信息")
    data: T | None = Field(default=None, description="响应数据")


class PaginationInfo(BaseModel):
    """分页元信息."""

    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页数量")
    total: int = Field(description="总记录数")
    total_pages: int = Field(description="总页数")
    has_next: bool = Field(description="是否有下一页")
    has_prev: bool = Field(description="是否有上一页")


class PaginatedResponse(BaseModel, Generic[T]):
    """分页列表响应结构."""

    code: str = Field(default="SUCCESS")
    message: str = Field(default="操作成功")
    data: list[T] = Field(default_factory=list, description="数据列表")
    pagination: PaginationInfo = Field(description="分页信息")


def success(data: Any | None = None, message: str = "操作成功") -> dict[str, Any]:
    """构造成功响应."""
    return {"code": "SUCCESS", "message": message, "data": data}


def error(code: str, message: str, data: Any | None = None) -> dict[str, Any]:
    """构造错误响应."""
    return {"code": code, "message": message, "data": data}
