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


class RoleUpdate(BaseModel):
    """Only `is_active` is editable for a system-seeded role — name/
    description/permissions for the built-in roles are defined in
    app/seed/default_roles.py, not per-tenant. This exists so a disabled
    role (see that module's docstring) can be re-enabled from the UI."""

    is_active: bool | None = None
    description: str | None = None


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
