"""Institution provisioning — Super Admin (platform_admin) only.

`POST /institutions` is the API-driven equivalent of
`scripts/provision_tenant.py`: insert the registry row, create the tenant
schema, run its Alembic chain, seed defaults (ARCHITECTURE.md §2).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.v1.endpoints.platform_auth import get_current_platform_admin
from app.db.tenancy import get_public_db
from app.models.public.institution import Institution
from app.models.public.platform_admin import PlatformAdmin
from app.schemas.institution import InstitutionCreate, InstitutionRead
from app.services.tenancy import (
    InvalidSlugError,
    TenantAlreadyExistsError,
    TenantProvisioningError,
    provision_tenant,
)

router = APIRouter()


@router.post("", response_model=InstitutionRead, status_code=status.HTTP_201_CREATED)
def create_institution(
    payload: InstitutionCreate,
    db: Session = Depends(get_public_db),
    _admin: PlatformAdmin = Depends(get_current_platform_admin),
) -> Institution:
    try:
        return provision_tenant(
            db,
            name=payload.name,
            code=payload.code,
            slug=payload.slug,
            contact_email=payload.contact_email,
            subscription_plan=payload.subscription_plan,
            timezone=payload.timezone,
            seed_demo=payload.seed_demo,
        )
    except InvalidSlugError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except TenantAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except TenantProvisioningError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)
        ) from exc


@router.get("", response_model=list[InstitutionRead])
def list_institutions(
    db: Session = Depends(get_public_db),
    _admin: PlatformAdmin = Depends(get_current_platform_admin),
) -> list[Institution]:
    return db.query(Institution).order_by(Institution.created_at.desc()).all()


@router.get("/{institution_id}", response_model=InstitutionRead)
def get_institution(
    institution_id: uuid.UUID,
    db: Session = Depends(get_public_db),
    _admin: PlatformAdmin = Depends(get_current_platform_admin),
) -> Institution:
    institution = db.get(Institution, institution_id)
    if institution is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found")
    return institution
