"""Password hashing and JWT access/refresh token creation & verification."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.core.config import settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    return _pwd_context.verify(plain_password, password_hash)


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


class TokenPayload(BaseModel):
    sub: str  # user id (tenant user) or platform admin id
    type: TokenType
    institution_slug: str | None = None
    is_platform_admin: bool = False
    jti: str
    exp: datetime
    iat: datetime


class InvalidTokenError(Exception):
    """Raised when a JWT fails signature/expiry/shape validation."""


def _create_token(
    subject: str,
    token_type: TokenType,
    expires_delta: timedelta,
    institution_slug: str | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type.value,
        "institution_slug": institution_slug,
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + expires_delta,
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def create_access_token(
    subject: str,
    institution_slug: str | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    return _create_token(
        subject,
        TokenType.ACCESS,
        timedelta(minutes=settings.access_token_expire_minutes),
        institution_slug,
        extra_claims,
    )


def create_refresh_token(subject: str, institution_slug: str | None = None) -> str:
    return _create_token(
        subject,
        TokenType.REFRESH,
        timedelta(days=settings.refresh_token_expire_days),
        institution_slug,
    )


def decode_token(token: str) -> TokenPayload:
    """Decode and validate a JWT. Raises InvalidTokenError on any failure."""
    try:
        raw = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        return TokenPayload.model_validate(raw)
    except (JWTError, ValueError) as exc:
        raise InvalidTokenError(str(exc)) from exc
