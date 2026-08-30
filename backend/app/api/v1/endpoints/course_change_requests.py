"""Course Settings change requests (Faculty Module spec §4.2): a faculty
member proposes a change to admin-controlled course information instead of
editing it directly. Approving a request only flips its status — it does
not auto-apply the change (see `CourseChangeRequest`'s model docstring for
why); the Course Coordinator/Program Administrator makes the real edit
through the existing admin Course Settings UI, using the approved request
as the audited justification.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.middleware.audit import get_request_context
from app.models.tenant.change_requests import CourseChangeRequest
from app.models.tenant.identity import User
from app.schemas.change_requests import (
    CourseChangeRequestCreate,
    CourseChangeRequestRead,
    CourseChangeRequestReview,
)
from app.services.audit import write_audit_log
from app.services.faculty_scope import (
    ensure_assigned_to_section,
    ensure_section_access,
    filter_to_my_sections,
)
from app.services.rbac import get_program_scoped_db, require_any_grant, require_permission

router = APIRouter()


def _get_or_404(db: Session, request_id: uuid.UUID) -> CourseChangeRequest:
    obj = db.get(CourseChangeRequest, request_id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Change request not found")
    return obj


@router.post("", response_model=CourseChangeRequestRead, status_code=status.HTTP_201_CREATED)
def create_course_change_request(
    payload: CourseChangeRequestCreate,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(
        require_permission("course_change_request.create", scope_type="program")
    ),
) -> CourseChangeRequest:
    ensure_assigned_to_section(db, current_user.id, payload.course_section_id)
    change_request = CourseChangeRequest(
        **payload.model_dump(), status="pending", requested_by=current_user.id
    )
    db.add(change_request)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="course_change_request.created",
        entity_type="CourseChangeRequest",
        entity_id=change_request.id,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return change_request


@router.get("", response_model=list[CourseChangeRequestRead])
def list_course_change_requests(
    request: Request,
    course_section_id: uuid.UUID | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(
        require_any_grant("course_change_request.create", "course_change_request.review")
    ),
) -> list[CourseChangeRequest]:
    if course_section_id is not None:
        ensure_section_access(db, current_user.id, course_section_id, request.state.program_id)
    query = db.query(CourseChangeRequest)
    if course_section_id is not None:
        query = query.filter(CourseChangeRequest.course_section_id == course_section_id)
    if status_filter is not None:
        query = query.filter(CourseChangeRequest.status == status_filter)
    my_section_ids = filter_to_my_sections(db, current_user.id, request.state.program_id)
    if my_section_ids is not None:
        query = query.filter(CourseChangeRequest.course_section_id.in_(my_section_ids))
    return query.order_by(CourseChangeRequest.created_at.desc()).all()


@router.post("/{request_id}/review", response_model=CourseChangeRequestRead)
def review_course_change_request(
    request_id: uuid.UUID,
    payload: CourseChangeRequestReview,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(
        require_permission("course_change_request.review", scope_type="program")
    ),
) -> CourseChangeRequest:
    change_request = _get_or_404(db, request_id)
    ensure_section_access(
        db, current_user.id, change_request.course_section_id, request.state.program_id
    )
    if change_request.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Change request is already {change_request.status!r}.",
        )
    change_request.status = payload.status
    change_request.reviewed_by = current_user.id
    change_request.review_note = payload.review_note
    change_request.reviewed_at = datetime.now(UTC)
    db.add(change_request)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action=f"course_change_request.{payload.status}",
        entity_type="CourseChangeRequest",
        entity_id=change_request.id,
        new_value={"status": payload.status, "review_note": payload.review_note},
        **get_request_context(request),
    )
    return change_request
