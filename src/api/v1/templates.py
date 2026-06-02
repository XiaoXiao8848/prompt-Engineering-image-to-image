"""模板管理 API 路由."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from src.api.deps import CurrentUser, DBSession
from src.core.exceptions import NotFoundException, ValidationException, exception_to_http
from src.core.responses import success
from src.schemas.template import (
    TemplateCreate,
    TemplateListQuery,
    TemplateOut,
    TemplateRenderRequest,
    TemplateRenderResponse,
    TemplateUpdate,
)
from src.services.template_service import TemplateService

router = APIRouter(prefix="/templates", tags=["模板"])


@router.post("", response_model=dict)
async def create_template(
    data: TemplateCreate, user: CurrentUser, db: DBSession
) -> dict:
    """创建模板."""
    service = TemplateService(db)
    template = await service.create(user_id=user["id"], data=data)
    return success(data=TemplateOut.model_validate(template), message="创建成功")


@router.get("", response_model=dict)
async def list_templates(
    query: TemplateListQuery = Depends(),
    db: DBSession = Depends(),
) -> dict:
    """查询模板列表."""
    service = TemplateService(db)
    items, total = await service.list_all(
        scene_id=query.scene_id,
        template_type=query.template_type,
        page=query.page,
        page_size=query.page_size,
        sort_by=query.sort_by,
        sort_order=query.sort_order,
    )
    total_pages = (total + query.page_size - 1) // query.page_size

    return {
        "code": "SUCCESS",
        "message": "查询成功",
        "data": [TemplateOut.model_validate(t).model_dump() for t in items],
        "pagination": {
            "page": query.page,
            "page_size": query.page_size,
            "total": total,
            "total_pages": total_pages,
            "has_next": query.page < total_pages,
            "has_prev": query.page > 1,
        },
    }


@router.get("/{template_uuid}", response_model=dict)
async def get_template(template_uuid: str, db: DBSession) -> dict:
    """获取模板详情."""
    try:
        service = TemplateService(db)
        template = await service.get_by_uuid(template_uuid)
        return success(data=TemplateOut.model_validate(template), message="查询成功")
    except NotFoundException as e:
        raise exception_to_http(e) from e


@router.put("/{template_uuid}", response_model=dict)
async def update_template(
    template_uuid: str, data: TemplateUpdate, user: CurrentUser, db: DBSession
) -> dict:
    """更新模板."""
    try:
        service = TemplateService(db)
        template = await service.update(
            template_uuid=template_uuid, data=data, user_id=user["id"]
        )
        return success(data=TemplateOut.model_validate(template), message="更新成功")
    except NotFoundException as e:
        raise exception_to_http(e) from e


@router.delete("/{template_uuid}", response_model=dict)
async def delete_template(
    template_uuid: str, user: CurrentUser, db: DBSession
) -> dict:
    """删除模板."""
    try:
        service = TemplateService(db)
        await service.delete(template_uuid, user_id=user["id"])
        return success(message="删除成功")
    except NotFoundException as e:
        raise exception_to_http(e) from e


@router.post("/{template_uuid}/render", response_model=dict)
async def render_template(
    template_uuid: str, data: TemplateRenderRequest, db: DBSession
) -> dict:
    """渲染模板."""
    try:
        service = TemplateService(db)
        rendered = await service.render(template_uuid, data)
        return success(
            data={"rendered": rendered, "template_uuid": template_uuid},
            message="渲染成功",
        )
    except (NotFoundException, ValidationException) as e:
        raise exception_to_http(e) from e


@router.get("/{template_uuid}/versions", response_model=dict)
async def list_template_versions(template_uuid: str, db: DBSession) -> dict:
    """查询模板版本历史."""
    try:
        service = TemplateService(db)
        versions = await service.list_versions(template_uuid)
        return success(
            data=[
                {
                    "id": v.id,
                    "version": v.version,
                    "content": v.content,
                    "change_note": v.change_note,
                    "created_at": v.created_at.isoformat(),
                }
                for v in versions
            ]
        )
    except NotFoundException as e:
        raise exception_to_http(e) from e


@router.post("/{template_uuid}/versions/{version}/restore", response_model=dict)
async def restore_template_version(
    template_uuid: str,
    version: int,
    user: CurrentUser,
    db: DBSession,
) -> dict:
    """回滚模板到指定版本."""
    try:
        service = TemplateService(db)
        template = await service.restore_version(
            template_uuid=template_uuid, version=version, user_id=user["id"]
        )
        return success(data=TemplateOut.model_validate(template), message="回滚成功")
    except NotFoundException as e:
        raise exception_to_http(e) from e
