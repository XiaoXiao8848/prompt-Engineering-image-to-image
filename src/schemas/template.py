"""模板系统相关 Pydantic Schema."""

from __future__ import annotations

from pydantic import Field

from src.schemas.base import BaseSchema, IDMixin, ListQueryParams, TimestampMixin


class TemplateCreate(BaseSchema):
    """创建模板请求."""

    scene_id: int = Field(description="关联场景 ID")
    name: str = Field(min_length=1, max_length=100, description="模板名称")
    template_type: str = Field(
        pattern=r"^(system|positive|negative|meta)$",
        description="模板类型",
    )
    content: str = Field(min_length=1, description="模板内容（Jinja2）")
    variables: list[str] = Field(default_factory=list, description="所需变量列表")
    is_default: bool = Field(default=False, description="是否默认模板")


class TemplateUpdate(BaseSchema):
    """更新模板请求."""

    name: str | None = Field(default=None, max_length=100)
    content: str | None = Field(default=None)
    variables: list[str] | None = Field(default=None)
    is_default: bool | None = Field(default=None)
    status: str | None = Field(default=None, pattern=r"^(active|inactive)$")


class TemplateOut(IDMixin, TimestampMixin):
    """模板详情响应."""

    template_uuid: str
    scene_id: int
    name: str
    template_type: str
    content: str
    variables: list[str]
    is_default: bool
    status: str


class TemplateBriefOut(BaseSchema):
    """模板简要信息."""

    template_uuid: str
    name: str
    template_type: str
    is_default: bool


class TemplateVersionOut(IDMixin):
    """模板版本历史响应."""

    version: int
    content: str
    change_note: str | None
    created_at: str


class TemplateRenderRequest(BaseSchema):
    """模板渲染请求."""

    variables: dict[str, str] = Field(default_factory=dict, description="渲染变量")


class TemplateRenderResponse(BaseSchema):
    """模板渲染响应."""

    rendered: str = Field(description="渲染后的内容")
    template_uuid: str


class TemplateListQuery(ListQueryParams):
    """模板列表查询参数."""

    scene_id: int | None = Field(default=None, description="场景筛选")
    template_type: str | None = Field(
        default=None,
        pattern=r"^(system|positive|negative|meta)$",
        description="类型筛选",
    )
