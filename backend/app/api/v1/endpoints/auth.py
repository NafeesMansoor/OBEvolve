"""Tenant-user authentication: login, refresh, /me.

Every token issued here carries the `institution_slug` of the tenant the
user logged into (from `request.state.institution_slug`, resolved by
`TenancyMiddleware`); `get_current_user` re-checks that claim against the
tenant of whatever request the token is later used on, so a token minted
for one institution cannot be replayed against another (defense in depth on
top of schema isolation itself).
"""

from __future__ import annotations

import hashlib
import logging
import secrets
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
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
from app.models.tenant.identity import (
    PasswordResetToken,
    Permission,
    Role,
    RolePermission,
    User,
    UserRole,
)
from app.schemas.auth import (
    ChangePasswordRequest,
    CurrentUserRead,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    GoogleLoginRequest,
    LoginRequest,
    RefreshRequest,
    ResetPasswordRequest,
    TokenResponse,
    UpdateMeRequest,
)
from app.services.audit import write_audit_log
from app.services.email import send_email
from app.services.google_oauth import GoogleTokenError, verify_google_id_token
from app.services.rbac import get_current_user, get_user_permission_grants

_PASSWORD_RESET_TOKEN_TTL = timedelta(hours=1)
_GENERIC_FORGOT_PASSWORD_MESSAGE = (
    "If that email is registered, a reset link has been sent."
)

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


@router.post("/google", response_model=TokenResponse)
def google_login(
    payload: GoogleLoginRequest, request: Request, db: Session = Depends(get_db)
) -> TokenResponse:
    """Alternate login path alongside `/login` — does not replace or
    require a password. Any user account whose email Google reports as
    verified can sign in this way (typically a faculty/institutional Google
    Workspace account the admin already entered when creating the user);
    accounts without a matching email keep using password login exactly as
    before."""
    try:
        email = verify_google_id_token(payload.id_token)
    except GoogleTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    user = db.query(User).filter(User.email == email).one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="This Google account is not linked to an active user in this institution.",
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


def _build_current_user_read(db: Session, current_user: User) -> CurrentUserRead:
    grants = get_user_permission_grants(db, current_user.id)
    permission_codes = sorted({code for code, _scope_type, _scope_id in grants})

    # Per-role breakdown (role name -> that role's own permission codes,
    # ignoring scope like `permissions` above) — see CurrentUserRead's
    # `role_permissions` docstring for why this exists. LEFT JOINed from
    # RolePermission/Permission (not inner-joined) so a role the user holds
    # that happens to grant zero permissions still shows up with an empty
    # list, instead of silently vanishing from `roles` entirely.
    role_perm_rows = (
        db.query(Role.name, Permission.code)
        .join(UserRole, UserRole.role_id == Role.id)
        .filter(UserRole.user_id == current_user.id)
        .outerjoin(RolePermission, RolePermission.role_id == Role.id)
        .outerjoin(Permission, Permission.id == RolePermission.permission_id)
        .distinct()
        .all()
    )
    role_permissions: dict[str, list[str]] = {}
    for role_name, code in role_perm_rows:
        codes = role_permissions.setdefault(role_name, [])
        if code is not None:
            codes.append(code)
    for codes in role_permissions.values():
        codes.sort()

    return CurrentUserRead(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        bio=current_user.bio,
        is_active=current_user.is_active,
        mfa_enabled=current_user.mfa_enabled,
        permissions=permission_codes,
        roles=sorted(role_permissions),
        role_permissions=role_permissions,
    )


@router.get("/me", response_model=CurrentUserRead)
def read_me(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> CurrentUserRead:
    return _build_current_user_read(db, current_user)


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

    return _build_current_user_read(db, current_user)


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


def _hash_reset_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(
    payload: ForgotPasswordRequest, request: Request, db: Session = Depends(get_db)
) -> ForgotPasswordResponse:
    """Always returns the same generic 200 response, whether or not `email`
    is registered in this tenant — never reveal account existence to an
    unauthenticated caller (standard anti-enumeration practice)."""
    tenant_slug: str = request.state.institution_slug
    user = db.query(User).filter(User.email == payload.email).one_or_none()

    if user is not None and user.is_active:
        raw_token = secrets.token_urlsafe(32)
        reset_token = PasswordResetToken(
            user_id=user.id,
            token_hash=_hash_reset_token(raw_token),
            expires_at=datetime.now(UTC) + _PASSWORD_RESET_TOKEN_TTL,
        )
        db.add(reset_token)
        db.flush()

        reset_link = (
            f"{settings.frontend_origin}/reset-password"
            f"?token={raw_token}&institution={tenant_slug}"
        )
        send_email(
            to=user.email,
            subject="Reset your OBEvolve password",
            body=(
                "We received a request to reset your OBEvolve password.\n\n"
                f"Reset it here (valid for 1 hour): {reset_link}\n\n"
                "If you did not request this, you can safely ignore this email."
            ),
        )

    return ForgotPasswordResponse(detail=_GENERIC_FORGOT_PASSWORD_MESSAGE)


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT)
def reset_password(
    payload: ResetPasswordRequest, request: Request, db: Session = Depends(get_db)
) -> None:
    token_hash = _hash_reset_token(payload.token)
    now = datetime.now(UTC)

    reset_token = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.token_hash == token_hash)
        .one_or_none()
    )
    if (
        reset_token is None
        or reset_token.used_at is not None
        or reset_token.expires_at < now
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This reset link is invalid, expired, or has already been used.",
        )

    user = db.get(User, reset_token.user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This reset link is invalid, expired, or has already been used.",
        )

    user.password_hash = hash_password(payload.new_password)
    db.add(user)

    reset_token.used_at = now
    db.add(reset_token)

    # Invalidate any other still-usable reset tokens for this user, so an
    # old leaked link can't be reused after a successful reset.
    other_tokens = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.id != reset_token.id,
            PasswordResetToken.used_at.is_(None),
        )
        .all()
    )
    for token in other_tokens:
        token.used_at = now
        db.add(token)

    db.flush()
    write_audit_log(
        db,
        user_id=user.id,
        action="user.password_reset",
        entity_type="User",
        entity_id=user.id,
        **get_request_context(request),
    )
