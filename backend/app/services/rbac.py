"""RBAC resolution: current-user auth dependency + `require_permission()`.

Permission checks are always by code (`require_permission("curriculum.approve")`),
never by role name (ARCHITECTURE.md §3). `user_roles.scope_type`/`scope_id`
let a grant be scoped to one org unit; `user_has_permission` treats an
institution-wide grant (`scope_type` is None, i.e. unscoped) as satisfying any
scope, and a scoped grant as satisfying only that specific scope — this is the
resolution ARCHITECTURE.md §3 describes as "against the resource being
accessed".
"""

from __future__ import annotations

import uuid
from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import InvalidTokenError, TokenType, decode_token
from app.db.tenancy import get_db
from app.models.tenant.identity import Permission, Role, RolePermission, User, UserRole

# tokenUrl is documentational only (schema-per-tenant login is tenant-scoped,
# not a single global endpoint) — the actual token is validated against the
# tenant resolved for this request by TenancyMiddleware.
_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login", auto_error=False)


def get_current_user(
    request: Request,
    token: str | None = Depends(_oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
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
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    if payload.type != TokenType.ACCESS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Not an access token"
        )

    tenant_slug = getattr(request.state, "institution_slug", None)
    if payload.institution_slug != tenant_slug:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is not valid for this institution",
        )

    user = db.get(User, uuid.UUID(payload.sub))
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user


def get_user_permission_grants(
    db: Session, user_id: uuid.UUID
) -> list[tuple[str, str | None, uuid.UUID | None]]:
    """Return `(permission_code, scope_type, scope_id)` for every permission
    this user holds through any of their role grants."""
    rows = (
        db.query(Permission.code, UserRole.scope_type, UserRole.scope_id)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(Role, Role.id == RolePermission.role_id)
        .join(UserRole, UserRole.role_id == Role.id)
        .filter(UserRole.user_id == user_id)
        .all()
    )
    return [(code, scope_type, scope_id) for code, scope_type, scope_id in rows]


def grants_satisfy_permission(
    grants: list[tuple[str, str | None, uuid.UUID | None]],
    code: str,
    *,
    scope_type: str | None = None,
    scope_id: uuid.UUID | None = None,
) -> bool:
    """Pure scope-matching logic, factored out of `user_has_permission` so it
    is unit-testable without a database (see tests/unit/test_rbac.py).

    True if `code` appears unscoped (institution-wide) or scoped to the
    exact `(scope_type, scope_id)` being checked.
    """
    for grant_code, grant_scope_type, grant_scope_id in grants:
        if grant_code != code:
            continue
        if grant_scope_type is None:
            return True  # unscoped grant = institution-wide
        if scope_type is not None and grant_scope_type == scope_type and grant_scope_id == scope_id:
            return True
    return False


def user_has_permission(
    db: Session,
    user_id: uuid.UUID,
    code: str,
    *,
    scope_type: str | None = None,
    scope_id: uuid.UUID | None = None,
) -> bool:
    """True if the user holds `code` unscoped (institution-wide) or scoped to
    the exact `(scope_type, scope_id)` being checked."""
    grants = get_user_permission_grants(db, user_id)
    return grants_satisfy_permission(grants, code, scope_type=scope_type, scope_id=scope_id)


def require_permission(
    code: str,
    *,
    scope_type: str | None = None,
) -> Callable[..., User]:
    """FastAPI dependency factory: 403s unless the current user holds `code`.

    `scope_type`, when given, is matched against unscoped or same-type scoped
    grants only; resolving the concrete `scope_id` of the resource being
    accessed is left to the endpoint (pass it via a wrapping dependency) —
    Phase 1 endpoints operate at institution scope, so this parameter exists
    for later phases to opt into resource-scoped checks without changing the
    dependency's shape.
    """

    def dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        if not user_has_permission(db, current_user.id, code, scope_type=scope_type):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {code}",
            )
        return current_user

    return dependency


def require_any_grant(*codes: str) -> Callable[..., User]:
    """FastAPI dependency factory: 403s unless the current user holds AT
    LEAST ONE grant (scoped or unscoped) for any of `codes` — regardless of
    scope_type/scope_id.

    Deliberately more lenient than `require_permission`, which only matches
    an *unscoped* grant when the caller doesn't supply a `scope_type` (see
    its docstring). That's the right behavior for e.g. `program.approve`,
    where the endpoint doesn't yet resolve which specific program is being
    acted on. It's the wrong behavior for the raw-data console
    (app/services/raw_data.py): a Program Administrator's
    `raw_data.manage_scoped` grant is *always* scoped (scope_type='program'),
    and the console does its own fine-grained per-table/per-row scope
    resolution internally — the endpoint just needs to know "does this user
    hold *some* raw_data grant at all" before doing that finer-grained work.
    """

    def dependency(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> User:
        grants = get_user_permission_grants(db, current_user.id)
        if not any(code in codes for code, _scope_type, _scope_id in grants):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: one of {', '.join(codes)}",
            )
        return current_user

    return dependency
