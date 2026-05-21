"""核心提示词引擎 — 支持模板模式与 LLM 扩写模式.

使用 LangChain 的 PromptTemplate 和 ChatPromptTemplate 作为底层实现.
"""

from __future__ import annotations

import json
import os
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI

from src.loader import (
    load_all_scene_templates,
    load_prompt_template,
    load_scene_library,
    load_yaml,
)
from src.models import GeneratedPrompt, ProductConfig, PromptBatchOutput, SceneDefinition


class BasePromptEngine(ABC):
    """提示词引擎抽象基类."""

    def __init__(self, product: ProductConfig) -> None:
        self.product = product

    @abstractmethod
    def generate(self, scene: SceneDefinition) -> GeneratedPrompt:
        """为单个场景生成提示词."""
        ...

    def generate_batch(
        self,
        scenes: dict[str, SceneDefinition],
        scene_ids: list[str] | None = None,
    ) -> PromptBatchOutput:
        """批量生成提示词."""
        if scene_ids is None:
            scene_ids = list(scenes.keys())

        results: list[GeneratedPrompt] = []
        for sid in scene_ids:
            if sid not in scenes:
                continue
            prompt = self.generate(scenes[sid])
            results.append(prompt)

        return PromptBatchOutput(
            product_id=self.product.product_id,
            product_name=self.product.product_name,
            generated_at=datetime.now(timezone.utc).isoformat(),
            mode=self.mode,
            prompts=results,
        )

    @property
    @abstractmethod
    def mode(self) -> str:
        """引擎模式标识."""
        ...


class TemplatePromptEngine(BasePromptEngine):
    """模板模式引擎 — 使用 LangChain PromptTemplate 直接渲染.

    无需调用 API，离线可用，速度快，适合快速出词.
    """

    def __init__(
        self,
        product: ProductConfig,
        templates_dir: Path,
    ) -> None:
        super().__init__(product)
        self.templates_dir = Path(templates_dir)

    @property
    def mode(self) -> str:
        return "template"

    def generate(self, scene: SceneDefinition) -> GeneratedPrompt:
        """加载场景 YAML 模板，用 PromptTemplate 渲染."""
        scene_id = scene.id
        template_file = self.templates_dir / f"{scene_id}.yaml"

        template_data: dict[str, Any] = load_yaml(template_file) if template_file.exists() else {}

        template_str = template_data.get("template", "")
        negative_str = template_data.get("negative_prompt", "")
        params = template_data.get("parameters", {})

        # 合并产品变量和场景变量
        variables = {**self.product.to_template_vars(), **scene.to_template_vars()}

        # 使用 LangChain PromptTemplate 渲染
        prompt_template = PromptTemplate.from_template(template_str)
        rendered_prompt = prompt_template.format(**variables)

        # 渲染负向提示词
        negative_template = PromptTemplate.from_template(negative_str)
        rendered_negative = negative_template.format(**variables)

        return GeneratedPrompt(
            scene_id=scene_id,
            scene_name=scene.name,
            prompt=rendered_prompt.strip(),
            negative_prompt=rendered_negative.strip(),
            parameters=params,
            mode=self.mode,
        )


class LLMPromptEngine(BasePromptEngine):
    """LLM 扩写模式引擎 — 使用 LangChain ChatPromptTemplate + ChatOpenAI.

    调用 DeepSeek API（兼容 OpenAI 格式），生成更自然、更贴产品的提示词.
    """

    def __init__(
        self,
        product: ProductConfig,
        meta_template_path: Path,
        model: str | None = None,
        temperature: float = 0.7,
    ) -> None:
        super().__init__(product)
        self.meta_data = load_yaml(meta_template_path)
        self.system_template = self.meta_data.get("system_template", "")
        self.human_template = self.meta_data.get("human_template", "")

        # 初始化 LangChain ChatOpenAI（兼容 DeepSeek）
        api_key = os.getenv("OPENAI_API_KEY", "")
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
        model_name = model or os.getenv("OPENAI_MODEL", "deepseek-chat")

        if not api_key:
            raise RuntimeError(
                "LLM 模式需要设置 OPENAI_API_KEY 环境变量。"
                "请复制 .env.example 为 .env 并填入 DeepSeek API Key。"
            )

        self.llm = ChatOpenAI(
            model=model_name,
            api_key=api_key,
            base_url=base_url,
            temperature=temperature,
        )

    @property
    def mode(self) -> str:
        return "llm"

    def generate(self, scene: SceneDefinition) -> GeneratedPrompt:
        """使用 ChatPromptTemplate 组织消息，调用 LLM 扩写."""
        # 合并变量
        variables = {**self.product.to_template_vars(), **scene.to_template_vars()}

        # 构建 ChatPromptTemplate
        chat_template = ChatPromptTemplate.from_messages([
            SystemMessage(content=self.system_template),
            ("human", self.human_template),
        ])

        # 渲染消息
        messages = chat_template.format_messages(**variables)

        # 调用 LLM
        response = self.llm.invoke(messages)
        content = response.content if hasattr(response, "content") else str(response)

        # 解析 JSON 输出
        prompt_text, negative_text, params = self._parse_llm_output(content)

        return GeneratedPrompt(
            scene_id=scene.id,
            scene_name=scene.name,
            prompt=prompt_text,
            negative_prompt=negative_text,
            parameters=params,
            mode=self.mode,
        )

    @staticmethod
    def _parse_llm_output(content: str) -> tuple[str, str, dict[str, Any]]:
        """解析 LLM 返回的 JSON 格式输出."""
        # 尝试提取 JSON 块
        text = content.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            # 回退：直接返回整个内容作为 prompt
            return text, "", {}

        prompt = data.get("prompt", text)
        negative = data.get("negative_prompt", "")
        params = data.get("parameters", {})
        return prompt, negative, params


def create_engine(
    mode: str,
    product: ProductConfig,
    templates_dir: Path | None = None,
    meta_template_path: Path | None = None,
) -> BasePromptEngine:
    """工厂函数：根据模式创建对应的引擎."""
    if mode == "template":
        if templates_dir is None:
            templates_dir = Path("prompts/templates")
        return TemplatePromptEngine(product, templates_dir)
    elif mode == "llm":
        if meta_template_path is None:
            meta_template_path = Path("prompts/meta/expand_scene.yaml")
        return LLMPromptEngine(product, meta_template_path)
    else:
        raise ValueError(f"不支持的模式: {mode}。请选择 'template' 或 'llm'。")
