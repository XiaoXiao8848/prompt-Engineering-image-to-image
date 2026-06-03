"""Alembic migration environment configuration — supports async SQLAlchemy."""

from __future__ import annotations

import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path

# Add project root to Python path so 'src' can be imported
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import application config and models
from src.config import settings
from src.infrastructure.database import Base

# Import all models to ensure Base.metadata contains all tables
from src.models.domain import *  # noqa: F401,F403

# Alembic Config 对象
config = context.config

# 覆盖数据库 URL
config.set_main_option("sqlalchemy.url", settings.database_url)

# 日志配置
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 目标 metadata
# 所有模型都继承自 Base，因此 Base.metadata 包含所有表
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """离线模式运行迁移 — 不创建实际连接."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """在已有连接上执行迁移."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """异步模式运行迁移."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """在线模式运行迁移 — 创建实际数据库连接."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
