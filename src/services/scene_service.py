"""场景服务层 — 业务逻辑编排."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundException
from src.models.domain.scene import Scene, SceneCategory
from src.repositories.scene_repo import SceneCategoryRepository, SceneRepository
from src.schemas.scene import SceneCreate, SceneUpdate


class SceneService:
    """场景服务."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = SceneRepository(session)
        self._category_repo = SceneCategoryRepository(session)

    async def create(self, user_id: int | None, data: SceneCreate) -> Scene:
        """创建场景."""
        # 检查 scene_id 是否已存在
        existing = await self._repo.get_by_scene_id(data.scene_id)
        if existing:
            raise ValueError(f"场景标识 '{data.scene_id}' 已存在")

        scene = Scene(
            scene_id=data.scene_id,
            name=data.name,
            description=data.description,
            lighting=data.lighting,
            background=data.background,
            props=data.props,
            atmosphere=data.atmosphere,
            keywords=data.keywords,
            category_id=data.category_id,
            is_builtin=False,
            is_public=data.is_public,
            created_by=user_id,
            status="active",
        )
        await self._repo.create(scene)
        return scene

    async def get_by_scene_id(self, scene_id: str) -> Scene:
        """根据场景标识获取场景."""
        scene = await self._repo.get_by_scene_id(scene_id)
        if not scene or scene.status != "active":
            raise NotFoundException("场景不存在")
        return scene

    async def get_by_uuid(self, scene_uuid: str) -> Scene:
        """根据 UUID 获取场景."""
        scene = await self._repo.get_by_uuid(scene_uuid)
        if not scene or scene.status != "active":
            raise NotFoundException("场景不存在")
        return scene

    async def update(
        self, scene_uuid: str, data: SceneUpdate, user_id: int | None = None
    ) -> Scene:
        """更新场景."""
        scene = await self.get_by_uuid(scene_uuid)

        # 内置场景只有管理员能修改
        if scene.is_builtin and user_id is not None:
            # TODO: 检查管理员权限
            pass

        update_data = data.model_dump(exclude_unset=True)
        await self._repo.update(scene, **update_data)
        return scene

    async def delete(self, scene_uuid: str) -> None:
        """软删除场景."""
        scene = await self.get_by_uuid(scene_uuid)
        await self._repo.soft_delete(scene)

    async def list_scenes(
        self,
        *,
        category_id: int | None = None,
        is_public: bool | None = True,
        keyword: str | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Scene], int]:
        """查询场景列表."""
        skip = (page - 1) * page_size
        return await self._repo.list_scenes(
            category_id=category_id,
            is_public=is_public,
            keyword=keyword,
            skip=skip,
            limit=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    async def list_by_ids(self, scene_ids: list[str]) -> list[Scene]:
        """根据 ID 列表查询场景."""
        return await self._repo.list_by_ids(scene_ids)


class SceneCategoryService:
    """场景分类服务."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = SceneCategoryRepository(session)

    async def create(self, name: str, description: str | None = None) -> SceneCategory:
        """创建分类."""
        category = SceneCategory(name=name, description=description)
        await self._repo.create(category)
        return category

    async def list_all(self) -> list[SceneCategory]:
        """查询所有分类."""
        return await self._repo.list_all_ordered()
