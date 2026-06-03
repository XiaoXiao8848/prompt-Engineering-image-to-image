"""Tests for AuthService."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import AlreadyExistsException, AuthenticationException
from src.services.auth_service import AuthService


@pytest.mark.asyncio
async def test_register_success(db_session: AsyncSession) -> None:
    """Test successful user registration."""
    service = AuthService(db_session)
    user = await service.register(
        username="testuser",
        email="test@example.com",
        password="password123",
        display_name="Test User",
    )
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.display_name == "Test User"
    assert user.role == "user"
    assert user.status == "active"


@pytest.mark.asyncio
async def test_register_duplicate_username(db_session: AsyncSession) -> None:
    """Test registration with duplicate username raises exception."""
    service = AuthService(db_session)
    await service.register(
        username="testuser",
        email="test1@example.com",
        password="password123",
    )
    with pytest.raises(AlreadyExistsException):
        await service.register(
            username="testuser",
            email="test2@example.com",
            password="password123",
        )


@pytest.mark.asyncio
async def test_login_success(db_session: AsyncSession) -> None:
    """Test successful login returns tokens."""
    service = AuthService(db_session)
    await service.register(
        username="testuser",
        email="test@example.com",
        password="password123",
    )
    tokens = await service.login("testuser", "password123")
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(db_session: AsyncSession) -> None:
    """Test login with wrong password raises exception."""
    service = AuthService(db_session)
    await service.register(
        username="testuser",
        email="test@example.com",
        password="password123",
    )
    with pytest.raises(AuthenticationException):
        await service.login("testuser", "wrongpassword")


@pytest.mark.asyncio
async def test_login_nonexistent_user(db_session: AsyncSession) -> None:
    """Test login with non-existent user raises exception."""
    service = AuthService(db_session)
    with pytest.raises(AuthenticationException):
        await service.login("nonexistent", "password123")


@pytest.mark.asyncio
async def test_update_user(db_session: AsyncSession) -> None:
    """Test updating user info."""
    service = AuthService(db_session)
    user = await service.register(
        username="testuser",
        email="test@example.com",
        password="password123",
    )
    updated = await service.update_user(
        user_id=user.id,
        display_name="Updated Name",
        avatar_url="https://example.com/avatar.png",
    )
    assert updated.display_name == "Updated Name"
    assert updated.avatar_url == "https://example.com/avatar.png"
