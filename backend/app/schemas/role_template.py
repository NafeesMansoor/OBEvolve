"""Schemas for `public.role_templates` — platform-admin-only surface."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RoleTemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    permission_codes: list[str] = Field(default_factory=list)
    all_permissions: bool = False


class RoleTemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None
    permission_codes: list[str] | None = None
    all_permissions: bool | None = None
    is_active: bool | None = None


class RoleTemplateRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    permission_codes: list[str]
    all_permissions: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime


class RoleTemplateResyncResult(BaseModel):
    """Response for `POST /role-templates/resync` — per-institution outcome
    of re-applying the current template catalogue to every already-
    provisioned tenant."""

    succeeded: list[str]
    failed: list[str]


class PermissionCatalogueEntry(BaseModel):
    """The fixed, code-level catalogue (`app.core.permissions.PERMISSIONS`)
    — not a DB row (unlike the tenant-scoped `Permission` model/`PermissionRead`
    in `app.schemas.identity`), since a platform admin has no tenant session
    to query one from. Same underlying data, different surface."""

    model_config = ConfigDict(from_attributes=True)

    code: str
    description: str
    module: str
