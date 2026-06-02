"""产品数据访问层."""

from __future__ import annotations

from sqlalchemy import asc, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.domain.product import Product
from src.repositories.base import BaseRepository


class ProductRepository(BaseRepository[Product]):
    """产品 Repository."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Product)

    async def get_by_uuid(self, product_uuid: str) -> Product | None:
        """根据 UUID 查询."""
        stmt = select(Product).where(Product.product_uuid == product_uuid)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_product_id(self, user_id: int, product_id: str) -> Product | None:
        """根据用户 ID + 产品标识查询."""
        stmt = select(Product).where(
            Product.user_id == user_id,
            Product.product_id == product_id,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: int,
        *,
        status: str | None = None,
        keyword: str | None = None,
        skip: int = 0,
        limit: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Product], int]:
        """查询用户的产品列表，返回 (列表, 总数)."""
        stmt = select(Product).where(Product.user_id == user_id)

        if status:
            stmt = stmt.where(Product.status == status)
        else:
            stmt = stmt.where(Product.status != "deleted")

        if keyword:
            stmt = stmt.where(
                Product.product_name.contains(keyword)
                | Product.product_id.contains(keyword)
            )

        # 排序
        sort_column = getattr(Product, sort_by, Product.created_at)
        order_func = desc if sort_order == "desc" else asc
        stmt = stmt.order_by(order_func(sort_column))

        # 总数
        total = await self.count(stmt)

        # 分页
        stmt = stmt.offset(skip).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total
