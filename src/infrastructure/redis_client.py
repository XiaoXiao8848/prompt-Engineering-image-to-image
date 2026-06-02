"""Redis 异步客户端封装 — 缓存、锁、限流、队列等底层操作."""

from __future__ import annotations

import json
from typing import Any

import redis.asyncio as aioredis

from src.config import settings

_redis_client: aioredis.Redis | None = None


async def init_redis() -> None:
    """初始化 Redis 连接池."""
    global _redis_client
    _redis_client = aioredis.from_url(
        settings.redis_url,
        max_connections=settings.redis_pool_size,
        decode_responses=True,
    )


async def close_redis() -> None:
    """关闭 Redis 连接池."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None


def get_redis() -> aioredis.Redis:
    """获取 Redis 客户端实例.

    注意：必须在 init_redis() 之后调用。
    """
    if _redis_client is None:
        raise RuntimeError("Redis 客户端未初始化，请先调用 init_redis()")
    return _redis_client


class RedisCache:
    """Redis 缓存封装类，提供类型安全的缓存操作."""

    def __init__(self, redis: aioredis.Redis | None = None) -> None:
        self._redis = redis or get_redis()

    async def get(self, key: str) -> str | None:
        """获取字符串缓存."""
        return await self._redis.get(key)

    async def get_json(self, key: str) -> Any | None:
        """获取 JSON 缓存并解析."""
        data = await self._redis.get(key)
        if data is None:
            return None
        return json.loads(data)

    async def set(
        self,
        key: str,
        value: str,
        ttl: int | None = None,
    ) -> None:
        """设置字符串缓存."""
        if ttl:
            await self._redis.setex(key, ttl, value)
        else:
            await self._redis.set(key, value)

    async def set_json(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> None:
        """设置 JSON 缓存."""
        await self.set(key, json.dumps(value, ensure_ascii=False), ttl)

    async def delete(self, key: str) -> None:
        """删除缓存."""
        await self._redis.delete(key)

    async def delete_pattern(self, pattern: str) -> None:
        """按模式删除缓存."""
        keys = await self._redis.keys(pattern)
        if keys:
            await self._redis.delete(*keys)

    async def exists(self, key: str) -> bool:
        """检查 Key 是否存在."""
        return await self._redis.exists(key) > 0

    async def acquire_lock(
        self,
        lock_key: str,
        lock_value: str,
        ttl: int = 60,
    ) -> bool:
        """获取分布式锁（SET NX EX 原子操作）.

        Args:
            lock_key: 锁的 Key
            lock_value: 锁的值（通常用 UUID 或任务 ID）
            ttl: 锁过期时间（秒）

        Returns:
            是否成功获取锁
        """
        result = await self._redis.set(lock_key, lock_value, nx=True, ex=ttl)
        return result is not None

    async def release_lock(self, lock_key: str, lock_value: str) -> bool:
        """释放分布式锁（Lua 脚本保证原子性）."""
        lua_script = """
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
        """
        result = await self._redis.eval(lua_script, 1, lock_key, lock_value)
        return bool(result)

    async def increment(self, key: str, amount: int = 1) -> int:
        """原子递增."""
        return await self._redis.incrby(key, amount)

    async def expire(self, key: str, ttl: int) -> None:
        """设置 TTL."""
        await self._redis.expire(key, ttl)

    @property
    def raw(self) -> aioredis.Redis:
        """暴露底层 Redis 客户端，用于 Pipeline 等高级操作."""
        return self._redis

    def pipeline(self) -> aioredis.client.Pipeline:
        """创建 Redis Pipeline."""
        return self._redis.pipeline()
