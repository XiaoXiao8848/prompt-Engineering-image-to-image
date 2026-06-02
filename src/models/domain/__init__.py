"""ORM 模型统一导入 — 确保 Alembic 和数据库初始化能发现所有表."""

from src.models.domain.generation import GenerationJob, GenerationResult
from src.models.domain.log import OperationLog, PromptHistory, RateLimitLog
from src.models.domain.product import Product
from src.models.domain.scene import Scene, SceneCategory
from src.models.domain.template import Template, TemplateVersion
from src.models.domain.user import ApiKey, User

__all__ = [
    "User",
    "ApiKey",
    "Product",
    "Scene",
    "SceneCategory",
    "Template",
    "TemplateVersion",
    "GenerationJob",
    "GenerationResult",
    "PromptHistory",
    "RateLimitLog",
    "OperationLog",
]
