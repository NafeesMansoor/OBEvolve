"""Auth request/response schemas."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class CurrentUserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    bio: str | None = None
    is_active: bool
    mfa_enabled: bool
    permissions: list[str] = []
    roles: list[str] = []


class UpdateMeRequest(BaseModel):
    """Self-service profile update. Any authenticated user may update their
    own record this way — no permission grant required, unlike the
    admin-facing `PATCH /users/{id}` (app/schemas/identity.py UserUpdate),
    which is what other users' accounts go through."""

    full_name: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = None
    bio: str | None = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)
