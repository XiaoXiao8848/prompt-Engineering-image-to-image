"""用户与认证相关 Pydantic Schema."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

from src.schemas.base import BaseSchema, IDMixin, TimestampMixin


# ========== 用户 ==========

class UserCreate(BaseSchema):
    """用户注册请求."""

    username: str = Field(min_length=3, max_length=50, description="登录名")
    email: EmailStr = Field(description="邮箱")
    password: str = Field(min_length=8, max_length=128, description="密码")
    display_name: str | None = Field(default=None, max_length=100, description="显示名称")


class UserUpdate(BaseSchema):
    """用户更新请求."""

    display_name: str | None = Field(default=None, max_length=100)
    avatar_url: str | None = Field(default=None, max_length=500)


class UserOut(IDMixin, TimestampMixin):
    """用户信息响应（不含敏感字段）."""

    username: str
    email: EmailStr
    display_name: str | None
    avatar_url: str | None
    role: Literal["admin", "user", "api"]
    status: Literal["active", "inactive", "banned"]
    quota_daily: int
    quota_used_today: int


class UserInDB(UserOut):
    """数据库中的完整用户信息（含敏感字段，不对外暴露）."""

    password_hash: str


# ========== 认证 ==========

class LoginRequest(BaseSchema):
    """登录请求."""

    username: str = Field(description="用户名或邮箱")
    password: str = Field(description="密码")


class TokenResponse(BaseSchema):
    """Token 响应."""

    access_token: str = Field(description="访问令牌")
    refresh_token: str = Field(description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")
    expires_in: int = Field(description="过期时间（秒）")


class RefreshRequest(BaseSchema):
    """刷新 Token 请求."""

    refresh_token: str = Field(description="刷新令牌")


class ChangePasswordRequest(BaseSchema):
    """修改密码请求."""

    old_password: str = Field(description="旧密码")
    new_password: str = Field(min_length=8, max_length=128, description="新密码")


# ========== API Key ==========

class ApiKeyCreate(BaseSchema):
    """创建 API Key 请求."""

    name: str = Field(max_length=100, description="Key 名称")
    permissions: list[str] | None = Field(default=None, description="权限列表")
    rate_limit: int | None = Field(default=None, description="每分钟限制")
    expires_at: datetime | None = Field(default=None, description="过期时间")


class ApiKeyOut(IDMixin):
    """API Key 响应（不含完整 Key）."""

    name: str
    key_prefix: str
    permissions: list[str] | None
    rate_limit: int
    last_used_at: datetime | None
    expires_at: datetime | None
    created_at: datetime


class ApiKeyCreateResponse(BaseSchema):
    """创建 API Key 响应（仅创建时返回完整 Key）."""

    id: int
    name: str
    api_key: str = Field(description="完整 API Key（仅显示一次）")
    key_prefix: str
    expires_at: datetime | None
    created_at: datetime
