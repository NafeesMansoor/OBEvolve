"""Platform-admin authentication (`public.platform_admins` — the only role
that spans institutions). Exempt from `TenancyMiddleware` since no tenant
has been resolved yet at this point — see `TENANT_EXEMPT_PREFIXES`.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import (
    InvalidTokenError,
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.db.tenancy import get_public_db
from app.models.public.platform_admin import PlatformAdmin
from app.schemas.auth import LoginRequest, PlatformAdminRead, RefreshRequest, TokenResponse

router = APIRouter()

_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="platform-auth/login", auto_error=False)


@router.post("/login", response_model=TokenResponse)
def platform_login(
    payload: LoginRequest, db: Session = Depends(get_public_db)
) -> TokenResponse:
    admin = db.query(PlatformAdmin).filter(PlatformAdmin.email == payload.email).one_or_none()
    valid_credentials = admin is not None and admin.is_active and verify_password(
        payload.password, admin.password_hash
    )
    if not valid_credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password"
        )

    extra = {"is_platform_admin": True}
    return TokenResponse(
        access_token=create_access_token(str(admin.id), institution_slug=None, extra_claims=extra),
        refresh_token=create_refresh_token(str(admin.id), institution_slug=None),
    )


@router.post("/refresh", response_model=TokenResponse)
def platform_refresh(
    payload: RefreshRequest, db: Session = Depends(get_public_db)
) -> TokenResponse:
    try:
        token_payload = decode_token(payload.refresh_token)
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token"
        ) from exc

    if token_payload.type != TokenType.REFRESH:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not a refresh token")

    admin = db.get(PlatformAdmin, uuid.UUID(token_payload.sub))
    if admin is None or not admin.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin not found")

    extra = {"is_platform_admin": True}
    return TokenResponse(
        access_token=create_access_token(str(admin.id), institution_slug=None, extra_claims=extra),
        refresh_token=create_refresh_token(str(admin.id), institution_slug=None),
    )


def get_current_platform_admin(
    token: str | None = Depends(_oauth2_scheme),
    db: Session = Depends(get_public_db),
) -> PlatformAdmin:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_token(token)
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        ) from exc

    if payload.type != TokenType.ACCESS or not payload.is_platform_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Platform admin token required"
        )

    admin = db.get(PlatformAdmin, uuid.UUID(payload.sub))
    if admin is None or not admin.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Admin not found")
    return admin


@router.get("/me", response_model=PlatformAdminRead)
def read_current_platform_admin(
    admin: PlatformAdmin = Depends(get_current_platform_admin),
) -> PlatformAdmin:
    return admin
