"""限流服务 — 基于 Redis 滑动窗口的分布式限流."""

from __future__ import annotations

import time
from uuid import uuid4

from src.config import settings
from src.infrastructure.redis_client import RedisCache


class RateLimitService:
    """滑动窗口限流服务."""

    def __init__(self, redis_cache: RedisCache) -> None:
        self._redis = redis_cache

    async def is_allowed(
        self,
        identifier: str,
        endpoint: str,
        limit: int | None = None,
        window: int = 60,
    ) -> tuple[bool, dict]:
        """滑动窗口限流检查.

        Args:
            identifier: 限流标识（user_id 或 api_key_hash）
            endpoint: 请求端点
            limit: 限制次数（默认从配置读取）
            window: 窗口大小（秒）

        Returns:
            (是否允许, 限流信息)
        """
        limit = limit or settings.rate_limit_default
        now_ms = int(time.time() * 1000)
        window_start = now_ms - window * 1000
        key = f"pe:rate_limit:{identifier}:{endpoint}"
        request_id = str(uuid4())

        pipe = self._redis._redis.pipeline()
        # 移除窗口外的旧记录
        pipe.zremrangebyscore(key, 0, window_start)
        # 添加当前请求
        pipe.zadd(key, {request_id: now_ms})
        # 统计窗口内请求数
        pipe.zcard(key)
        # 设置 Key 过期时间
        pipe.expire(key, window)

        _, _, current_count, _ = await pipe.execute()

        if current_count > limit:
            # 超限，删除刚添加的记录
            await self._redis._redis.zrem(key, request_id)
            reset_at = window_start + window * 1000
            return False, {
                "limit": limit,
                "current": current_count - 1,
                "remaining": 0,
                "reset_at": reset_at,
            }

        return True, {
            "limit": limit,
            "current": current_count,
            "remaining": limit - current_count,
            "reset_at": window_start + window * 1000,
        }
