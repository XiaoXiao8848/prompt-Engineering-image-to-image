"""Pytest shared fixtures."""

from __future__ import annotations

from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.infrastructure.database import Base
import importlib.util
_spec = importlib.util.spec_from_file_location("legacy_models", str(Path(__file__).parent.parent / "src" / "models.py"))
_legacy_models = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_legacy_models)
ProductConfig = _legacy_models.ProductConfig
SceneDefinition = _legacy_models.SceneDefinition


# ── Database fixtures ──

@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    """Create a test database session using SQLite in-memory."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, checkfirst=True)

    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session:
        yield session

    await engine.dispose()


# ── 路径 fixtures ──

@pytest.fixture
def fixtures_dir() -> Path:
    """测试 fixtures 目录."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def product_path(fixtures_dir: Path) -> Path:
    """测试产品配置文件路径."""
    return fixtures_dir / "test_product.yaml"


@pytest.fixture
def scenes_path(fixtures_dir: Path) -> Path:
    """测试场景库文件路径."""
    return fixtures_dir / "test_scenes.yaml"


@pytest.fixture
def templates_dir(fixtures_dir: Path) -> Path:
    """测试模板目录路径."""
    return fixtures_dir / "templates"


@pytest.fixture
def meta_template_path(fixtures_dir: Path) -> Path:
    """测试 LLM 元提示词模板路径."""
    return fixtures_dir / "meta_template.yaml"


# ── 数据模型 fixtures ──

@pytest.fixture
def sample_product() -> ProductConfig:
    """内存中的示例产品配置."""
    return ProductConfig(
        product_id="test_serum",
        product_name="测试精华液",
        brand="TestBrand",
        material="磨砂玻璃",
        shape="圆柱形",
        color="琥珀色",
        size="30ml",
        lock_tags="amber glass bottle, frosted texture, gold cap",
        selling_points=["深层修护", "提亮肤色"],
        material_keywords=["磨砂玻璃", "琥珀色"],
        brand_tone="高端简约",
    )


@pytest.fixture
def sample_scene_studio() -> SceneDefinition:
    """示例棚拍场景."""
    return SceneDefinition(
        id="test_studio",
        name="测试棚拍",
        description="纯白背景棚拍测试",
        lighting="柔光箱双侧打光",
        background="纯白无缝背景",
        props=["反光板", "柔光布"],
        atmosphere="干净专业",
        keywords=["棚拍", "白底"],
    )


@pytest.fixture
def sample_scene_lifestyle() -> SceneDefinition:
    """示例生活场景."""
    return SceneDefinition(
        id="test_lifestyle",
        name="测试生活场景",
        description="家居生活场景测试",
        lighting="自然窗光",
        background="木质桌面",
        props=["绿植", "咖啡杯"],
        atmosphere="温馨自然",
        keywords=["生活", "家居"],
    )
