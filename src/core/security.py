"""安全相关工具 — JWT 生成/验证、密码哈希."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from src.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证明文密码与哈希是否匹配."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def get_password_hash(password: str) -> str:
    """生成 bcrypt 密码哈希."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_access_token(
    subject: str | int,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """创建 JWT Access Token.

    Args:
        subject: 主题（通常是用户 ID）
        expires_delta: 自定义过期时间
        extra_claims: 额外声明

    Returns:
        JWT 字符串
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            seconds=settings.jwt_access_token_expire
        )

    to_encode: dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "type": "access",
        "iat": datetime.now(timezone.utc),
    }
    if extra_claims:
        to_encode.update(extra_claims)

    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def create_refresh_token(
    subject: str | int,
    expires_delta: timedelta | None = None,
) -> str:
    """创建 JWT Refresh Token."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            seconds=settings.jwt_refresh_token_expire
        )

    to_encode: dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "type": "refresh",
        "iat": datetime.now(timezone.utc),
    }

    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def decode_token(token: str) -> dict[str, Any] | None:
    """解码并验证 JWT Token.

    Returns:
        解码后的 payload，如果验证失败返回 None
    """
    try:
        payload = jwt.decode(
            token, settings.jwt_secret, algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        return None


def generate_api_key() -> str:
    """生成随机 API Key（格式: pe_xxxxxxxx...）.

    Returns:
        原始 API Key（仅显示一次，需立即保存哈希值）
    """
    import secrets

    raw_key = "pe_" + secrets.token_urlsafe(32)
    return raw_key


def hash_api_key(raw_key: str) -> str:
    """对 API Key 进行 SHA256 哈希存储."""
    import hashlib

    return hashlib.sha256(raw_key.encode()).hexdigest()
