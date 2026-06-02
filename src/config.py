"""全局配置管理 — 基于 Pydantic Settings，支持 .env 文件和环境变量覆盖."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类，所有配置项均有类型安全和默认值."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # === 应用 ===
    app_name: str = Field(default="Prompt Engine", alias="APP_NAME")
    debug: bool = Field(default=False, alias="DEBUG")
    env: Literal["development", "staging", "production"] = Field(default="development", alias="ENV")

    # === MySQL ===
    database_url: str = Field(
        default="mysql+asyncmy://root:rootpass@localhost:3306/prompt_engine",
        alias="DATABASE_URL",
    )
    db_pool_size: int = Field(default=10, alias="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=20, alias="DB_MAX_OVERFLOW")
    db_pool_timeout: int = Field(default=30, alias="DB_POOL_TIMEOUT")

    # === Redis ===
    redis_url: str = Field(default="redis://localhost:6379/0", alias="REDIS_URL")
    redis_pool_size: int = Field(default=50, alias="REDIS_POOL_SIZE")

    # === Celery ===
    celery_broker_url: str = Field(
        default="redis://localhost:6379/0", alias="CELERY_BROKER_URL"
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/0", alias="CELERY_RESULT_BACKEND"
    )

    # === LLM ===
    llm_provider: str = Field(default="deepseek", alias="LLM_PROVIDER")
    llm_api_key: str = Field(default="", alias="LLM_API_KEY")
    llm_base_url: str = Field(
        default="https://api.deepseek.com/v1", alias="LLM_BASE_URL"
    )
    llm_model: str = Field(default="deepseek-chat", alias="LLM_MODEL")
    llm_temperature: float = Field(default=0.7, alias="LLM_TEMPERATURE")
    llm_timeout: int = Field(default=30, alias="LLM_TIMEOUT")
    llm_max_retries: int = Field(default=3, alias="LLM_MAX_RETRIES")
    llm_cache_ttl: int = Field(default=86400, alias="LLM_CACHE_TTL")  # 24h

    # === JWT ===
    jwt_secret: str = Field(default="change-me-in-production", alias="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire: int = Field(default=3600, alias="JWT_ACCESS_TOKEN_EXPIRE")  # 1h
    jwt_refresh_token_expire: int = Field(
        default=604800, alias="JWT_REFRESH_TOKEN_EXPIRE"
    )  # 7d

    # === 限流 ===
    rate_limit_default: int = Field(default=60, alias="RATE_LIMIT_DEFAULT")  # 每分钟
    rate_limit_api_key: int = Field(default=1000, alias="RATE_LIMIT_API_KEY")

    # === S3 / MinIO (可选) ===
    storage_type: str = Field(default="local", alias="STORAGE_TYPE")
    s3_endpoint: str | None = Field(default=None, alias="S3_ENDPOINT")
    s3_access_key: str | None = Field(default=None, alias="S3_ACCESS_KEY")
    s3_secret_key: str | None = Field(default=None, alias="S3_SECRET_KEY")
    s3_bucket: str | None = Field(default=None, alias="S3_BUCKET")
    s3_region: str = Field(default="us-east-1", alias="S3_REGION")

    @property
    def is_dev(self) -> bool:
        return self.env == "development"

    @property
    def is_prod(self) -> bool:
        return self.env == "production"


@lru_cache
def get_settings() -> Settings:
    """获取配置单例，缓存避免重复解析."""
    return Settings()


settings = get_settings()
