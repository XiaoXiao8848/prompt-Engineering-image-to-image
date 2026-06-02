"""模板模式引擎 — 使用 Jinja2 直接渲染."""

from __future__ import annotations

from typing import Any

from jinja2 import Template as JinjaTemplate

from src.engine.base import BasePromptEngine
from src.repositories.template_repo import TemplateRepository
from src.schemas.prompt import GeneratedPromptOut


class TemplatePromptEngine(BasePromptEngine):
    """模板模式引擎 — 无需调用 API，离线可用，速度快."""

    def __init__(self, template_repo: TemplateRepository) -> None:
        self._template_repo = template_repo

    @property
    def mode(self) -> str:
        return "template"

    async def generate(
        self,
        product_data: dict[str, Any],
        scene_data: dict[str, Any],
    ) -> GeneratedPromptOut:
        """加载场景模板，用 Jinja2 渲染."""
        scene_id = scene_data.get("scene_id")

        # 查询默认正向模板
        positive_tpl = await self._template_repo.get_default_by_scene(
            scene_id=scene_data.get("db_id"), template_type="positive"
        )
        negative_tpl = await self._template_repo.get_default_by_scene(
            scene_id=scene_data.get("db_id"), template_type="negative"
        )

        positive_content = positive_tpl.content if positive_tpl else ""
        negative_content = negative_tpl.content if negative_tpl else ""

        # 合并变量
        variables = {**product_data, **scene_data}

        # 渲染
        rendered_prompt = JinjaTemplate(positive_content).render(**variables) if positive_content else ""
        rendered_negative = JinjaTemplate(negative_content).render(**variables) if negative_content else ""

        return GeneratedPromptOut(
            scene_id=scene_id or "",
            scene_name=scene_data.get("scene_name", ""),
            prompt=rendered_prompt.strip(),
            negative_prompt=rendered_negative.strip(),
            parameters=scene_data.get("parameters", {}),
            mode=self.mode,
        )
