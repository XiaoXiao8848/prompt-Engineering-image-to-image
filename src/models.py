"""Pydantic 数据模型定义产品配置、场景定义和生成结果."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ReferenceImage(BaseModel):
    """参考图说明."""

    description: str = ""
    angle: str = ""
    lighting: str = ""


class ProductConfig(BaseModel):
    """产品配置模型."""

    product_id: str
    product_name: str
    brand: str = ""
    material: str = ""
    shape: str = ""
    color: str = ""
    size: str = ""
    lock_tags: str = Field(default="", description="产品外观锁定标签，图生图时必须保留")
    selling_points: list[str] = Field(default_factory=list)
    reference_image: ReferenceImage = Field(default_factory=ReferenceImage)
    material_keywords: list[str] = Field(default_factory=list)
    brand_tone: str = ""

    def to_template_vars(self) -> dict[str, Any]:
        """转换为模板渲染变量字典."""
        return {
            "product_id": self.product_id,
            "product_name": self.product_name,
            "brand": self.brand,
            "material": self.material,
            "shape": self.shape,
            "color": self.color,
            "size": self.size,
            "lock_tags": self.lock_tags.strip(),
            "selling_points": ", ".join(self.selling_points),
            "material_keywords": ", ".join(self.material_keywords),
            "brand_tone": self.brand_tone,
            "reference_description": self.reference_image.description,
            "reference_angle": self.reference_image.angle,
            "reference_lighting": self.reference_image.lighting,
        }


class SceneDefinition(BaseModel):
    """场景定义模型."""

    id: str
    name: str
    description: str = ""
    lighting: str = ""
    background: str = ""
    props: list[str] = Field(default_factory=list)
    atmosphere: str = ""
    keywords: list[str] = Field(default_factory=list)

    def to_template_vars(self) -> dict[str, Any]:
        """转换为模板渲染变量字典."""
        return {
            "scene_id": self.id,
            "scene_name": self.name,
            "scene_description": self.description,
            "lighting": self.lighting,
            "background": self.background,
            "props": ", ".join(self.props) if self.props else "",
            "atmosphere": self.atmosphere,
            "scene_keywords": ", ".join(self.keywords),
        }


class GeneratedPrompt(BaseModel):
    """生成的单条提示词结果."""

    scene_id: str
    scene_name: str
    prompt: str = Field(description="正向提示词（positive prompt）")
    negative_prompt: str = Field(default="", description="负向提示词（negative prompt）")
    parameters: dict[str, Any] = Field(default_factory=dict, description="图生图参数建议")
    mode: str = Field(default="template", description="生成模式：template 或 llm")


class PromptBatchOutput(BaseModel):
    """批量生成结果."""

    product_id: str
    product_name: str
    generated_at: str = ""
    mode: str = "template"
    prompts: list[GeneratedPrompt] = Field(default_factory=list)
