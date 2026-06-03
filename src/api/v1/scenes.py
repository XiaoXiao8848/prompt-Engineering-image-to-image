"""场景管理 API 路由."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from src.api.deps import AdminUser, CurrentUser, DBSession, OptionalUser
from src.core.exceptions import NotFoundException, ValidationException, exception_to_http
from src.core.responses import success
from src.schemas.scene import (
    SceneBriefOut,
    SceneCategoryCreate,
    SceneCategoryOut,
    SceneCreate,
    SceneListQuery,
    SceneOut,
    SceneUpdate,
)
from src.services.scene_service import SceneCategoryService, SceneService

router = APIRouter(prefix="/scenes", tags=["场景"])


@router.post("/categories", response_model=dict)
async def create_category(
    data: SceneCategoryCreate, user: AdminUser, db: DBSession
) -> dict:
    """创建场景分类（管理员）."""
    service = SceneCategoryService(db)
    category = await service.create(name=data.name, description=data.description)
    return success(
        data={"id": category.id, "name": category.name, "description": category.description},
        message="创建成功",
    )


@router.get("/categories", response_model=dict)
async def list_categories(db: DBSession) -> dict:
    """查询所有场景分类."""
    service = SceneCategoryService(db)
    categories = await service.list_all()
    return success(
        data=[
            {"id": c.id, "name": c.name, "description": c.description, "sort_order": c.sort_order}
            for c in categories
        ]
    )


@router.post("", response_model=dict)
async def create_scene(data: SceneCreate, user: CurrentUser, db: DBSession) -> dict:
    """创建场景."""
    try:
        service = SceneService(db)
        scene = await service.create(user_id=user["id"], data=data)
        return success(data=SceneOut.model_validate(scene), message="创建成功")
    except ValueError as e:
        raise exception_to_http(ValidationException(str(e))) from e


@router.get("", response_model=dict)
async def list_scenes(
    db: DBSession,
    query: SceneListQuery = Depends(),
) -> dict:
    """查询场景列表."""
    service = SceneService(db)
    items, total = await service.list_scenes(
        category_id=query.category_id,
        is_public=query.is_public,
        keyword=query.keyword,
        page=query.page,
        page_size=query.page_size,
        sort_by=query.sort_by,
        sort_order=query.sort_order,
    )
    total_pages = (total + query.page_size - 1) // query.page_size

    return {
        "code": "SUCCESS",
        "message": "查询成功",
        "data": [SceneOut.model_validate(s).model_dump() for s in items],
        "pagination": {
            "page": query.page,
            "page_size": query.page_size,
            "total": total,
            "total_pages": total_pages,
            "has_next": query.page < total_pages,
            "has_prev": query.page > 1,
        },
    }


@router.get("/{scene_uuid}", response_model=dict)
async def get_scene(scene_uuid: str, db: DBSession) -> dict:
    """获取场景详情."""
    try:
        service = SceneService(db)
        scene = await service.get_by_uuid(scene_uuid)
        return success(data=SceneOut.model_validate(scene), message="查询成功")
    except NotFoundException as e:
        raise exception_to_http(e) from e


@router.put("/{scene_uuid}", response_model=dict)
async def update_scene(
    scene_uuid: str,
    data: SceneUpdate,
    user: CurrentUser,
    db: DBSession,
) -> dict:
    """更新场景."""
    try:
        service = SceneService(db)
        scene = await service.update(
            scene_uuid,
            data,
            user_id=user["id"],
            is_admin=user.get("role") == "admin",
        )
        return success(data=SceneOut.model_validate(scene), message="更新成功")
    except NotFoundException as e:
        raise exception_to_http(e) from e


@router.delete("/{scene_uuid}", response_model=dict)
async def delete_scene(scene_uuid: str, user: CurrentUser, db: DBSession) -> dict:
    """删除场景."""
    try:
        service = SceneService(db)
        await service.delete(
            scene_uuid,
            user_id=user["id"],
            is_admin=user.get("role") == "admin",
        )
        return success(message="删除成功")
    except NotFoundException as e:
        raise exception_to_http(e) from e
