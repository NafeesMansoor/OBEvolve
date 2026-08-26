"""CRUD for grading policy (letter-grade bands) — DATABASE_PLAN.md §C.

Reads require `grading.view`, writes require `grading.manage`
(ARCHITECTURE.md §3).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.db.tenancy import get_db
from app.middleware.audit import get_request_context
from app.models.tenant.courses.grading import GradingBand, GradingPolicy
from app.models.tenant.identity import User
from app.schemas.grading import (
    GradingBandCreate,
    GradingBandRead,
    GradingPolicyCreate,
    GradingPolicyRead,
)
from app.services.audit import write_audit_log
from app.services.rbac import require_permission

router = APIRouter()


def _get_or_404(db: Session, model, obj_id: uuid.UUID, label: str):
    obj = db.get(model, obj_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{label} not found")
    return obj


# --- Grading policies ---
@router.post("/policies", response_model=GradingPolicyRead, status_code=status.HTTP_201_CREATED)
def create_grading_policy(
    payload: GradingPolicyCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("grading.manage")),
) -> GradingPolicy:
    policy = GradingPolicy(**payload.model_dump())
    db.add(policy)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="grading_policy.created",
        entity_type="GradingPolicy",
        entity_id=policy.id,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return policy


@router.get("/policies", response_model=list[GradingPolicyRead])
def list_grading_policies(
    program_version_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("grading.view")),
) -> list[GradingPolicy]:
    query = db.query(GradingPolicy)
    if program_version_id is not None:
        query = query.filter(GradingPolicy.program_version_id == program_version_id)
    return query.order_by(GradingPolicy.name).all()


@router.get("/policies/{policy_id}", response_model=GradingPolicyRead)
def get_grading_policy(
    policy_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("grading.view")),
) -> GradingPolicy:
    return _get_or_404(db, GradingPolicy, policy_id, "Grading policy")


@router.patch("/policies/{policy_id}", response_model=GradingPolicyRead)
def update_grading_policy(
    policy_id: uuid.UUID,
    payload: GradingPolicyCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("grading.manage")),
) -> GradingPolicy:
    policy = _get_or_404(db, GradingPolicy, policy_id, "Grading policy")
    previous_value = {
        "name": policy.name,
        "program_version_id": str(policy.program_version_id)
        if policy.program_version_id
        else None,
        "is_default": policy.is_default,
        "description": policy.description,
    }
    for field, value in payload.model_dump().items():
        setattr(policy, field, value)
    db.add(policy)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="grading_policy.updated",
        entity_type="GradingPolicy",
        entity_id=policy.id,
        previous_value=previous_value,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return policy


@router.delete("/policies/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_grading_policy(
    policy_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("grading.manage")),
) -> None:
    policy = _get_or_404(db, GradingPolicy, policy_id, "Grading policy")
    db.delete(policy)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="grading_policy.deleted",
        entity_type="GradingPolicy",
        entity_id=policy_id,
        **get_request_context(request),
    )


# --- Grading bands ---
@router.post("/bands", response_model=GradingBandRead, status_code=status.HTTP_201_CREATED)
def create_grading_band(
    payload: GradingBandCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("grading.manage")),
) -> GradingBand:
    _get_or_404(db, GradingPolicy, payload.grading_policy_id, "Grading policy")
    band = GradingBand(**payload.model_dump())
    db.add(band)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="grading_band.created",
        entity_type="GradingBand",
        entity_id=band.id,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return band


@router.get("/bands", response_model=list[GradingBandRead])
def list_grading_bands(
    grading_policy_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("grading.view")),
) -> list[GradingBand]:
    query = db.query(GradingBand)
    if grading_policy_id is not None:
        query = query.filter(GradingBand.grading_policy_id == grading_policy_id)
    return query.order_by(GradingBand.sequence).all()


@router.get("/bands/{band_id}", response_model=GradingBandRead)
def get_grading_band(
    band_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("grading.view")),
) -> GradingBand:
    return _get_or_404(db, GradingBand, band_id, "Grading band")


@router.patch("/bands/{band_id}", response_model=GradingBandRead)
def update_grading_band(
    band_id: uuid.UUID,
    payload: GradingBandCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("grading.manage")),
) -> GradingBand:
    band = _get_or_404(db, GradingBand, band_id, "Grading band")
    _get_or_404(db, GradingPolicy, payload.grading_policy_id, "Grading policy")
    previous_value = {
        "letter_grade": band.letter_grade,
        "min_percentage": str(band.min_percentage),
        "max_percentage": str(band.max_percentage),
        "grade_point": str(band.grade_point) if band.grade_point is not None else None,
        "sequence": band.sequence,
    }
    for field, value in payload.model_dump().items():
        setattr(band, field, value)
    db.add(band)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="grading_band.updated",
        entity_type="GradingBand",
        entity_id=band.id,
        previous_value=previous_value,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return band


@router.delete("/bands/{band_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_grading_band(
    band_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("grading.manage")),
) -> None:
    band = _get_or_404(db, GradingBand, band_id, "Grading band")
    db.delete(band)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="grading_band.deleted",
        entity_type="GradingBand",
        entity_id=band_id,
        **get_request_context(request),
    )
