"""提示词生成相关 Pydantic Schema."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from src.schemas.base import BaseSchema


class GeneratePromptRequest(BaseSchema):
    """单条提示词生成请求."""

    product_uuid: str = Field(description="产品 UUID")
    scene_id: str = Field(description="场景标识")
    mode: Literal["template", "llm"] = Field(default="template", description="生成模式")
    llm_model: str | None = Field(default=None, description="LLM 模型（覆盖默认）")
    llm_temperature: float | None = Field(
        default=None, ge=0.0, le=2.0, description="温度参数"
    )
    use_cache: bool = Field(default=True, description="是否使用缓存")


class GeneratedPromptOut(BaseSchema):
    """生成的单条提示词结果."""

    scene_id: str = Field(description="场景标识")
    scene_name: str = Field(description="场景名称")
    prompt: str = Field(description="正向提示词")
    negative_prompt: str = Field(default="", description="负向提示词")
    parameters: dict[str, Any] = Field(default_factory=dict, description="图生图参数建议")
    mode: str = Field(description="生成模式")
    cache_hit: bool = Field(default=False, description="是否命中缓存")


class PromptWorkflowOut(BaseSchema):
    """ComfyUI / SD WebUI 兼容格式."""

    scene_id: str
    scene_name: str
    positive: str
    negative: str
    img2img_params: dict[str, Any]


class BatchGenerateRequest(BaseSchema):
    """批量生成请求."""

    product_uuid: str = Field(description="产品 UUID")
    scene_ids: list[str] = Field(min_length=1, description="场景标识列表")
    mode: Literal["template", "llm"] = Field(default="template", description="生成模式")
    llm_model: str | None = Field(default=None, description="LLM 模型")
    llm_temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    webhook_url: str | None = Field(default=None, max_length=500, description="完成回调 URL")


class BatchGenerateResponse(BaseSchema):
    """批量提交响应."""

    job_uuid: str = Field(description="任务 UUID")
    status: str = Field(description="任务状态")
    total_tasks: int = Field(description="总任务数")
    message: str = Field(default="批量任务已提交", description="提示信息")
