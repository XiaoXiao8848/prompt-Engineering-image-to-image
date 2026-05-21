"""YAML 配置加载工具."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from src.models import ProductConfig, SceneDefinition


def load_yaml(path: Path) -> dict[str, Any]:
    """加载 YAML 文件为字典."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_product_config(path: Path) -> ProductConfig:
    """加载产品配置 YAML."""
    data = load_yaml(path)
    return ProductConfig.model_validate(data)


def load_scene_library(path: Path) -> dict[str, SceneDefinition]:
    """加载场景库 YAML，返回以 scene_id 为键的字典."""
    data = load_yaml(path)
    scenes_raw = data.get("scenes", [])
    return {s["id"]: SceneDefinition.model_validate(s) for s in scenes_raw}


def load_prompt_template(path: Path) -> str:
    """加载提示词模板文件（YAML 中的 template 字段或纯文本）."""
    data = load_yaml(path)
    if isinstance(data, dict):
        return data.get("template", "")
    return str(data) if data else ""


def load_all_scene_templates(templates_dir: Path) -> dict[str, str]:
    """加载 templates 目录下所有场景模板."""
    templates: dict[str, str] = {}
    if not templates_dir.exists():
        return templates
    for file_path in templates_dir.glob("*.yaml"):
        scene_id = file_path.stem
        templates[scene_id] = load_prompt_template(file_path)
    return templates
