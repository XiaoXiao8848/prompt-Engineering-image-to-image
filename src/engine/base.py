"""提示词引擎抽象基类."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from src.schemas.prompt import GeneratedPromptOut


class BasePromptEngine(ABC):
    """提示词引擎抽象基类."""

    @abstractmethod
    async def generate(
        self,
        product_data: dict[str, Any],
        scene_data: dict[str, Any],
    ) -> GeneratedPromptOut:
        """为单个场景生成提示词."""
        ...

    @property
    @abstractmethod
    def mode(self) -> str:
        """引擎模式标识."""
        ...
