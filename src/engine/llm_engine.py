"""LLM 扩写模式引擎 — 调用 DeepSeek/OpenAI API."""

from __future__ import annotations

import json
import os
from typing import Any

from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from src.config import settings
from src.engine.base import BasePromptEngine
from src.schemas.prompt import GeneratedPromptOut


class LLMPromptEngine(BasePromptEngine):
    """LLM 扩写模式引擎 — 调用 API 生成更自然的提示词."""

    def __init__(
        self,
        model: str | None = None,
        temperature: float | None = None,
    ) -> None:
        api_key = settings.llm_api_key or os.getenv("OPENAI_API_KEY", "")
        base_url = settings.llm_base_url
        model_name = model or settings.llm_model
        temp = temperature if temperature is not None else settings.llm_temperature

        if not api_key:
            raise RuntimeError("LLM 模式需要配置 LLM_API_KEY")

        self._llm = ChatOpenAI(
            model=model_name,
            api_key=api_key,
            base_url=base_url,
            temperature=temp,
            timeout=settings.llm_timeout,
            max_retries=settings.llm_max_retries,
        )
        self._temperature = temp
        self._model_name = model_name

        # 系统提示词（与原有 meta template 逻辑一致）
        self._system_prompt = (
            "你是一位专业的 AI 图像生成提示词工程师，精通 Stable Diffusion、ComfyUI、Midjourney 等图生图工作流。\n\n"
            "## 核心职责\n"
            "根据产品信息和场景描述，生成高质量的英文图生图提示词。\n\n"
            "## 输出原则\n"
            "1. 产品锚定：提示词开头必须包含产品的 lock_tags\n"
            "2. 只改场景：背景、光线、道具、氛围可变；产品形状、配色、logo 位置不变\n"
            "3. 英文输出：所有提示词必须为英文，使用逗号分隔的 tag 风格\n"
            "4. 质量标签：自动追加画质增强标签\n"
            "5. 参数建议：为每个场景提供推荐的图生图参数\n\n"
            "## 输出格式\n"
            "请严格按以下 JSON 格式输出，不要包含任何其他文字：\n"
            '{"prompt": "正向提示词", "negative_prompt": "负向提示词", "parameters": {"denoising_strength": 0.4, "cfg_scale": 7.5, "steps": 30, "sampler": "DPM++ 2M Karras"}}'
        )

    @property
    def mode(self) -> str:
        return "llm"

    async def generate(
        self,
        product_data: dict[str, Any],
        scene_data: dict[str, Any],
    ) -> GeneratedPromptOut:
        """调用 LLM 扩写生成提示词."""
        # 构建用户消息
        user_msg = self._build_user_message(product_data, scene_data)

        chat_template = ChatPromptTemplate.from_messages([
            SystemMessage(content=self._system_prompt),
            ("human", user_msg),
        ])

        messages = chat_template.format_messages()
        response = await self._llm.ainvoke(messages)
        content = response.content if hasattr(response, "content") else str(response)

        prompt_text, negative_text, params = self._parse_llm_output(content)

        return GeneratedPromptOut(
            scene_id=scene_data.get("scene_id", ""),
            scene_name=scene_data.get("scene_name", ""),
            prompt=prompt_text,
            negative_prompt=negative_text,
            parameters=params,
            mode=self.mode,
        )

    def _build_user_message(self, product: dict[str, Any], scene: dict[str, Any]) -> str:
        """构建给 LLM 的用户消息."""
        return (
            f"请为以下产品生成「{scene.get('scene_name')}」场景的图生图提示词。\n\n"
            f"## 产品信息\n"
            f"- 产品名称：{product.get('product_name')}\n"
            f"- 品牌：{product.get('brand', '')}\n"
            f"- 材质：{product.get('material', '')}\n"
            f"- 形状：{product.get('shape', '')}\n"
            f"- 颜色：{product.get('color', '')}\n"
            f"- 尺寸：{product.get('size', '')}\n"
            f"- 产品外观锁定标签（必须保留）：{product.get('lock_tags', '')}\n"
            f"- 卖点：{product.get('selling_points', '')}\n"
            f"- 品牌调性：{product.get('brand_tone', '')}\n\n"
            f"## 场景信息\n"
            f"- 场景名称：{scene.get('scene_name')}\n"
            f"- 场景描述：{scene.get('scene_description', '')}\n"
            f"- 光线：{scene.get('lighting', '')}\n"
            f"- 背景：{scene.get('background', '')}\n"
            f"- 道具：{scene.get('props', '')}\n"
            f"- 氛围：{scene.get('atmosphere', '')}\n"
            f"- 关键词：{scene.get('scene_keywords', '')}\n\n"
            "请生成该场景的正向提示词、负向提示词和推荐参数，以 JSON 格式输出。"
        )

    @staticmethod
    def _parse_llm_output(content: str) -> tuple[str, str, dict[str, Any]]:
        """解析 LLM 返回的 JSON 格式输出."""
        text = content.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return text, "", {}

        prompt = data.get("prompt", text)
        negative = data.get("negative_prompt", "")
        params = data.get("parameters", {})
        return prompt, negative, params
