"""产品管理 API 路由."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from src.api.deps import CurrentUser, DBSession
from src.core.exceptions import NotFoundException, exception_to_http
from src.core.responses import PaginatedResponse, PaginationInfo, success
from src.schemas.product import (
    ProductBriefOut,
    ProductCreate,
    ProductListQuery,
    ProductOut,
    ProductUpdate,
)
from src.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["产品"])


@router.post("", response_model=dict)
async def create_product(data: ProductCreate, user: CurrentUser, db: DBSession) -> dict:
    """创建产品."""
    try:
        service = ProductService(db)
        product = await service.create(user_id=user["id"], data=data)
        return success(data=ProductOut.model_validate(product), message="创建成功")
    except ValueError as e:
        raise exception_to_http(ValueError(str(e))) from e


@router.get("", response_model=dict)
async def list_products(
    query: ProductListQuery = Depends(),
    user: CurrentUser = Depends(),
    db: DBSession = Depends(),
) -> dict:
    """查询产品列表."""
    service = ProductService(db)
    items, total = await service.list_by_user(
        user_id=user["id"],
        status=query.status,
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
        "data": [ProductOut.model_validate(p).model_dump() for p in items],
        "pagination": {
            "page": query.page,
            "page_size": query.page_size,
            "total": total,
            "total_pages": total_pages,
            "has_next": query.page < total_pages,
            "has_prev": query.page > 1,
        },
    }


@router.get("/{product_uuid}", response_model=dict)
async def get_product(product_uuid: str, user: CurrentUser, db: DBSession) -> dict:
    """获取产品详情."""
    try:
        service = ProductService(db)
        product = await service.get_by_uuid(user_id=user["id"], product_uuid=product_uuid)
        return success(data=ProductOut.model_validate(product), message="查询成功")
    except NotFoundException as e:
        raise exception_to_http(e) from e


@router.put("/{product_uuid}", response_model=dict)
async def update_product(
    product_uuid: str, data: ProductUpdate, user: CurrentUser, db: DBSession
) -> dict:
    """更新产品."""
    try:
        service = ProductService(db)
        product = await service.update(
            user_id=user["id"], product_uuid=product_uuid, data=data
        )
        return success(data=ProductOut.model_validate(product), message="更新成功")
    except NotFoundException as e:
        raise exception_to_http(e) from e


@router.delete("/{product_uuid}", response_model=dict)
async def delete_product(product_uuid: str, user: CurrentUser, db: DBSession) -> dict:
    """删除产品."""
    try:
        service = ProductService(db)
        await service.delete(user_id=user["id"], product_uuid=product_uuid)
        return success(message="删除成功")
    except NotFoundException as e:
        raise exception_to_http(e) from e
