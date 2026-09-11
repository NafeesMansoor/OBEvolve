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
from app.db.session import session_scope
from app.db.tenancy import get_public_db
from app.models.public.institution import Institution
from app.models.public.platform_admin import PlatformAdmin
from app.models.tenant.identity import Role, User, UserRole
from app.schemas.institution import (
    InstitutionAdminCreate,
    InstitutionAdminCreateResult,
    InstitutionAdminRead,
    InstitutionAdminResetPasswordResult,
    InstitutionCreate,
    InstitutionCreateResult,
    InstitutionRead,
    InstitutionStatusUpdate,
)
from app.seed.institution_admin import (
    create_institution_admin,
    list_institution_admins,
    reset_institution_admin_password,
)
from app.services.tenancy import (
    InvalidSlugError,
    TenantAlreadyExistsError,
    TenantProvisioningError,
    provision_tenant,
)

router = APIRouter()


def _get_institution_or_404(db: Session, institution_id: uuid.UUID) -> Institution:
    institution = db.get(Institution, institution_id)
    if institution is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found")
    return institution


@router.post("", response_model=InstitutionCreateResult, status_code=status.HTTP_201_CREATED)
def create_institution(
    payload: InstitutionCreate,
    db: Session = Depends(get_public_db),
    _admin: PlatformAdmin = Depends(get_current_platform_admin),
) -> InstitutionCreateResult:
    try:
        institution, admin_temporary_password = provision_tenant(
            db,
            name=payload.name,
            code=payload.code,
            slug=payload.slug,
            contact_email=payload.contact_email,
            subscription_plan=payload.subscription_plan,
            timezone=payload.timezone,
            seed_demo=payload.seed_demo,
            admin_full_name=payload.admin_full_name,
            admin_email=payload.admin_email,
        )
        return InstitutionCreateResult(
            institution=InstitutionRead.model_validate(institution),
            admin_temporary_password=admin_temporary_password,
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
    return _get_institution_or_404(db, institution_id)


@router.patch("/{institution_id}/status", response_model=InstitutionRead)
def update_institution_status(
    institution_id: uuid.UUID,
    payload: InstitutionStatusUpdate,
    db: Session = Depends(get_public_db),
    _admin: PlatformAdmin = Depends(get_current_platform_admin),
) -> Institution:
    institution = _get_institution_or_404(db, institution_id)
    institution.status = payload.status
    db.add(institution)
    db.commit()
    return institution


@router.get("/{institution_id}/admins", response_model=list[InstitutionAdminRead])
def list_institution_admins_endpoint(
    institution_id: uuid.UUID,
    db: Session = Depends(get_public_db),
    _admin: PlatformAdmin = Depends(get_current_platform_admin),
) -> list[InstitutionAdminRead]:
    institution = _get_institution_or_404(db, institution_id)
    with session_scope(schema_translate_map={None: institution.schema_name}) as tenant_db:
        return [
            InstitutionAdminRead.model_validate(admin)
            for admin in list_institution_admins(tenant_db)
        ]


@router.post(
    "/{institution_id}/admins",
    response_model=InstitutionAdminCreateResult,
    status_code=status.HTTP_201_CREATED,
)
def create_institution_admin_endpoint(
    institution_id: uuid.UUID,
    payload: InstitutionAdminCreate,
    db: Session = Depends(get_public_db),
    _admin: PlatformAdmin = Depends(get_current_platform_admin),
) -> InstitutionAdminCreateResult:
    """Create an Institution Administrator for an already-provisioned
    institution — the same account `POST /institutions` can create inline at
    creation time, for institutions that didn't get one then."""
    institution = _get_institution_or_404(db, institution_id)
    with session_scope(schema_translate_map={None: institution.schema_name}) as tenant_db:
        if tenant_db.query(User).filter(User.email == payload.email).one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already in use in this institution",
            )
        admin, temporary_password = create_institution_admin(
            tenant_db, full_name=payload.full_name, email=payload.email
        )
        tenant_db.flush()
        admin_read = InstitutionAdminRead.model_validate(admin)
    return InstitutionAdminCreateResult(admin=admin_read, temporary_password=temporary_password)


@router.post(
    "/{institution_id}/admins/{user_id}/reset-password",
    response_model=InstitutionAdminResetPasswordResult,
)
def reset_institution_admin_password_endpoint(
    institution_id: uuid.UUID,
    user_id: uuid.UUID,
    db: Session = Depends(get_public_db),
    _admin: PlatformAdmin = Depends(get_current_platform_admin),
) -> InstitutionAdminResetPasswordResult:
    institution = _get_institution_or_404(db, institution_id)
    with session_scope(schema_translate_map={None: institution.schema_name}) as tenant_db:
        user = tenant_db.get(User, user_id)
        role = tenant_db.query(Role).filter(Role.name == "Institution Administrator").one_or_none()
        grant = (
            None
            if user is None or role is None
            else tenant_db.query(UserRole)
            .filter(
                UserRole.user_id == user.id,
                UserRole.role_id == role.id,
                UserRole.scope_type.is_(None),
            )
            .first()
        )
        if user is None or grant is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Admin account not found"
            )
        temporary_password = reset_institution_admin_password(tenant_db, user=user)
    return InstitutionAdminResetPasswordResult(temporary_password=temporary_password)
