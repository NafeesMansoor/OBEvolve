"""CO-failure continuous-improvement workflow (spec §5): propose an action
plan against a CO, get it reviewed (approved/rejected), and mark it
implemented. No auto-flagging job — the attainment report already marks a
CO `is_attained=False` on every view (app.services.attainment); the
frontend offers "create a plan" from there.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.middleware.audit import get_request_context
from app.models.tenant.identity import User
from app.models.tenant.obe.improvement import ImprovementPlan
from app.schemas.improvement import (
    ImprovementPlanCreate,
    ImprovementPlanRead,
    ImprovementPlanReview,
    ImprovementPlanUpdate,
)
from app.services.audit import write_audit_log
from app.services.rbac import get_program_scoped_db, require_any_grant, require_permission

router = APIRouter()

_CREATE_GRANTS = ("marks.enter", "assessment.create", "assessment.approve")
_VIEW_GRANTS = ("marks.enter", "assessment.create", "assessment.approve", "assessment.view")


def _get_or_404(db: Session, plan_id: uuid.UUID) -> ImprovementPlan:
    plan = db.get(ImprovementPlan, plan_id)
    if plan is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Improvement plan not found")
    return plan


@router.post("", response_model=ImprovementPlanRead, status_code=status.HTTP_201_CREATED)
def create_improvement_plan(
    payload: ImprovementPlanCreate,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_any_grant(*_CREATE_GRANTS)),
) -> ImprovementPlan:
    plan = ImprovementPlan(**payload.model_dump(), created_by=current_user.id, status="proposed")
    db.add(plan)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="improvement_plan.created",
        entity_type="ImprovementPlan",
        entity_id=plan.id,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return plan


@router.get("", response_model=list[ImprovementPlanRead])
def list_improvement_plans(
    course_section_id: uuid.UUID | None = Query(default=None),
    course_outcome_id: uuid.UUID | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_program_scoped_db),
    _current_user: User = Depends(require_any_grant(*_VIEW_GRANTS)),
) -> list[ImprovementPlan]:
    query = db.query(ImprovementPlan)
    if course_section_id is not None:
        query = query.filter(ImprovementPlan.course_section_id == course_section_id)
    if course_outcome_id is not None:
        query = query.filter(ImprovementPlan.course_outcome_id == course_outcome_id)
    if status_filter is not None:
        query = query.filter(ImprovementPlan.status == status_filter)
    return query.order_by(ImprovementPlan.created_at.desc()).all()


@router.get("/{plan_id}", response_model=ImprovementPlanRead)
def get_improvement_plan(
    plan_id: uuid.UUID,
    db: Session = Depends(get_program_scoped_db),
    _current_user: User = Depends(require_any_grant(*_VIEW_GRANTS)),
) -> ImprovementPlan:
    return _get_or_404(db, plan_id)


@router.patch("/{plan_id}", response_model=ImprovementPlanRead)
def update_improvement_plan(
    plan_id: uuid.UUID,
    payload: ImprovementPlanUpdate,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_any_grant(*_CREATE_GRANTS)),
) -> ImprovementPlan:
    plan = _get_or_404(db, plan_id)
    if plan.status != "proposed":
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail=f"Plan in status {plan.status!r} can no longer be edited.",
        )
    previous_value = {"status": plan.status}
    for field, value in payload.model_dump().items():
        setattr(plan, field, value)
    db.add(plan)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="improvement_plan.updated",
        entity_type="ImprovementPlan",
        entity_id=plan.id,
        previous_value=previous_value,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return plan


@router.post("/{plan_id}/review", response_model=ImprovementPlanRead)
def review_improvement_plan(
    plan_id: uuid.UUID,
    payload: ImprovementPlanReview,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("assessment.approve", scope_type="program")),
) -> ImprovementPlan:
    plan = _get_or_404(db, plan_id)
    if plan.status != "proposed":
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail=f"Plan in status {plan.status!r} has already been reviewed.",
        )
    previous_value = {"status": plan.status}
    plan.status = "approved" if payload.approve else "rejected"
    plan.reviewed_by = current_user.id
    plan.reviewed_at = datetime.now(UTC)
    if payload.remarks:
        plan.evidence = (
            f"{plan.evidence}\n\nReview remarks: {payload.remarks}"
            if plan.evidence
            else f"Review remarks: {payload.remarks}"
        )
    db.add(plan)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="improvement_plan.reviewed",
        entity_type="ImprovementPlan",
        entity_id=plan.id,
        previous_value=previous_value,
        new_value={"status": plan.status, "remarks": payload.remarks},
        **get_request_context(request),
    )
    return plan


@router.post("/{plan_id}/implement", response_model=ImprovementPlanRead)
def mark_improvement_plan_implemented(
    plan_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_any_grant(*_CREATE_GRANTS)),
) -> ImprovementPlan:
    plan = _get_or_404(db, plan_id)
    if plan.status != "approved":
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail=f"Plan in status {plan.status!r} must be approved before it can be implemented.",
        )
    previous_value = {"status": plan.status}
    plan.status = "implemented"
    db.add(plan)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="improvement_plan.implemented",
        entity_type="ImprovementPlan",
        entity_id=plan.id,
        previous_value=previous_value,
        new_value={"status": "implemented"},
        **get_request_context(request),
    )
    return plan


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_improvement_plan(
    plan_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_any_grant(*_CREATE_GRANTS)),
) -> None:
    plan = _get_or_404(db, plan_id)
    db.delete(plan)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="improvement_plan.deleted",
        entity_type="ImprovementPlan",
        entity_id=plan_id,
        **get_request_context(request),
    )
