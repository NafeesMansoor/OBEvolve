"""Course-level change requests: a faculty member proposes a change to an
admin-controlled, section-gated part of their course (Course Overview/
Settings/Students/Assessments) instead of editing it directly. See
docs/course_level_settings_and_approval_workflow.md and
`app.models.tenant.change_requests.CourseChangeRequest`'s docstring for the
staged-approval/auto-apply shape.
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
from app.services.course_type_config import (
    SECTION_APPROVAL_TIERS,
    apply_change_request,
    compute_import_preview,
    ensure_section_enabled,
)
from app.services.faculty_scope import (
    ensure_assigned_to_section,
    ensure_section_access,
    filter_to_my_sections,
)
from app.services.rbac import (
    get_program_scoped_db,
    require_any_grant,
    require_permission,
    user_has_permission,
)

router = APIRouter()


def _get_or_404(db: Session, request_id: uuid.UUID) -> CourseChangeRequest:
    obj = db.get(CourseChangeRequest, request_id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Change request not found")
    return obj


@router.get("/import-preview", response_model=dict[str, dict[str, object]])
def preview_import(
    course_section_id: uuid.UUID = Query(...),
    source_course_version_id: uuid.UUID = Query(...),
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(
        require_permission("course_change_request.create", scope_type="program")
    ),
) -> dict[str, dict[str, object]]:
    """Read-only "review what will be imported before confirming" step
    (spec §10) — computes the current-vs-source diff for every importable
    settings field without writing anything. The caller reviews this, edits
    the reason/fields they actually want, then submits each chosen field
    through the normal `POST /course-change-requests` using this preview's
    `proposed_value` verbatim, so an import still flows through the same
    approval workflow as any other teacher-submitted change."""
    ensure_assigned_to_section(db, current_user.id, course_section_id)
    return compute_import_preview(db, course_section_id, source_course_version_id)


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
    ensure_section_enabled(db, payload.course_section_id, payload.section_key)
    change_request = CourseChangeRequest(
        **payload.model_dump(), status="pending_admin", requested_by=current_user.id
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
        require_any_grant(
            "course_change_request.create",
            "course_change_request.review",
            "course_change_request.review_admin",
            "course_change_request.review_program",
        )
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
        require_any_grant(
            "course_change_request.review_admin", "course_change_request.review_program"
        )
    ),
) -> CourseChangeRequest:
    change_request = _get_or_404(db, request_id)
    ensure_section_access(
        db, current_user.id, change_request.course_section_id, request.state.program_id
    )

    if change_request.status == "pending_admin":
        required_code = "course_change_request.review_admin"
    elif change_request.status == "pending_program_coordinator":
        required_code = "course_change_request.review_program"
    else:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Change request is already {change_request.status!r}.",
        )

    if not user_has_permission(
        db, current_user.id, required_code, scope_type="program", scope_id=request.state.program_id
    ) and not user_has_permission(db, current_user.id, required_code):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing required permission for this stage: {required_code}",
        )

    now = datetime.now(UTC)
    if payload.edited_value_json is not None and payload.status == "approved":
        change_request.edited_value_json = payload.edited_value_json
        change_request.edited_by = current_user.id
        change_request.edited_at = now

    if change_request.status == "pending_admin":
        change_request.reviewed_by = current_user.id
        change_request.review_note = payload.review_note
        change_request.reviewed_at = now
        if payload.status == "approved":
            if SECTION_APPROVAL_TIERS[change_request.section_key] == 1:
                change_request.status = "approved"
                apply_change_request(db, change_request)
            else:
                change_request.status = "pending_program_coordinator"
        else:
            change_request.status = payload.status
    else:  # pending_program_coordinator
        change_request.program_coordinator_reviewed_by = current_user.id
        change_request.program_coordinator_review_note = payload.review_note
        change_request.program_coordinator_reviewed_at = now
        if payload.status == "approved":
            change_request.status = "approved"
            apply_change_request(db, change_request)
        else:
            change_request.status = payload.status

    db.add(change_request)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action=f"course_change_request.{payload.status}",
        entity_type="CourseChangeRequest",
        entity_id=change_request.id,
        new_value={
            "status": change_request.status,
            "review_note": payload.review_note,
            "edited_value_json": payload.edited_value_json,
        },
        **get_request_context(request),
    )
    return change_request
