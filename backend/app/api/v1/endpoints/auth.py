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
    hash_password,
    verify_password,
)
from app.db.tenancy import get_db
from app.middleware.audit import get_request_context
from app.models.tenant.identity import Role, User, UserRole
from app.schemas.auth import (
    ChangePasswordRequest,
    CurrentUserRead,
    LoginRequest,
    RefreshRequest,
    TokenResponse,
    UpdateMeRequest,
)
from app.services.audit import write_audit_log
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
        bio=current_user.bio,
        is_active=current_user.is_active,
        mfa_enabled=current_user.mfa_enabled,
        permissions=permission_codes,
        roles=[name for (name,) in role_names],
    )


@router.patch("/me", response_model=CurrentUserRead)
def update_me(
    payload: UpdateMeRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CurrentUserRead:
    """Self-service profile update — no permission grant required, any
    authenticated user may edit their own record (ARCHITECTURE.md §3 only
    gates *other* users' data; a user always owns their own)."""
    updates = payload.model_dump(exclude_unset=True)

    if "email" in updates and updates["email"] != current_user.email:
        conflict = db.query(User).filter(User.email == updates["email"]).one_or_none()
        if conflict is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")

    previous_value = {
        "full_name": current_user.full_name,
        "email": current_user.email,
        "bio": current_user.bio,
    }
    for field, value in updates.items():
        setattr(current_user, field, value)
    db.add(current_user)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="user.self_updated",
        entity_type="User",
        entity_id=current_user.id,
        previous_value=previous_value,
        new_value=updates,
        **get_request_context(request),
    )

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
        bio=current_user.bio,
        is_active=current_user.is_active,
        mfa_enabled=current_user.mfa_enabled,
        permissions=permission_codes,
        roles=[name for (name,) in role_names],
    )


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Current password is incorrect"
        )
    current_user.password_hash = hash_password(payload.new_password)
    db.add(current_user)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="user.password_changed",
        entity_type="User",
        entity_id=current_user.id,
        **get_request_context(request),
    )
