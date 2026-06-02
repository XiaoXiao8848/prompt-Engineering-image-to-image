"""产品服务层 — 业务逻辑编排."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundException
from src.models.domain.product import Product
from src.repositories.product_repo import ProductRepository
from src.schemas.product import ProductCreate, ProductUpdate


class ProductService:
    """产品服务."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ProductRepository(session)

    async def create(self, user_id: int, data: ProductCreate) -> Product:
        """创建产品."""
        # 检查同用户下 product_id 是否已存在
        existing = await self._repo.get_by_product_id(user_id, data.product_id)
        if existing:
            raise ValueError(f"产品标识 '{data.product_id}' 已存在")

        product = Product(
            user_id=user_id,
            product_id=data.product_id,
            product_name=data.product_name,
            brand=data.brand,
            material=data.material,
            shape=data.shape,
            color=data.color,
            size=data.size,
            lock_tags=data.lock_tags,
            selling_points=data.selling_points,
            reference_image=data.reference_image.model_dump(),
            material_keywords=data.material_keywords,
            brand_tone=data.brand_tone,
            status="active",
        )
        await self._repo.create(product)
        return product

    async def get_by_uuid(self, user_id: int, product_uuid: str) -> Product:
        """获取产品详情（带权限校验）."""
        product = await self._repo.get_by_uuid(product_uuid)
        if not product or product.user_id != user_id:
            raise NotFoundException("产品不存在")
        if product.status == "deleted":
            raise NotFoundException("产品已删除")
        return product

    async def update(
        self, user_id: int, product_uuid: str, data: ProductUpdate
    ) -> Product:
        """更新产品."""
        product = await self.get_by_uuid(user_id, product_uuid)

        update_data = data.model_dump(exclude_unset=True)
        if "reference_image" in update_data and update_data["reference_image"]:
            update_data["reference_image"] = update_data["reference_image"].model_dump()

        await self._repo.update(product, **update_data)
        return product

    async def delete(self, user_id: int, product_uuid: str) -> None:
        """软删除产品."""
        product = await self.get_by_uuid(user_id, product_uuid)
        await self._repo.soft_delete(product)

    async def list_by_user(
        self,
        user_id: int,
        *,
        status: str | None = "active",
        keyword: str | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Product], int]:
        """查询用户的产品列表."""
        skip = (page - 1) * page_size
        return await self._repo.list_by_user(
            user_id,
            status=status,
            keyword=keyword,
            skip=skip,
            limit=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )
