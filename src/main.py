"""FastAPI 应用入口 — Prompt Engine 服务端."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.core.middleware import AuditLogMiddleware, RateLimitMiddleware
from src.infrastructure.database import close_db, init_db
from src.infrastructure.redis_client import close_redis, init_redis


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """应用生命周期管理：启动时初始化资源，关闭时释放资源."""
    # Startup
    await init_db()
    await init_redis()
    # Cache warmup
    await _warmup_cache()
    yield
    # Shutdown
    await close_redis()
    await close_db()


async def _warmup_cache() -> None:
    """预热缓存：加载公开场景和模板到 Redis."""
    from src.infrastructure.database import AsyncSessionLocal
    from src.infrastructure.redis_client import get_redis, RedisCache
    from src.repositories.scene_repo import SceneRepository
    from src.repositories.template_repo import TemplateRepository

    try:
        async with AsyncSessionLocal() as session:
            redis = RedisCache(get_redis())
            # Warmup public scenes
            scene_repo = SceneRepository(session)
            scenes = await scene_repo.list_scenes(is_public=True, limit=100)
            for scene in scenes:
                await redis.set_json(
                    f"pe:scene:{scene.scene_id}",
                    {"name": scene.name, "description": scene.description},
                    ttl=300,
                )
            # Warmup templates
            template_repo = TemplateRepository(session)
            templates, _ = await template_repo.list_all_active(limit=100)
            for template in templates:
                await redis.set_json(
                    f"pe:template:{template.template_uuid}",
                    {"name": template.name, "content": template.content},
                    ttl=600,
                )
    except Exception:
        pass


def create_application() -> FastAPI:
    """工厂函数：创建并配置 FastAPI 应用实例."""
    app = FastAPI(
        title=settings.app_name,
        description="基于 MySQL + Redis 的多场景图生图提示词生成服务",
        version="0.2.0",
        docs_url="/docs" if settings.is_dev else None,
        redoc_url="/redoc" if settings.is_dev else None,
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.is_dev else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rate Limit Middleware
    app.add_middleware(RateLimitMiddleware)

    # Audit Log Middleware
    app.add_middleware(AuditLogMiddleware)

    # 注册路由
    from src.api.v1 import auth, jobs, products, prompts, scenes, templates

    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(products.router, prefix="/api/v1")
    app.include_router(scenes.router, prefix="/api/v1")
    app.include_router(templates.router, prefix="/api/v1")
    app.include_router(prompts.router, prefix="/api/v1")
    app.include_router(jobs.router, prefix="/api/v1")

    @app.get("/health", tags=["健康检查"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok", "version": "0.2.0"}

    return app


app = create_application()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.is_dev,
        workers=1 if settings.is_dev else 4,
    )
