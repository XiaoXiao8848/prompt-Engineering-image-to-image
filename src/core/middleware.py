"""FastAPI 中间件 — 限流、审计日志、CORS 等."""

from __future__ import annotations

import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from src.core.exceptions import RateLimitException
from src.infrastructure.redis_client import get_redis, RedisCache
from src.services.rate_limit_service import RateLimitService


class RateLimitMiddleware(BaseHTTPMiddleware):
    """全局 API 限流中间件."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip health check and docs
        path = request.url.path
        if path in ("/health", "/docs", "/redoc", "/openapi.json"):
            return await call_next(request)

        # Identify by user id or client IP
        user = getattr(request.state, "user", None)
        identifier = str(user["id"]) if user else request.client.host if request.client else "unknown"
        endpoint = f"{request.method}:{path}"

        redis = get_redis()
        rate_limit = RateLimitService(RedisCache(redis))
        allowed, info = await rate_limit.is_allowed(identifier, endpoint)

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(info["reset_at"])

        if not allowed:
            raise RateLimitException()

        return response


class AuditLogMiddleware(BaseHTTPMiddleware):
    """操作审计日志中间件 — 记录所有 API 请求."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        response = await call_next(request)
        duration = round((time.time() - start_time) * 1000, 2)

        # Skip health check
        path = request.url.path
        if path in ("/health", "/docs", "/redoc", "/openapi.json"):
            return response

        # Async log to database (fire and forget, don't block response)
        user = getattr(request.state, "user", None)
        user_id = user["id"] if user else None

        # Use asyncio.create_task for non-blocking logging
        import asyncio
        from datetime import datetime, timezone

        from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

        from src.config import settings
        from src.models.domain.log import OperationLog

        async def _log():
            try:
                engine = create_async_engine(settings.database_url, pool_pre_ping=True, pool_size=2)
                session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
                async with session_factory() as session:
                    log = OperationLog(
                        user_id=user_id,
                        action=request.method,
                        resource_type=path.split("/")[2] if len(path.split("/")) > 2 else "unknown",
                        resource_id=path,
                        details={
                            "status_code": response.status_code,
                            "duration_ms": duration,
                            "query_params": str(request.query_params),
                        },
                        client_ip=request.client.host if request.client else None,
                        user_agent=request.headers.get("user-agent"),
                        created_at=datetime.now(timezone.utc),
                    )
                    session.add(log)
                    await session.commit()
                await engine.dispose()
            except Exception:
                pass

        asyncio.create_task(_log())
        return response
