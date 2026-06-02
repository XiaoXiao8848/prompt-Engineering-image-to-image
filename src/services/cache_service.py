"""缓存服务 — 统一封装缓存策略（预热、双删、LLM 结果缓存）."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from src.config import settings
from src.infrastructure.redis_client import RedisCache
from src.schemas.prompt import GeneratedPromptOut


class CacheService:
    """缓存服务."""

    def __init__(self, redis_cache: RedisCache) -> None:
        self._redis = redis_cache

    # ========== 场景缓存 ==========

    async def get_scene(self, scene_id: str) -> dict | None:
        """获取场景缓存."""
        return await self._redis.get_json(f"pe:scene:{scene_id}")

    async def set_scene(self, scene_id: str, data: dict, ttl: int = 300) -> None:
        """设置场景缓存（默认 5 分钟）."""
        await self._redis.set_json(f"pe:scene:{scene_id}", data, ttl)

    async def delete_scene(self, scene_id: str) -> None:
        """删除场景缓存."""
        await self._redis.delete(f"pe:scene:{scene_id}")

    # ========== 模板缓存 ==========

    async def get_template(self, template_uuid: str) -> dict | None:
        """获取模板缓存."""
        return await self._redis.get_json(f"pe:template:{template_uuid}")

    async def set_template(self, template_uuid: str, data: dict, ttl: int = 600) -> None:
        """设置模板缓存（默认 10 分钟）."""
        await self._redis.set_json(f"pe:template:{template_uuid}", data, ttl)

    async def delete_template(self, template_uuid: str) -> None:
        """删除模板缓存."""
        await self._redis.delete(f"pe:template:{template_uuid}")

    # ========== LLM 结果缓存 ==========

    def _compute_llm_cache_key(
        self,
        product_id: str,
        scene_id: str,
        mode: str,
        model: str,
        temperature: float,
    ) -> str:
        """计算 LLM 缓存 Key."""
        content = f"{product_id}:{scene_id}:{mode}:{model}:{temperature}"
        hash_val = hashlib.sha256(content.encode()).hexdigest()
        return f"pe:llm:cache:{hash_val}"

    async def get_llm_result(
        self,
        product_id: str,
        scene_id: str,
        mode: str,
        model: str,
        temperature: float,
    ) -> GeneratedPromptOut | None:
        """获取 LLM 生成结果缓存."""
        key = self._compute_llm_cache_key(product_id, scene_id, mode, model, temperature)
        data = await self._redis.get_json(key)
        if data:
            return GeneratedPromptOut(**data)
        return None

    async def set_llm_result(
        self,
        product_id: str,
        scene_id: str,
        mode: str,
        model: str,
        temperature: float,
        result: GeneratedPromptOut,
    ) -> None:
        """设置 LLM 生成结果缓存（默认 24 小时）."""
        key = self._compute_llm_cache_key(product_id, scene_id, mode, model, temperature)
        await self._redis.set_json(key, result.model_dump(), settings.llm_cache_ttl)

    # ========== 产品缓存 ==========

    async def get_product(self, product_uuid: str) -> dict | None:
        """获取产品缓存."""
        return await self._redis.get_json(f"pe:product:{product_uuid}")

    async def set_product(self, product_uuid: str, data: dict, ttl: int = 600) -> None:
        """设置产品缓存."""
        await self._redis.set_json(f"pe:product:{product_uuid}", data, ttl)

    async def delete_product(self, product_uuid: str) -> None:
        """删除产品缓存."""
        await self._redis.delete(f"pe:product:{product_uuid}")

    # ========== 分布式锁 ==========

    async def acquire_lock(self, lock_key: str, lock_value: str, ttl: int = 60) -> bool:
        """获取分布式锁."""
        return await self._redis.acquire_lock(lock_key, lock_value, ttl)

    async def release_lock(self, lock_key: str, lock_value: str) -> bool:
        """释放分布式锁."""
        return await self._redis.release_lock(lock_key, lock_value)
