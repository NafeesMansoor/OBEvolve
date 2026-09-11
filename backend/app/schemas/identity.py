"""Schemas for tenant identity & RBAC (users, roles, permissions, grants)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=255)


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    mfa_enabled: bool
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime


class UserUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    is_active: bool | None = None


class PermissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    description: str
    module: str


class RoleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    is_system_role: bool
    is_active: bool
    permission_codes: list[str]


class RoleCreate(BaseModel):
    """Institution-level custom role ("user type") — always created with
    `is_system_role=False`. `permission_codes` must be a subset of the fixed
    catalogue (`app.core.permissions.PERMISSION_CODES`); an institution
    can't invent new permission codes, only compose existing ones into a
    new named role."""

    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    permission_codes: list[str] = Field(default_factory=list)


class RoleUpdate(BaseModel):
    """`is_active`/`description` are editable for every role — this is how a
    disabled system-seeded role gets re-enabled from the UI. `name` and
    `permission_codes` are additionally editable, but ONLY for a custom
    (`is_system_role=False`) role: a system role's name/permissions are
    defined in app/seed/default_roles.py (or, once seeded from it, the
    platform-level role-template catalogue), not per-tenant — the endpoint
    rejects attempts to set either field on a system role rather than
    silently ignoring them."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    is_active: bool | None = None
    permission_codes: list[str] | None = None


class UserRoleCreate(BaseModel):
    user_id: uuid.UUID
    role_id: uuid.UUID
    scope_type: str | None = None
    scope_id: uuid.UUID | None = None


class UserRoleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    role_id: uuid.UUID
    scope_type: str | None
    scope_id: uuid.UUID | None


class FacultyDirectoryEntry(BaseModel):
    """Minimal, non-sensitive shape (no email) for `GET /users/faculty-directory`
    — deliberately not the full `UserRead`."""

    id: uuid.UUID
    full_name: str
