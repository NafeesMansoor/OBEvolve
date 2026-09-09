"""Schemas for `public.institutions` — Super Admin / platform-level surface."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class InstitutionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    code: str = Field(min_length=1, max_length=50)
    slug: str = Field(min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")
    contact_email: EmailStr
    subscription_plan: str | None = None
    timezone: str = "UTC"
    seed_demo: bool = False
    # Optional: also create the tenant's Institute Admin account in the same
    # request (app.seed.institution_admin) — all-or-nothing, since granting
    # "Institution Administrator" to a name-only or email-only account makes
    # no sense.
    admin_full_name: str | None = Field(default=None, min_length=1, max_length=255)
    admin_email: EmailStr | None = None

    @model_validator(mode="after")
    def _admin_fields_together(self) -> InstitutionCreate:
        if bool(self.admin_full_name) != bool(self.admin_email):
            raise ValueError("admin_full_name and admin_email must be given together.")
        return self


class InstitutionUpdate(BaseModel):
    """Self-service update of the caller's OWN institution (see `GET`/`PATCH
    /org/institution` — app.api.v1.endpoints.org) — deliberately a narrower
    field set than `InstitutionCreate`: `slug`/`schema_name`/`status` are
    platform-admin-only concerns (changing them touches tenant routing and
    provisioning state), not something an Institution Administrator edits
    from within their own tenant."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    contact_email: EmailStr | None = None
    subscription_plan: str | None = None
    logo_url: str | None = None
    timezone: str | None = None


class InstitutionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    code: str
    slug: str
    schema_name: str
    status: str
    subscription_plan: str | None
    contact_email: str
    logo_url: str | None
    timezone: str
    created_at: datetime
    updated_at: datetime


class InstitutionCreateResult(BaseModel):
    """`POST /institutions`'s response: the institution, plus the Institute
    Admin's one-time temporary password when an admin was requested —
    never retrievable again after this response (same one-time-reveal shape
    as `program_roles.FacultyCreateResult`)."""

    institution: InstitutionRead
    admin_temporary_password: str | None = None
