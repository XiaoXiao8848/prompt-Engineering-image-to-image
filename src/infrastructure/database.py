"""SQLAlchemy 异步数据库连接管理 — 引擎、会话、连接池."""

from __future__ import annotations

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from src.config import settings

# 注意：不要在模块顶层导入 models，避免循环导入
# 模型注册到 Base.metadata 在 Alembic env.py 和 init_db() 中完成

# 创建异步引擎
engine = create_async_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_pre_ping=True,  # 连接前 ping，避免使用已断开的连接
    echo=settings.debug,  # 调试模式打印 SQL
    future=True,
)

# 异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

# 声明基类
Base = declarative_base()


async def init_db() -> None:
    """初始化数据库：创建所有表（开发环境可用，生产环境建议用 Alembic 迁移）."""
    # 延迟导入模型，避免循环导入，同时确保 Base.metadata 注册所有表
    from src.models.domain import (  # noqa: F401
        ApiKey,
        GenerationJob,
        GenerationResult,
        OperationLog,
        Product,
        PromptHistory,
        RateLimitLog,
        Scene,
        SceneCategory,
        Template,
        TemplateVersion,
        User,
    )

    async with engine.begin() as conn:
        # 注意：生产环境请使用 Alembic 管理迁移，不要自动创建表
        if settings.is_dev:
            await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """关闭数据库引擎."""
    await engine.dispose()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI Depends 用的数据库会话生成器.

    使用方式:
        async def handler(db: AsyncSession = Depends(get_db_session)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # 仅在事务仍处于活跃状态时提交（未被手动 rollback）
            if session.is_active:
                await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
