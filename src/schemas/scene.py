"""场景定义相关 Pydantic Schema."""

from __future__ import annotations

from pydantic import Field

from src.schemas.base import BaseSchema, IDMixin, ListQueryParams, TimestampMixin


class SceneCategoryCreate(BaseSchema):
    """创建场景分类请求."""

    name: str = Field(min_length=1, max_length=50, description="分类名称")
    description: str | None = Field(default=None, max_length=200, description="描述")
    sort_order: int = Field(default=0, description="排序")


class SceneCategoryOut(IDMixin):
    """场景分类响应."""

    name: str
    description: str | None
    sort_order: int
    created_at: str


class SceneCreate(BaseSchema):
    """创建场景请求."""

    scene_id: str = Field(min_length=1, max_length=64, description="场景标识")
    name: str = Field(min_length=1, max_length=100, description="场景名称")
    description: str | None = Field(default=None, description="场景描述")
    lighting: str | None = Field(default=None, description="光线描述")
    background: str | None = Field(default=None, description="背景描述")
    props: list[str] = Field(default_factory=list, description="道具列表")
    atmosphere: str | None = Field(default=None, max_length=200, description="氛围")
    keywords: list[str] = Field(default_factory=list, description="关键词列表")
    category_id: int | None = Field(default=None, description="所属分类 ID")
    is_public: bool = Field(default=True, description="是否公开")


class SceneUpdate(BaseSchema):
    """更新场景请求."""

    name: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None)
    lighting: str | None = Field(default=None)
    background: str | None = Field(default=None)
    props: list[str] | None = Field(default=None)
    atmosphere: str | None = Field(default=None, max_length=200)
    keywords: list[str] | None = Field(default=None)
    category_id: int | None = Field(default=None)
    is_public: bool | None = Field(default=None)
    status: str | None = Field(default=None, pattern=r"^(active|inactive)$")


class SceneOut(IDMixin, TimestampMixin):
    """场景详情响应."""

    scene_uuid: str
    scene_id: str
    name: str
    description: str | None
    lighting: str | None
    background: str | None
    props: list[str]
    atmosphere: str | None
    keywords: list[str]
    category: SceneCategoryOut | None
    is_builtin: bool
    is_public: bool
    status: str


class SceneBriefOut(BaseSchema):
    """场景简要信息."""

    scene_id: str
    name: str
    description: str | None
    atmosphere: str | None


class SceneListQuery(ListQueryParams):
    """场景列表查询参数."""

    category_id: int | None = Field(default=None, description="分类筛选")
    is_public: bool | None = Field(default=True, description="是否公开")
