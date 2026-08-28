"""Auth request/response schemas."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class GoogleLoginRequest(BaseModel):
    """`id_token` is the credential Google Identity Services hands the
    frontend after a successful Google sign-in — a signed JWT, not a
    password substitute. Verified server-side in
    app.api.v1.endpoints.auth.google_login before it's trusted."""

    id_token: str


class RefreshRequest(BaseModel):
    refresh_token: str


class PlatformAdminRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool


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
    # Flat, deduplicated union across every role — unchanged, still what
    # every existing permission check in the app should keep using.
    permissions: list[str] = []
    roles: list[str] = []
    # Role name -> that role's OWN permission codes (ignoring scope, same
    # simplification as `permissions`) — lets the frontend's "view as <role>"
    # switcher (lib/active-role-context.tsx) restrict `hasPermission()` to
    # just one role's grants instead of the full union, so previewing as
    # Faculty actually stops the UI from offering admin-only actions instead
    # of just de-emphasizing them. Not a backend security boundary (this
    # user genuinely holds every permission in `permissions` above,
    # regardless of which role is "active") — it's a self-service UI preview
    # for a real admin who wants to see what a lower-privileged role sees.
    role_permissions: dict[str, list[str]] = {}


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


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    detail: str


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8)
