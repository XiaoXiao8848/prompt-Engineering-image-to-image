"""测试 YAML 加载工具."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from src.loader import (
    load_all_scene_templates,
    load_product_config,
    load_prompt_template,
    load_scene_library,
    load_yaml,
)
from src.models import ProductConfig, SceneDefinition


class TestLoadYaml:
    """测试基础 YAML 加载."""

    def test_load_existing_file(self, fixtures_dir: Path) -> None:
        """加载存在的 YAML 文件."""
        path = fixtures_dir / "test_product.yaml"
        data = load_yaml(path)
        assert isinstance(data, dict)
        assert data["product_id"] == "test_serum"
        assert data["product_name"] == "测试精华液"

    def test_load_nonexistent_file(self, tmp_path: Path) -> None:
        """加载不存在的文件应抛出 FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_yaml(tmp_path / "not_exist.yaml")

    def test_load_empty_file(self, tmp_path: Path) -> None:
        """加载空文件返回空字典."""
        empty_file = tmp_path / "empty.yaml"
        empty_file.write_text("", encoding="utf-8")
        data = load_yaml(empty_file)
        assert data == {}


class TestLoadProductConfig:
    """测试产品配置加载."""

    def test_load_from_file(self, product_path: Path) -> None:
        """从 YAML 文件加载产品配置."""
        product = load_product_config(product_path)
        assert isinstance(product, ProductConfig)
        assert product.product_id == "test_serum"
        assert product.product_name == "测试精华液"
        assert product.brand == "TestBrand"
        assert product.material == "磨砂玻璃"
        assert product.selling_points == ["深层修护", "提亮肤色", "温和不刺激"]

    def test_invalid_data(self, tmp_path: Path) -> None:
        """无效数据应抛出 ValidationError."""
        bad_file = tmp_path / "bad.yaml"
        bad_file.write_text("product_id: test\n", encoding="utf-8")
        with pytest.raises(Exception):
            load_product_config(bad_file)


class TestLoadSceneLibrary:
    """测试场景库加载."""

    def test_load_from_file(self, scenes_path: Path) -> None:
        """从 YAML 文件加载场景库."""
        scenes = load_scene_library(scenes_path)
        assert isinstance(scenes, dict)
        assert "test_studio" in scenes
        assert "test_lifestyle" in scenes

        studio = scenes["test_studio"]
        assert isinstance(studio, SceneDefinition)
        assert studio.name == "测试棚拍"
        assert studio.lighting == "柔光箱双侧打光"
        assert studio.props == ["反光板", "柔光布"]

    def test_empty_scenes(self, tmp_path: Path) -> None:
        """空场景库返回空字典."""
        empty_file = tmp_path / "empty_scenes.yaml"
        empty_file.write_text("scenes: []\n", encoding="utf-8")
        scenes = load_scene_library(empty_file)
        assert scenes == {}


class TestLoadPromptTemplate:
    """测试提示词模板加载."""

    def test_load_template(self, templates_dir: Path) -> None:
        """加载模板文件获取 template 字符串."""
        path = templates_dir / "test_studio.yaml"
        template = load_prompt_template(path)
        assert isinstance(template, str)
        assert "{lock_tags}" in template
        assert "{product_name}" in template

    def test_load_nonexistent(self, tmp_path: Path) -> None:
        """不存在的文件应抛出 FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_prompt_template(tmp_path / "no.yaml")


class TestLoadAllSceneTemplates:
    """测试批量加载场景模板."""

    def test_load_directory(self, templates_dir: Path) -> None:
        """加载模板目录下所有模板."""
        templates = load_all_scene_templates(templates_dir)
        assert "test_studio" in templates
        assert "test_lifestyle" in templates
        assert isinstance(templates["test_studio"], str)
        assert "{lock_tags}" in templates["test_studio"]

    def test_load_empty_directory(self, tmp_path: Path) -> None:
        """空目录返回空字典."""
        empty_dir = tmp_path / "empty_templates"
        empty_dir.mkdir()
        templates = load_all_scene_templates(empty_dir)
        assert templates == {}

    def test_load_nonexistent_directory(self, tmp_path: Path) -> None:
        """不存在的目录返回空字典."""
        templates = load_all_scene_templates(tmp_path / "not_exist")
        assert templates == {}
