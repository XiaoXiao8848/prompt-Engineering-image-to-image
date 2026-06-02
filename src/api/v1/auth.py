"""认证相关 API 路由."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import ActiveUser, CurrentUser, DBSession, get_db
from src.core.exceptions import exception_to_http
from src.core.responses import success
from src.schemas.user import (
    ApiKeyCreate,
    ApiKeyCreateResponse,
    ApiKeyOut,
    ChangePasswordRequest,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    UserCreate,
    UserOut,
    UserUpdate,
)
from src.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/register", response_model=dict)
async def register(data: UserCreate, db: DBSession) -> dict:
    """用户注册."""
    try:
        service = AuthService(db)
        user = await service.register(
            username=data.username,
            email=data.email,
            password=data.password,
            display_name=data.display_name,
        )
        return success(data=UserOut.model_validate(user), message="注册成功")
    except Exception as e:
        if hasattr(e, "code"):
            raise exception_to_http(e) from e
        raise


@router.post("/login", response_model=dict)
async def login(data: LoginRequest, db: DBSession) -> dict:
    """用户登录."""
    try:
        service = AuthService(db)
        tokens = await service.login(
            username=data.username,
            password=data.password,
        )
        return success(data=tokens, message="登录成功")
    except Exception as e:
        if hasattr(e, "code"):
            raise exception_to_http(e) from e
        raise


@router.post("/refresh", response_model=dict)
async def refresh(data: RefreshRequest, db: DBSession) -> dict:
    """刷新 Access Token."""
    try:
        service = AuthService(db)
        tokens = await service.refresh_token(data.refresh_token)
        return success(data=tokens, message="刷新成功")
    except Exception as e:
        if hasattr(e, "code"):
            raise exception_to_http(e) from e
        raise


@router.get("/me", response_model=dict)
async def get_me(user: CurrentUser) -> dict:
    """获取当前用户信息."""
    return success(data=user, message="获取成功")


@router.put("/me", response_model=dict)
async def update_me(data: UserUpdate, user: CurrentUser, db: DBSession) -> dict:
    """更新当前用户信息."""
    # TODO: 实现用户信息更新
    return success(data=user, message="更新成功")


@router.post("/api-keys", response_model=dict)
async def create_api_key(
    data: ApiKeyCreate, user: CurrentUser, db: DBSession
) -> dict:
    """创建 API Key."""
    service = AuthService(db)
    api_key, raw_key = await service.create_api_key(
        user_id=user["id"],
        name=data.name,
        permissions=data.permissions,
        rate_limit=data.rate_limit,
        expires_at=data.expires_at,
    )
    return success(
        data={
            "id": api_key.id,
            "name": api_key.name,
            "api_key": raw_key,
            "key_prefix": api_key.key_prefix,
            "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
            "created_at": api_key.created_at.isoformat(),
        },
        message="API Key 创建成功，请妥善保存，此 Key 仅显示一次",
    )
