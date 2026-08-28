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
from collections.abc import Callable, Generator

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import InvalidTokenError, TokenType, decode_token
from app.db.tenancy import get_db, get_program_db
from app.models.tenant.identity import Permission, Role, RolePermission, User, UserRole
from app.models.tenant.org import Program

PROGRAM_CODE_HEADER = "X-Program-Code"

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

    `scope_type="program"` matches an unscoped grant *or* a
    `scope_type="program"` grant scoped to the exact program the request's
    `X-Program-Code` header already resolved and authorized
    (`get_program_context`) — the same program a sibling
    `Depends(get_program_scoped_db)` on the same endpoint is bound to.
    `get_program_context` is itself cached per-request by FastAPI, so
    declaring it here doesn't re-run the header/grant resolution it already
    did for `get_program_scoped_db`.

    Historically this parameter was accepted but never actually resolved a
    concrete `scope_id` to compare against — `grants_satisfy_permission`
    requires an *exact* `(scope_type, scope_id)` match for a scoped grant,
    so passing `scope_type="program"` alone could never match any real
    scoped grant (`scope_id` stayed `None` on both sides only by
    coincidence-proof, never on purpose). That silently rejected every
    correctly *scoped* Program Coordinator/Administrator/Course
    Administrator grant on every program-scoped endpoint using this
    parameter — the intended, realistic way those roles get assigned — data
    that looked missing (COs, mappings, "Add" actions failing/hidden)
    was actually just permission checks that could never pass. Found live
    against a real Program Coordinator account.
    """
    if scope_type == "program":

        def program_scoped_dependency(
            current_user: User = Depends(get_current_user),
            db: Session = Depends(get_db),
            program: Program = Depends(get_program_context),
        ) -> User:
            if not user_has_permission(
                db, current_user.id, code, scope_type="program", scope_id=program.id
            ):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Missing required permission: {code}",
                )
            return current_user

        return program_scoped_dependency

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


def get_program_context(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Program:
    """Resolves the `X-Program-Code` header to a `Program` row and 403s
    unless the caller holds either an institution-wide grant (any permission,
    unscoped) or a grant scoped to this exact program
    (`scope_type="program"`, `scope_id==program.id`) — see
    docs/adr/0003-schema-per-program.md. This runs BEFORE any program-schema
    session is opened (`get_program_scoped_db` below depends on it), so an
    unauthorized caller never gets a query bound to a program schema they
    don't have a grant for, regardless of what specific permission the
    endpoint itself goes on to check.
    """
    program_code = request.headers.get(PROGRAM_CODE_HEADER)
    if not program_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"{PROGRAM_CODE_HEADER} header is required",
        )

    program = (
        db.query(Program)
        .filter(Program.code == program_code, Program.is_active.is_(True))
        .one_or_none()
    )
    if program is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Unknown or inactive program"
        )

    grants = get_user_permission_grants(db, current_user.id)
    authorized = any(scope_type is None for _code, scope_type, _scope_id in grants) or any(
        scope_type == "program" and scope_id == program.id
        for _code, scope_type, scope_id in grants
    )
    if not authorized:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No grant for this program",
        )

    # Stashed on request.state so endpoints can cross-check a payload's own
    # program_id/scope against the header-authorized program without
    # re-querying (see app.api.v1.endpoints.org.create_program_version).
    request.state.program_id = program.id
    request.state.program_code = program.code
    return program


def get_program_scoped_db(
    request: Request,
    program: Program = Depends(get_program_context),
) -> Generator[Session]:
    """FastAPI dependency: a session bound to both the institution schema and
    `program`'s schema. Use in place of `get_db` for endpoints touching
    program-specific tables (see docs/adr/0003-schema-per-program.md for the
    full table list)."""
    yield from get_program_db(request, program.code)


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
