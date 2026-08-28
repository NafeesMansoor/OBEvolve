"""Basic user + role management within a tenant."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.tenancy import get_db
from app.middleware.audit import get_request_context
from app.models.tenant.identity import FacultyProfile, Role, User, UserRole
from app.schemas.identity import (
    FacultyDirectoryEntry,
    RoleRead,
    RoleUpdate,
    UserCreate,
    UserRead,
    UserRoleCreate,
    UserRoleRead,
    UserUpdate,
)
from app.services.audit import write_audit_log
from app.services.rbac import get_current_user, require_permission

router = APIRouter()


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("user.manage")),
) -> User:
    if db.query(User).filter(User.email == payload.email).one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")

    user = User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        is_active=True,
    )
    db.add(user)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="user.created",
        entity_type="User",
        entity_id=user.id,
        new_value={"email": payload.email, "full_name": payload.full_name},
        **get_request_context(request),
    )
    return user


@router.get("", response_model=list[UserRead])
def list_users(
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("user.view")),
) -> list[User]:
    return db.query(User).order_by(User.full_name).all()


@router.get("/user-roles", response_model=list[UserRoleRead])
def list_user_roles(
    user_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("role.view")),
) -> list[UserRole]:
    """Was missing entirely until now — the console could POST/DELETE role
    grants but had no way to list existing ones, so the frontend fell back
    to a localStorage-only cache of grants made in that same browser (now
    removed — see frontend/src/features/organization/UsersTab.tsx).
    `user_id` narrows to one user's grants; omitted, returns every grant in
    the tenant (small enough — grants are one row per user/role/scope, not
    a high-cardinality table — to not need pagination yet).

    MUST be registered before `GET /{user_id}` below: both are single path
    segments, and Starlette matches routes in registration order — with
    this route later in the file, `GET /user-roles` was being swallowed by
    `/{user_id}` first (tried to parse "user-roles" as a UUID, 422'd)."""
    query = db.query(UserRole)
    if user_id is not None:
        query = query.filter(UserRole.user_id == user_id)
    return query.all()


@router.get("/faculty-directory", response_model=list[FacultyDirectoryEntry])
def list_faculty_directory(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[FacultyDirectoryEntry]:
    """Open to any authenticated tenant user, not gated behind `user.view`
    (the full user-directory permission) — Faculty/Course Coordinator/
    Program Coordinator hold `section.manage` and legitimately need to pick
    a colleague when assigning faculty to a section, without holding
    `user.view`. Deliberately narrower than `UserRead` (id + name only, no
    email) and filtered to users with a `FacultyProfile`, so this isn't a
    backdoor around the real user directory — just enough to populate that
    one picker (and resolve names for already-assigned faculty)."""
    rows = (
        db.query(User.id, User.full_name)
        .join(FacultyProfile, FacultyProfile.user_id == User.id)
        .order_by(User.full_name)
        .all()
    )
    return [FacultyDirectoryEntry(id=row.id, full_name=row.full_name) for row in rows]


@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("user.view")),
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("user.manage")),
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    previous_value = {"full_name": user.full_name, "is_active": user.is_active}
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(user, field, value)
    db.add(user)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="user.updated",
        entity_type="User",
        entity_id=user.id,
        previous_value=previous_value,
        new_value=updates,
        **get_request_context(request),
    )
    return user


@router.get("/roles/all", response_model=list[RoleRead])
def list_roles(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("role.view")),
) -> list[Role]:
    """Disabled roles (`is_active=False`) are excluded by default so they
    stop cluttering the assignment picker; pass `?include_inactive=true` to
    see them too (e.g. to audit who still holds a since-disabled role, or to
    re-enable one)."""
    query = db.query(Role)
    if not include_inactive:
        query = query.filter(Role.is_active.is_(True))
    return query.order_by(Role.name).all()


@router.patch("/roles/{role_id}", response_model=RoleRead)
def update_role(
    role_id: uuid.UUID,
    payload: RoleUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role.manage")),
) -> Role:
    role = db.get(Role, role_id)
    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    previous_value = {"is_active": role.is_active, "description": role.description}
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(role, field, value)
    db.add(role)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="role.updated",
        entity_type="Role",
        entity_id=role.id,
        previous_value=previous_value,
        new_value=updates,
        **get_request_context(request),
    )
    return role


@router.post("/user-roles", response_model=UserRoleRead, status_code=status.HTTP_201_CREATED)
def assign_role(
    payload: UserRoleCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role.manage")),
) -> UserRole:
    if db.get(User, payload.user_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if db.get(Role, payload.role_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    grant = UserRole(**payload.model_dump())
    db.add(grant)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="user_role.assigned",
        entity_type="UserRole",
        entity_id=grant.id,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return grant


@router.delete("/user-roles/{user_role_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_role(
    user_role_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("role.manage")),
) -> None:
    grant = db.get(UserRole, user_role_id)
    if grant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role grant not found")

    previous_value = {
        "user_id": str(grant.user_id),
        "role_id": str(grant.role_id),
        "scope_type": grant.scope_type,
        "scope_id": str(grant.scope_id) if grant.scope_id else None,
    }
    db.delete(grant)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="user_role.revoked",
        entity_type="UserRole",
        entity_id=user_role_id,
        previous_value=previous_value,
        **get_request_context(request),
    )
