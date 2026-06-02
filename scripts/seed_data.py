#!/usr/bin/env python3
"""数据初始化脚本 — 将 YAML 场景和模板导入数据库.

用法:
    python scripts/seed_data.py
    # 或 Docker 中:
    docker-compose exec api python scripts/seed_data.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.config import settings
from src.models.domain.scene import Scene, SceneCategory
from src.models.domain.template import Template


async def seed_scenes(session: AsyncSession) -> None:
    """导入场景数据."""
    scenes_file = Path("scenes/scenes.yaml")
    if not scenes_file.exists():
        print(f"场景文件不存在: {scenes_file}")
        return

    with open(scenes_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    scenes_raw = data.get("scenes", [])
    print(f"发现 {len(scenes_raw)} 个场景")

    # 创建默认分类
    category = SceneCategory(name="默认分类", description="系统内置场景", sort_order=0)
    session.add(category)
    await session.flush()

    for s in scenes_raw:
        scene = Scene(
            scene_id=s["id"],
            name=s["name"],
            description=s.get("description", ""),
            lighting=s.get("lighting", ""),
            background=s.get("background", ""),
            props=s.get("props", []),
            atmosphere=s.get("atmosphere", ""),
            keywords=s.get("keywords", []),
            category_id=category.id,
            is_builtin=True,
            is_public=True,
            created_by=None,
            status="active",
        )
        session.add(scene)

    await session.commit()
    print(f"成功导入 {len(scenes_raw)} 个场景")


async def seed_templates(session: AsyncSession) -> None:
    """导入模板数据."""
    templates_dir = Path("prompts/templates")
    if not templates_dir.exists():
        print(f"模板目录不存在: {templates_dir}")
        return

    # 先查询所有场景
    from sqlalchemy import select
    result = await session.execute(select(Scene))
    scenes = {s.scene_id: s for s in result.scalars().all()}

    count = 0
    for file_path in templates_dir.glob("*.yaml"):
        scene_id = file_path.stem
        scene = scenes.get(scene_id)
        if not scene:
            print(f"跳过: 未找到场景 {scene_id}")
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        template = Template(
            scene_id=scene.id,
            name=f"{scene.name} 默认模板",
            template_type="positive",
            content=data.get("template", ""),
            variables=[],
            is_default=True,
            created_by=None,
            status="active",
        )
        session.add(template)

        # 负向提示词模板
        if data.get("negative_prompt"):
            neg_template = Template(
                scene_id=scene.id,
                name=f"{scene.name} 负向模板",
                template_type="negative",
                content=data["negative_prompt"],
                variables=[],
                is_default=True,
                created_by=None,
                status="active",
            )
            session.add(neg_template)

        count += 1

    await session.commit()
    print(f"成功导入 {count} 个场景模板")


async def main() -> int:
    """主函数."""
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        await seed_scenes(session)
        await seed_templates(session)

    await engine.dispose()
    print("数据初始化完成")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
