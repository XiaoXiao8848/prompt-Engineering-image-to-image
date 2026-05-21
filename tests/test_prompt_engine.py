"""测试提示词引擎.

覆盖模板模式引擎和 LLM 模式引擎的核心功能.
对 LLM 调用使用 unittest.mock 进行模拟.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.models import GeneratedPrompt, ProductConfig, SceneDefinition
from src.prompt_engine import (
    BasePromptEngine,
    LLMPromptEngine,
    TemplatePromptEngine,
    create_engine,
)


# ═══════════════════════════════════════════════════════════════
#  TemplatePromptEngine Tests
# ═══════════════════════════════════════════════════════════════

class TestTemplatePromptEngine:
    """测试模板模式引擎."""

    def test_init(self, sample_product: ProductConfig, templates_dir: Path) -> None:
        """引擎初始化应正确设置模板目录."""
        engine = TemplatePromptEngine(sample_product, templates_dir)
        assert engine.product == sample_product
        assert engine.mode == "template"
        assert engine.templates_dir == templates_dir

    def test_generate_single_scene(
        self,
        sample_product: ProductConfig,
        sample_scene_studio: SceneDefinition,
        templates_dir: Path,
    ) -> None:
        """为单个场景生成提示词."""
        engine = TemplatePromptEngine(sample_product, templates_dir)
        result = engine.generate(sample_scene_studio)

        assert isinstance(result, GeneratedPrompt)
        assert result.scene_id == "test_studio"
        assert result.scene_name == "测试棚拍"
        assert result.mode == "template"

        # 验证产品信息被正确插入
        assert "amber glass bottle, frosted texture, gold cap" in result.prompt
        assert "测试精华液" in result.prompt
        assert "磨砂玻璃" in result.prompt

        # 验证场景信息被正确插入
        assert "测试棚拍" in result.prompt
        assert "纯白无缝背景" in result.prompt
        assert "柔光箱双侧打光" in result.prompt

        # 验证负向提示词
        assert result.negative_prompt != ""
        assert "blurry" in result.negative_prompt

        # 验证参数
        assert result.parameters["denoising_strength"] == 0.35
        assert result.parameters["cfg_scale"] == 7.0

    def test_generate_lifestyle_scene(
        self,
        sample_product: ProductConfig,
        sample_scene_lifestyle: SceneDefinition,
        templates_dir: Path,
    ) -> None:
        """为生活场景生成提示词."""
        engine = TemplatePromptEngine(sample_product, templates_dir)
        result = engine.generate(sample_scene_lifestyle)

        assert result.scene_id == "test_lifestyle"
        assert "木质桌面" in result.prompt
        assert "自然窗光" in result.prompt
        assert "绿植" in result.prompt
        assert result.parameters["denoising_strength"] == 0.45

    def test_generate_missing_template(
        self,
        sample_product: ProductConfig,
        tmp_path: Path,
    ) -> None:
        """场景无对应模板时应优雅处理."""
        engine = TemplatePromptEngine(sample_product, tmp_path)
        fake_scene = SceneDefinition(id="no_template", name="无模板")
        result = engine.generate(fake_scene)

        # 无模板时 template_str 为空，渲染结果基本为空或只有变量名
        assert result.scene_id == "no_template"
        assert result.mode == "template"

    def test_generate_batch(
        self,
        sample_product: ProductConfig,
        sample_scene_studio: SceneDefinition,
        sample_scene_lifestyle: SceneDefinition,
        templates_dir: Path,
    ) -> None:
        """批量生成多个场景."""
        engine = TemplatePromptEngine(sample_product, templates_dir)
        scenes = {
            "test_studio": sample_scene_studio,
            "test_lifestyle": sample_scene_lifestyle,
        }
        batch = engine.generate_batch(scenes)

        assert batch.product_id == "test_serum"
        assert batch.product_name == "测试精华液"
        assert batch.mode == "template"
        assert len(batch.prompts) == 2

        scene_ids = {p.scene_id for p in batch.prompts}
        assert scene_ids == {"test_studio", "test_lifestyle"}

    def test_generate_batch_filter(
        self,
        sample_product: ProductConfig,
        sample_scene_studio: SceneDefinition,
        sample_scene_lifestyle: SceneDefinition,
        templates_dir: Path,
    ) -> None:
        """批量生成时过滤指定场景."""
        engine = TemplatePromptEngine(sample_product, templates_dir)
        scenes = {
            "test_studio": sample_scene_studio,
            "test_lifestyle": sample_scene_lifestyle,
        }
        batch = engine.generate_batch(scenes, scene_ids=["test_studio"])

        assert len(batch.prompts) == 1
        assert batch.prompts[0].scene_id == "test_studio"

    def test_generate_batch_skip_missing(
        self,
        sample_product: ProductConfig,
        sample_scene_studio: SceneDefinition,
        templates_dir: Path,
    ) -> None:
        """批量生成时跳过不存在的场景."""
        engine = TemplatePromptEngine(sample_product, templates_dir)
        scenes = {"test_studio": sample_scene_studio}
        batch = engine.generate_batch(scenes, scene_ids=["test_studio", "not_exist"])

        assert len(batch.prompts) == 1
        assert batch.prompts[0].scene_id == "test_studio"


# ═══════════════════════════════════════════════════════════════
#  LLMPromptEngine Tests (with mocked LLM)
# ═══════════════════════════════════════════════════════════════

class TestLLMPromptEngine:
    """测试 LLM 扩写模式引擎（Mock LLM 调用）."""

    @pytest.fixture
    def mock_llm_response(self) -> MagicMock:
        """模拟 LLM 返回的 JSON 格式响应."""
        mock_response = MagicMock()
        mock_response.content = json.dumps({
            "prompt": "mocked positive prompt with product details",
            "negative_prompt": "mocked negative prompt",
            "parameters": {"denoising_strength": 0.5, "steps": 25},
        })
        return mock_response

    @pytest.fixture
    def mock_llm_plain_text(self) -> MagicMock:
        """模拟 LLM 返回的纯文本响应."""
        mock_response = MagicMock()
        mock_response.content = "plain text prompt without json"
        return mock_response

    def test_init_without_api_key(
        self,
        sample_product: ProductConfig,
        meta_template_path: Path,
    ) -> None:
        """未设置 API Key 时应抛出 RuntimeError."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=True):
            with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
                LLMPromptEngine(sample_product, meta_template_path)

    def test_mode_property(
        self,
        sample_product: ProductConfig,
        meta_template_path: Path,
    ) -> None:
        """mode 属性应为 'llm'."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}, clear=True):
            engine = LLMPromptEngine(sample_product, meta_template_path)
            assert engine.mode == "llm"

    def test_generate_with_mock_llm(
        self,
        sample_product: ProductConfig,
        sample_scene_studio: SceneDefinition,
        meta_template_path: Path,
        mock_llm_response: MagicMock,
    ) -> None:
        """使用 Mock LLM 生成提示词."""
        mock_llm_class = MagicMock()
        mock_llm_class.return_value.invoke.return_value = mock_llm_response

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}, clear=True):
            with patch("src.prompt_engine.ChatOpenAI", mock_llm_class):
                engine = LLMPromptEngine(sample_product, meta_template_path)
                result = engine.generate(sample_scene_studio)

        assert isinstance(result, GeneratedPrompt)
        assert result.scene_id == "test_studio"
        assert result.scene_name == "测试棚拍"
        assert result.mode == "llm"
        assert result.prompt == "mocked positive prompt with product details"
        assert result.negative_prompt == "mocked negative prompt"
        assert result.parameters == {"denoising_strength": 0.5, "steps": 25}

    def test_generate_plain_text_fallback(
        self,
        sample_product: ProductConfig,
        sample_scene_studio: SceneDefinition,
        meta_template_path: Path,
        mock_llm_plain_text: MagicMock,
    ) -> None:
        """LLM 返回非 JSON 时回退为纯文本."""
        mock_llm_class = MagicMock()
        mock_llm_class.return_value.invoke.return_value = mock_llm_plain_text

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}, clear=True):
            with patch("src.prompt_engine.ChatOpenAI", mock_llm_class):
                engine = LLMPromptEngine(sample_product, meta_template_path)
                result = engine.generate(sample_scene_studio)

        assert result.prompt == "plain text prompt without json"
        assert result.negative_prompt == ""
        assert result.parameters == {}

    def test_generate_batch_with_mock(
        self,
        sample_product: ProductConfig,
        sample_scene_studio: SceneDefinition,
        sample_scene_lifestyle: SceneDefinition,
        meta_template_path: Path,
        mock_llm_response: MagicMock,
    ) -> None:
        """批量生成时使用 Mock LLM."""
        mock_llm_class = MagicMock()
        mock_llm_class.return_value.invoke.return_value = mock_llm_response

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}, clear=True):
            with patch("src.prompt_engine.ChatOpenAI", mock_llm_class):
                engine = LLMPromptEngine(sample_product, meta_template_path)
                scenes = {
                    "test_studio": sample_scene_studio,
                    "test_lifestyle": sample_scene_lifestyle,
                }
                batch = engine.generate_batch(scenes)

        assert batch.mode == "llm"
        assert len(batch.prompts) == 2
        for p in batch.prompts:
            assert p.prompt == "mocked positive prompt with product details"

    def test_parse_llm_output_json_block(self) -> None:
        """解析 markdown JSON 代码块."""
        content = '```json\n{"prompt": "test", "negative_prompt": "neg", "parameters": {"a": 1}}\n```'
        prompt, negative, params = LLMPromptEngine._parse_llm_output(content)
        assert prompt == "test"
        assert negative == "neg"
        assert params == {"a": 1}

    def test_parse_llm_output_plain_json(self) -> None:
        """解析纯 JSON 文本."""
        content = '{"prompt": "test2", "negative_prompt": "neg2"}'
        prompt, negative, params = LLMPromptEngine._parse_llm_output(content)
        assert prompt == "test2"
        assert negative == "neg2"

    def test_parse_llm_output_invalid_json(self) -> None:
        """无效 JSON 回退为纯文本."""
        content = "this is not json at all"
        prompt, negative, params = LLMPromptEngine._parse_llm_output(content)
        assert prompt == "this is not json at all"
        assert negative == ""
        assert params == {}


# ═══════════════════════════════════════════════════════════════
#  Factory & Integration Tests
# ═══════════════════════════════════════════════════════════════

class TestCreateEngine:
    """测试引擎工厂函数."""

    def test_create_template_engine(
        self,
        sample_product: ProductConfig,
        templates_dir: Path,
    ) -> None:
        """创建模板模式引擎."""
        engine = create_engine(
            "template",
            sample_product,
            templates_dir=templates_dir,
        )
        assert isinstance(engine, TemplatePromptEngine)
        assert engine.mode == "template"

    def test_create_llm_engine(
        self,
        sample_product: ProductConfig,
        meta_template_path: Path,
    ) -> None:
        """创建 LLM 模式引擎."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}, clear=True):
            engine = create_engine(
                "llm",
                sample_product,
                meta_template_path=meta_template_path,
            )
            assert isinstance(engine, LLMPromptEngine)
            assert engine.mode == "llm"

    def test_create_invalid_mode(self, sample_product: ProductConfig) -> None:
        """无效模式应抛出 ValueError."""
        with pytest.raises(ValueError, match="不支持的模式"):
            create_engine("invalid", sample_product)


class TestEngineAbstractBase:
    """测试引擎抽象基类."""

    def test_base_class_cannot_instantiate(self, sample_product: ProductConfig) -> None:
        """抽象基类不能直接实例化."""
        with pytest.raises(TypeError):
            BasePromptEngine(sample_product)  # type: ignore[abstract]

    def test_base_class_requires_mode(self, sample_product: ProductConfig) -> None:
        """子类必须实现 mode 属性."""
        class IncompleteEngine(BasePromptEngine):
            def generate(self, scene: SceneDefinition) -> GeneratedPrompt:
                return GeneratedPrompt(scene_id="", scene_name="")

        with pytest.raises(TypeError):
            IncompleteEngine(sample_product)  # type: ignore[abstract]
