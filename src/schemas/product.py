"""产品配置相关 Pydantic Schema."""

from __future__ import annotations

from pydantic import Field

from src.schemas.base import BaseSchema, IDMixin, ListQueryParams, TimestampMixin


class ReferenceImage(BaseSchema):
    """参考图说明."""

    description: str = Field(default="", description="图片描述")
    angle: str = Field(default="", description="拍摄角度")
    lighting: str = Field(default="", description="光线说明")


class ProductCreate(BaseSchema):
    """创建产品请求."""

    product_id: str = Field(min_length=1, max_length=64, description="产品标识")
    product_name: str = Field(min_length=1, max_length=200, description="产品名称")
    brand: str | None = Field(default=None, max_length=100, description="品牌")
    material: str | None = Field(default=None, max_length=200, description="材质")
    shape: str | None = Field(default=None, max_length=200, description="形状")
    color: str | None = Field(default=None, max_length=200, description="颜色")
    size: str | None = Field(default=None, max_length=50, description="尺寸")
    lock_tags: str = Field(min_length=1, description="产品外观锁定标签")
    selling_points: list[str] = Field(default_factory=list, description="核心卖点")
    reference_image: ReferenceImage = Field(default_factory=ReferenceImage, description="参考图")
    material_keywords: list[str] = Field(default_factory=list, description="材质关键词")
    brand_tone: str | None = Field(default=None, max_length=200, description="品牌调性")


class ProductUpdate(BaseSchema):
    """更新产品请求."""

    product_name: str | None = Field(default=None, max_length=200)
    brand: str | None = Field(default=None, max_length=100)
    material: str | None = Field(default=None, max_length=200)
    shape: str | None = Field(default=None, max_length=200)
    color: str | None = Field(default=None, max_length=200)
    size: str | None = Field(default=None, max_length=50)
    lock_tags: str | None = Field(default=None)
    selling_points: list[str] | None = Field(default=None)
    reference_image: ReferenceImage | None = Field(default=None)
    material_keywords: list[str] | None = Field(default=None)
    brand_tone: str | None = Field(default=None, max_length=200)
    status: str | None = Field(default=None, pattern=r"^(active|archived)$")


class ProductOut(IDMixin, TimestampMixin):
    """产品详情响应."""

    product_uuid: str
    product_id: str
    product_name: str
    brand: str | None
    material: str | None
    shape: str | None
    color: str | None
    size: str | None
    lock_tags: str
    selling_points: list[str]
    reference_image: ReferenceImage
    material_keywords: list[str]
    brand_tone: str | None
    status: str


class ProductListQuery(ListQueryParams):
    """产品列表查询参数."""

    status: str | None = Field(default="active", description="状态筛选")


class ProductBriefOut(BaseSchema):
    """产品简要信息（用于下拉选择等场景）."""

    product_uuid: str
    product_id: str
    product_name: str
    brand: str | None
    status: str
