"""Tenant-user authentication: login, refresh, /me.

Every token issued here carries the `institution_slug` of the tenant the
user logged into (from `request.state.institution_slug`, resolved by
`TenancyMiddleware`); `get_current_user` re-checks that claim against the
tenant of whatever request the token is later used on, so a token minted
for one institution cannot be replayed against another (defense in depth on
top of schema isolation itself).
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.security import (
    InvalidTokenError,
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.db.tenancy import get_db
from app.models.tenant.identity import Role, User, UserRole
from app.schemas.auth import CurrentUserRead, LoginRequest, RefreshRequest, TokenResponse
from app.services.rbac import get_current_user, get_user_permission_grants

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest, request: Request, db: Session = Depends(get_db)
) -> TokenResponse:
    user = db.query(User).filter(User.email == payload.email).one_or_none()
    valid_credentials = user is not None and user.is_active and verify_password(
        payload.password, user.password_hash
    )
    if not valid_credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password"
        )

    tenant_slug: str = request.state.institution_slug
    user.last_login_at = datetime.now(UTC)
    db.add(user)

    return TokenResponse(
        access_token=create_access_token(str(user.id), institution_slug=tenant_slug),
        refresh_token=create_refresh_token(str(user.id), institution_slug=tenant_slug),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    payload: RefreshRequest, request: Request, db: Session = Depends(get_db)
) -> TokenResponse:
    try:
        token_payload = decode_token(payload.refresh_token)
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token"
        ) from exc

    if token_payload.type != TokenType.REFRESH:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not a refresh token")

    tenant_slug: str = request.state.institution_slug
    if token_payload.institution_slug != tenant_slug:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is not valid for this institution",
        )

    user = db.get(User, uuid.UUID(token_payload.sub))
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return TokenResponse(
        access_token=create_access_token(str(user.id), institution_slug=tenant_slug),
        refresh_token=create_refresh_token(str(user.id), institution_slug=tenant_slug),
    )


@router.get("/me", response_model=CurrentUserRead)
def read_me(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> CurrentUserRead:
    grants = get_user_permission_grants(db, current_user.id)
    permission_codes = sorted({code for code, _scope_type, _scope_id in grants})

    role_names = (
        db.query(Role.name)
        .join(UserRole, UserRole.role_id == Role.id)
        .filter(UserRole.user_id == current_user.id)
        .distinct()
        .all()
    )

    return CurrentUserRead(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        is_active=current_user.is_active,
        mfa_enabled=current_user.mfa_enabled,
        permissions=permission_codes,
        roles=[name for (name,) in role_names],
    )
