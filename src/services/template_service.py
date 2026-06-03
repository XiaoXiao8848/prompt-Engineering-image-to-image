"""模板服务层 — 业务逻辑编排."""

from __future__ import annotations

from jinja2 import Template as JinjaTemplate
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundException, ValidationException
from src.models.domain.template import Template, TemplateVersion
from src.repositories.template_repo import TemplateRepository, TemplateVersionRepository
from src.schemas.template import TemplateCreate, TemplateRenderRequest, TemplateUpdate


class TemplateService:
    """模板服务."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = TemplateRepository(session)
        self._version_repo = TemplateVersionRepository(session)

    async def create(self, user_id: int | None, data: TemplateCreate) -> Template:
        """创建模板."""
        # 检查默认模板唯一性
        if data.is_default:
            existing = await self._repo.get_default_by_scene(data.scene_id, data.template_type)
            if existing:
                raise ValueError("该场景已存在默认模板，请先取消现有默认模板")

        template = Template(
            scene_id=data.scene_id,
            name=data.name,
            template_type=data.template_type,
            content=data.content,
            variables=data.variables,
            is_default=data.is_default,
            created_by=user_id,
            status="active",
        )
        await self._repo.create(template)
        return template

    async def get_by_uuid(self, template_uuid: str) -> Template:
        """获取模板详情."""
        template = await self._repo.get_by_uuid(template_uuid)
        if not template or template.status != "active":
            raise NotFoundException("模板不存在")
        return template

    async def update(
        self, template_uuid: str, data: TemplateUpdate, user_id: int | None = None
    ) -> Template:
        """更新模板（自动创建版本历史）."""
        template = await self.get_by_uuid(template_uuid)

        # 保存版本历史（如果内容显式传入且与当前不同）
        if data.content is not None and data.content != template.content:
            latest_version = await self._version_repo.get_latest_version(template.id)
            version = TemplateVersion(
                template_id=template.id,
                version=latest_version + 1,
                content=template.content,
                changed_by=user_id,
                change_note="内容更新",
            )
            await self._version_repo.create(version)

        update_data = data.model_dump(exclude_unset=True)
        await self._repo.update(template, **update_data)
        return template

    async def delete(
        self, template_uuid: str, user_id: int | None = None, is_admin: bool = False
    ) -> None:
        """软删除模板."""
        template = await self.get_by_uuid(template_uuid)
        # 系统模板（created_by 为 None）需要管理员权限
        if template.created_by is None and not is_admin:
            from src.core.exceptions import AuthorizationException
            raise AuthorizationException("系统模板需要管理员权限才能删除")
        # 非系统模板只能由创建者删除
        if template.created_by is not None and template.created_by != user_id:
            from src.core.exceptions import AuthorizationException
            raise AuthorizationException("无权删除该模板")
        await self._repo.soft_delete(template)

    async def render(
        self, template_uuid: str, data: TemplateRenderRequest
    ) -> str:
        """渲染模板."""
        template = await self.get_by_uuid(template_uuid)
        try:
            jinja_tpl = JinjaTemplate(template.content)
            rendered = jinja_tpl.render(**data.variables)
            return rendered
        except Exception as e:
            raise ValidationException(f"模板渲染失败: {e}")

    async def list_by_scene(
        self, scene_id: int, template_type: str | None = None
    ) -> list[Template]:
        """查询场景下的模板."""
        return await self._repo.list_by_scene(
            scene_id, template_type=template_type
        )

    async def list_all(
        self,
        *,
        scene_id: int | None = None,
        template_type: str | None = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> tuple[list[Template], int]:
        """查询所有模板."""
        skip = (page - 1) * page_size
        return await self._repo.list_all_active(
            scene_id=scene_id,
            template_type=template_type,
            skip=skip,
            limit=page_size,
            sort_by=sort_by,
            sort_order=sort_order,
        )

    async def list_versions(self, template_uuid: str) -> list[TemplateVersion]:
        """查询模板版本历史."""
        template = await self.get_by_uuid(template_uuid)
        return await self._version_repo.list_by_template(template.id)

    async def restore_version(
        self, template_uuid: str, version: int, user_id: int | None = None
    ) -> Template:
        """回滚到指定版本."""
        template = await self.get_by_uuid(template_uuid)

        versions = await self._version_repo.list_by_template(template.id)
        target = next((v for v in versions if v.version == version), None)
        if not target:
            raise NotFoundException(f"版本 {version} 不存在")

        # 保存当前版本到历史
        latest_version = await self._version_repo.get_latest_version(template.id)
        new_version = TemplateVersion(
            template_id=template.id,
            version=latest_version + 1,
            content=template.content,
            changed_by=user_id,
            change_note=f"回滚到版本 {version}",
        )
        await self._version_repo.create(new_version)

        # 恢复内容
        await self._repo.update(template, content=target.content)
        return template
