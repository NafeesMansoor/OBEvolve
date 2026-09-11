"""`public.role_templates` — the platform-editable "default user types"
catalogue every newly-provisioned institution starts from.

Distinct from the per-tenant `roles` table (`app.models.tenant.identity.Role`):
this is ONE cross-institution catalogue, editable only by a platform admin
(`public.platform_admins`) — an institution admin can create their own
custom roles in their own tenant (`role.manage`, `POST /users/roles`), but
can never see or touch this table. `provision_tenant` reads it at
provisioning time to seed each new tenant's `roles` table, falling back to
the hardcoded `app.seed.default_roles.DEFAULT_ROLES` constant if it's empty
(local dev / a deployment that hasn't been seeded yet)."""

from __future__ import annotations

from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import PublicBase, TimestampMixin, UUIDPKMixin


class RoleTemplate(UUIDPKMixin, TimestampMixin, PublicBase):
    __tablename__ = "role_templates"
    __table_args__ = {"schema": "public"}

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    # A JSON array of codes from the fixed app.core.permissions.PERMISSION_CODES
    # catalogue — validated at write time (role_templates.py endpoints), not
    # enforced by a DB constraint, same posture as the tenant-level
    # RoleCreate/RoleUpdate validation in app/api/v1/endpoints/users.py.
    # Ignored (should be []) when all_permissions is True.
    permission_codes: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    # Mirrors app.seed.default_roles's `_ALL` sentinel (only "Legacy Tenant
    # Administrator" uses it today) — a separate boolean rather than
    # overloading permission_codes with a magic value, since the catalogue
    # itself can grow and a role meaning "every permission that will ever
    # exist" needs to keep meaning that.
    all_permissions: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Whether a tenant seeded from this template starts with the role
    # assignable (mirrors RoleDef.is_active) — every template is always
    # seeded into every new tenant; this only controls whether the
    # resulting Role shows up in that tenant's assignable-roles list.
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<RoleTemplate {self.name!r}>"
