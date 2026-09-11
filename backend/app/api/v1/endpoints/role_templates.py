"""`public.role_templates` CRUD — platform-admin only.

The default "user type" catalogue every newly-provisioned institution starts
from (see `app.models.public.role_template.RoleTemplate` and
`app.services.tenancy.provision_tenant`'s use of it). An institution admin
never reaches this router — their own custom-role surface is
`POST/PATCH /users/roles` (tenant-scoped, `app/api/v1/endpoints/users.py`),
a structurally separate table in a structurally separate schema.
"""

from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.platform_auth import get_current_platform_admin
from app.core.permissions import PERMISSION_CODES, PERMISSIONS
from app.db.tenancy import get_public_db
from app.models.public.institution import Institution
from app.models.public.platform_admin import PlatformAdmin
from app.models.public.role_template import RoleTemplate
from app.schemas.role_template import (
    PermissionCatalogueEntry,
    RoleTemplateCreate,
    RoleTemplateRead,
    RoleTemplateResyncResult,
    RoleTemplateUpdate,
)
from app.services.tenancy import resync_role_templates

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/permission-catalogue", response_model=list[PermissionCatalogueEntry])
def list_permission_catalogue(
    _admin: PlatformAdmin = Depends(get_current_platform_admin),
) -> list[PermissionCatalogueEntry]:
    """The fixed code-level catalogue, not a DB query — a platform admin has
    no tenant session to read the `permissions` table from (that table
    doesn't even exist until a tenant schema is provisioned). Powers the
    permission-checkbox list on the role-template create/edit form, same
    role `GET /users/permissions` plays for the tenant-scoped custom-role
    form.

    MUST be registered before `PATCH /{template_id}` below — same
    single-path-segment collision every other `/{id}`-shaped route in this
    codebase has to watch for (see `users.py`'s `/permissions` route)."""
    return [
        PermissionCatalogueEntry(code=p.code, description=p.description, module=p.module)
        for p in sorted(PERMISSIONS, key=lambda p: (p.module, p.code))
    ]


def _validate_codes(permission_codes: list[str], all_permissions: bool) -> None:
    if all_permissions:
        return
    unknown = [c for c in permission_codes if c not in PERMISSION_CODES]
    if unknown:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unknown permission code(s): {', '.join(unknown)}",
        )


@router.get("", response_model=list[RoleTemplateRead])
def list_role_templates(
    db: Session = Depends(get_public_db),
    _admin: PlatformAdmin = Depends(get_current_platform_admin),
) -> list[RoleTemplate]:
    return db.query(RoleTemplate).order_by(RoleTemplate.name).all()


@router.post("", response_model=RoleTemplateRead, status_code=status.HTTP_201_CREATED)
def create_role_template(
    payload: RoleTemplateCreate,
    db: Session = Depends(get_public_db),
    _admin: PlatformAdmin = Depends(get_current_platform_admin),
) -> RoleTemplate:
    if db.query(RoleTemplate).filter(RoleTemplate.name == payload.name).one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="A role template with this name exists"
        )
    _validate_codes(payload.permission_codes, payload.all_permissions)

    template = RoleTemplate(
        name=payload.name,
        description=payload.description,
        permission_codes=[] if payload.all_permissions else payload.permission_codes,
        all_permissions=payload.all_permissions,
        is_active=True,
    )
    db.add(template)
    db.commit()
    return template


@router.patch("/{template_id}", response_model=RoleTemplateRead)
def update_role_template(
    template_id: uuid.UUID,
    payload: RoleTemplateUpdate,
    db: Session = Depends(get_public_db),
    _admin: PlatformAdmin = Depends(get_current_platform_admin),
) -> RoleTemplate:
    template = db.get(RoleTemplate, template_id)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role template not found")

    updates = payload.model_dump(exclude_unset=True)
    all_permissions = updates.get("all_permissions", template.all_permissions)
    permission_codes = updates.get("permission_codes", template.permission_codes)
    _validate_codes(permission_codes, all_permissions)
    if all_permissions:
        updates["permission_codes"] = []

    for field, value in updates.items():
        setattr(template, field, value)
    db.add(template)
    db.commit()
    return template


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role_template(
    template_id: uuid.UUID,
    db: Session = Depends(get_public_db),
    _admin: PlatformAdmin = Depends(get_current_platform_admin),
) -> None:
    """Permanently removes a template from the catalogue — unlike the
    tenant-level `Role`/`RoleUpdate` surface (deactivate-only, no delete;
    see `app/api/v1/endpoints/users.py`), a hard delete is safe here because
    `role_templates` has no foreign-key relationship to anything: it's only
    ever read by value at provisioning/resync time and copied into each
    tenant's own `roles` table, which this does not touch. Deleting a
    template only affects institutions provisioned (or resynced) after this
    point — it does not remove the role from any tenant that already has
    it (that tenant's own `Role` row is untouched; only future seeding
    stops offering it)."""
    template = db.get(RoleTemplate, template_id)
    if template is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role template not found")
    db.delete(template)
    db.commit()


@router.post("/resync", response_model=RoleTemplateResyncResult)
def resync_role_templates_endpoint(
    db: Session = Depends(get_public_db),
    _admin: PlatformAdmin = Depends(get_current_platform_admin),
) -> RoleTemplateResyncResult:
    """Re-applies the current `role_templates` catalogue to every already-
    provisioned institution — `provision_tenant` only reads it once, at
    creation time, so an edit made here (create/update above) has no effect
    on existing tenants until this is run. Same all-institutions loop as
    `scripts/resync_role_templates.py` (kept as a separate CLI entry point
    for ops contexts without a running server), applied one tenant at a
    time so one failure doesn't abort the rest."""
    institutions = db.query(Institution).order_by(Institution.slug).all()
    succeeded: list[str] = []
    failed: list[str] = []
    for institution in institutions:
        try:
            resync_role_templates(institution.schema_name)
        except Exception:
            logger.exception(
                "role_templates.resync_failed", extra={"slug": institution.slug}
            )
            failed.append(institution.slug)
            continue
        succeeded.append(institution.slug)
    return RoleTemplateResyncResult(succeeded=succeeded, failed=failed)
