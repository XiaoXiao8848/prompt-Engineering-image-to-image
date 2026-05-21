"""测试 Pydantic 数据模型."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.models import (
    GeneratedPrompt,
    ProductConfig,
    PromptBatchOutput,
    ReferenceImage,
    SceneDefinition,
)


class TestProductConfig:
    """测试产品配置模型."""

    def test_create_minimal(self) -> None:
        """最小必填字段创建."""
        p = ProductConfig(product_id="test", product_name="测试")
        assert p.product_id == "test"
        assert p.product_name == "测试"
        assert p.lock_tags == ""
        assert p.selling_points == []

    def test_create_full(self) -> None:
        """完整字段创建."""
        p = ProductConfig(
            product_id="serum_01",
            product_name="焕颜精华液",
            brand="GlowLab",
            material="玻璃",
            color="琥珀色",
            lock_tags="amber bottle, gold cap",
            selling_points=["修护", "保湿"],
        )
        assert p.brand == "GlowLab"
        assert p.lock_tags == "amber bottle, gold cap"
        assert p.selling_points == ["修护", "保湿"]

    def test_missing_required_fields(self) -> None:
        """缺少必填字段应抛出 ValidationError."""
        with pytest.raises(ValidationError):
            ProductConfig(product_id="test")  # 缺少 product_name

    def test_to_template_vars(self, sample_product: ProductConfig) -> None:
        """转换为模板变量字典."""
        vars_dict = sample_product.to_template_vars()
        assert vars_dict["product_id"] == "test_serum"
        assert vars_dict["product_name"] == "测试精华液"
        assert vars_dict["lock_tags"] == "amber glass bottle, frosted texture, gold cap"
        assert vars_dict["selling_points"] == "深层修护, 提亮肤色"
        assert vars_dict["material_keywords"] == "磨砂玻璃, 琥珀色"
        assert "reference_description" in vars_dict

    def test_reference_image_default(self) -> None:
        """默认参考图对象."""
        p = ProductConfig(product_id="x", product_name="y")
        assert isinstance(p.reference_image, ReferenceImage)
        assert p.reference_image.description == ""


class TestSceneDefinition:
    """测试场景定义模型."""

    def test_create_minimal(self) -> None:
        """最小字段创建."""
        s = SceneDefinition(id="studio", name="棚拍")
        assert s.id == "studio"
        assert s.name == "棚拍"
        assert s.props == []
        assert s.keywords == []

    def test_create_full(self) -> None:
        """完整字段创建."""
        s = SceneDefinition(
            id="outdoor",
            name="户外",
            description="自然光户外场景",
            lighting="自然光",
            background="草地",
            props=["花朵", "树叶"],
            atmosphere="清新",
        )
        assert s.lighting == "自然光"
        assert s.props == ["花朵", "树叶"]

    def test_to_template_vars(self, sample_scene_studio: SceneDefinition) -> None:
        """转换为模板变量字典."""
        vars_dict = sample_scene_studio.to_template_vars()
        assert vars_dict["scene_id"] == "test_studio"
        assert vars_dict["scene_name"] == "测试棚拍"
        assert vars_dict["lighting"] == "柔光箱双侧打光"
        assert vars_dict["props"] == "反光板, 柔光布"
        assert vars_dict["scene_keywords"] == "棚拍, 白底"

    def test_empty_lists_to_empty_string(self) -> None:
        """空列表应转为空字符串."""
        s = SceneDefinition(id="x", name="y")
        vars_dict = s.to_template_vars()
        assert vars_dict["props"] == ""
        assert vars_dict["scene_keywords"] == ""


class TestGeneratedPrompt:
    """测试生成结果模型."""

    def test_create(self) -> None:
        """创建生成结果."""
        g = GeneratedPrompt(
            scene_id="studio",
            scene_name="棚拍",
            prompt="test prompt",
            negative_prompt="bad quality",
            parameters={"steps": 30},
            mode="template",
        )
        assert g.scene_id == "studio"
        assert g.prompt == "test prompt"
        assert g.mode == "template"

    def test_default_values(self) -> None:
        """默认值测试."""
        g = GeneratedPrompt(scene_id="x", scene_name="y", prompt="test")
        assert g.negative_prompt == ""
        assert g.parameters == {}
        assert g.mode == "template"


class TestPromptBatchOutput:
    """测试批量输出模型."""

    def test_create(self) -> None:
        """创建批量输出."""
        batch = PromptBatchOutput(
            product_id="serum",
            product_name="精华液",
            prompts=[
                GeneratedPrompt(scene_id="s1", scene_name="场景1", prompt="p1"),
                GeneratedPrompt(scene_id="s2", scene_name="场景2", prompt="p2"),
            ],
        )
        assert batch.product_id == "serum"
        assert len(batch.prompts) == 2
        assert batch.mode == "template"

    def test_serialization(self) -> None:
        """序列化为字典."""
        batch = PromptBatchOutput(
            product_id="test",
            product_name="测试",
            prompts=[GeneratedPrompt(scene_id="s1", scene_name="场景1", prompt="p1")],
        )
        data = batch.model_dump()
        assert data["product_id"] == "test"
        assert len(data["prompts"]) == 1
        assert "generated_at" in data
