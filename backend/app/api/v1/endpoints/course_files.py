"""Course Files (Faculty Module spec §5-9): the seeded document catalogue,
admin-configured per-semester requirements (course-wise or holistic, with
import-from-previous-term), and per-section upload/review — mirrors
`endpoints/assessment.py`'s document upload/review pattern almost exactly,
just against a broader, admin-configurable checklist instead of a fixed
code-level one.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.db.tenancy import get_db
from app.middleware.audit import get_request_context
from app.models.tenant.course_files import (
    CourseFileRequirement,
    CourseFileSubmission,
    CourseFileType,
)
from app.models.tenant.identity import User
from app.schemas.course_files import (
    CourseFileChecklistItem,
    CourseFileRequirementCreate,
    CourseFileRequirementImport,
    CourseFileRequirementRead,
    CourseFileSubmissionRead,
    CourseFileSubmissionReview,
    CourseFileTypeRead,
)
from app.services.audit import write_audit_log
from app.services.course_files import import_requirements, resolve_requirements
from app.services.faculty_scope import ensure_assigned_to_section, ensure_section_access
from app.services.rbac import get_program_scoped_db, require_any_grant, require_permission
from app.services.storage import delete_upload, read_upload, save_upload

router = APIRouter()


def _get_or_404(db: Session, model, obj_id: uuid.UUID, label: str):
    obj = db.get(model, obj_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{label} not found")
    return obj


# --- Catalogue (institution-shared, read-only) ---
@router.get("/types", response_model=list[CourseFileTypeRead])
def list_course_file_types(
    db: Session = Depends(get_db),
    _current_user: User = Depends(
        require_any_grant("course_file.view", "course_file.configure", "course_file.upload")
    ),
) -> list[CourseFileType]:
    return db.query(CourseFileType).order_by(CourseFileType.category, CourseFileType.name).all()


# --- Requirements (institution-shared; program/coordinator-configured) ---
@router.post(
    "/requirements", response_model=CourseFileRequirementRead, status_code=status.HTTP_201_CREATED
)
def create_course_file_requirement(
    payload: CourseFileRequirementCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("course_file.configure")),
) -> CourseFileRequirement:
    _get_or_404(db, CourseFileType, payload.course_file_type_id, "Course file type")
    requirement = CourseFileRequirement(**payload.model_dump())
    db.add(requirement)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="course_file_requirement.created",
        entity_type="CourseFileRequirement",
        entity_id=requirement.id,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return requirement


@router.get("/requirements", response_model=list[CourseFileRequirementRead])
def list_course_file_requirements(
    academic_term_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    _current_user: User = Depends(
        require_any_grant("course_file.view", "course_file.configure")
    ),
) -> list[CourseFileRequirement]:
    query = db.query(CourseFileRequirement)
    if academic_term_id is not None:
        query = query.filter(CourseFileRequirement.academic_term_id == academic_term_id)
    return query.all()


@router.patch("/requirements/{requirement_id}", response_model=CourseFileRequirementRead)
def update_course_file_requirement(
    requirement_id: uuid.UUID,
    payload: CourseFileRequirementCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("course_file.configure")),
) -> CourseFileRequirement:
    requirement = _get_or_404(db, CourseFileRequirement, requirement_id, "Course file requirement")
    for field, value in payload.model_dump().items():
        setattr(requirement, field, value)
    db.add(requirement)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="course_file_requirement.updated",
        entity_type="CourseFileRequirement",
        entity_id=requirement.id,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return requirement


@router.delete("/requirements/{requirement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course_file_requirement(
    requirement_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("course_file.configure")),
) -> None:
    requirement = _get_or_404(db, CourseFileRequirement, requirement_id, "Course file requirement")
    db.delete(requirement)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="course_file_requirement.deleted",
        entity_type="CourseFileRequirement",
        entity_id=requirement_id,
        **get_request_context(request),
    )


@router.post("/requirements/import", response_model=list[CourseFileRequirementRead])
def import_course_file_requirements(
    payload: CourseFileRequirementImport,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("course_file.configure")),
) -> list[CourseFileRequirement]:
    """"Import Previous Semester Configuration" (spec §9) — copies every
    requirement rule from one term to another; the caller can then edit the
    copied rows before activating the new semester."""
    created = import_requirements(
        db, payload.from_academic_term_id, payload.to_academic_term_id
    )
    write_audit_log(
        db,
        user_id=current_user.id,
        action="course_file_requirement.imported",
        entity_type="CourseFileRequirement",
        entity_id=None,
        new_value={
            "from_academic_term_id": str(payload.from_academic_term_id),
            "to_academic_term_id": str(payload.to_academic_term_id),
            "created_count": len(created),
        },
        **get_request_context(request),
    )
    return created


# --- Per-section checklist + upload/review (program-scoped) ---
@router.get("/sections/{course_section_id}", response_model=list[CourseFileChecklistItem])
def get_section_course_files(
    course_section_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(
        require_any_grant("course_file.view", "course_file.upload", "course_file.review")
    ),
) -> list[CourseFileChecklistItem]:
    ensure_section_access(db, current_user.id, course_section_id, request.state.program_id)
    return resolve_requirements(db, course_section_id)


@router.post(
    "/sections/{course_section_id}/{course_file_type_id}/upload",
    response_model=CourseFileSubmissionRead,
)
def upload_course_file(
    course_section_id: uuid.UUID,
    course_file_type_id: uuid.UUID,
    request: Request,
    file: UploadFile = File(...),
    hard_copy_submitted: bool = Form(default=False),
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("course_file.upload", scope_type="program")),
) -> CourseFileSubmission:
    ensure_assigned_to_section(db, current_user.id, course_section_id)
    _get_or_404(db, CourseFileType, course_file_type_id, "Course file type")

    key, size = save_upload(
        file, key_prefix=f"course-files/{course_section_id}/{course_file_type_id}"
    )
    now = datetime.now(UTC)

    existing = (
        db.query(CourseFileSubmission)
        .filter(
            CourseFileSubmission.course_section_id == course_section_id,
            CourseFileSubmission.course_file_type_id == course_file_type_id,
        )
        .one_or_none()
    )
    if existing is not None:
        old_key = existing.file_key
        existing.file_key = key
        existing.file_name = file.filename or "document"
        existing.file_size = size
        existing.content_type = file.content_type or "application/octet-stream"
        existing.version += 1
        existing.hard_copy_submitted = hard_copy_submitted
        existing.status = "pending"
        existing.submitted_by = current_user.id
        existing.submitted_at = now
        existing.reviewed_by = None
        existing.reviewed_at = None
        existing.review_note = None
        db.add(existing)
        db.flush()
        delete_upload(old_key)
        submission = existing
        action = "course_file.replaced"
    else:
        submission = CourseFileSubmission(
            course_section_id=course_section_id,
            course_file_type_id=course_file_type_id,
            file_key=key,
            file_name=file.filename or "document",
            file_size=size,
            content_type=file.content_type or "application/octet-stream",
            version=1,
            hard_copy_submitted=hard_copy_submitted,
            status="pending",
            submitted_by=current_user.id,
            submitted_at=now,
        )
        db.add(submission)
        db.flush()
        action = "course_file.uploaded"

    write_audit_log(
        db,
        user_id=current_user.id,
        action=action,
        entity_type="CourseFileSubmission",
        entity_id=submission.id,
        new_value={"file_name": submission.file_name, "version": submission.version},
        **get_request_context(request),
    )
    return submission


@router.get("/submissions/{submission_id}/download")
def download_course_file(
    submission_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(
        require_any_grant("course_file.view", "course_file.upload", "course_file.review")
    ),
):
    submission = _get_or_404(db, CourseFileSubmission, submission_id, "Course file submission")
    ensure_section_access(
        db, current_user.id, submission.course_section_id, request.state.program_id
    )
    contents = read_upload(submission.file_key)
    from fastapi import Response

    return Response(
        content=contents,
        media_type=submission.content_type,
        headers={"Content-Disposition": f'attachment; filename="{submission.file_name}"'},
    )


@router.post("/submissions/{submission_id}/review", response_model=CourseFileSubmissionRead)
def review_course_file(
    submission_id: uuid.UUID,
    payload: CourseFileSubmissionReview,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("course_file.review", scope_type="program")),
) -> CourseFileSubmission:
    submission = _get_or_404(db, CourseFileSubmission, submission_id, "Course file submission")
    if submission.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Submission is already {submission.status!r}.",
        )
    submission.status = payload.status
    submission.reviewed_by = current_user.id
    submission.reviewed_at = datetime.now(UTC)
    submission.review_note = payload.review_note
    db.add(submission)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action=f"course_file.{payload.status}",
        entity_type="CourseFileSubmission",
        entity_id=submission.id,
        new_value={"status": payload.status, "review_note": payload.review_note},
        **get_request_context(request),
    )
    return submission
