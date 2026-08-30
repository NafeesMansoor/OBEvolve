"""Marks entry (student_marks) and attainment configuration/calculation.
Assessment *definition* CRUD lives in endpoints/assessment.py — this file is
scoped to recording scores against already-defined assessment questions and
computing CO attainment from them (app.services.attainment).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.db.tenancy import get_db
from app.middleware.audit import get_request_context
from app.models.tenant.assessments import (
    Assessment,
    AssessmentQuestion,
    CourseAttainmentConfig,
    GradeSubmission,
    ProgramAttainmentConfig,
    StudentMark,
)
from app.models.tenant.identity import StudentProfile, User
from app.schemas.attainment import (
    CourseAttainmentConfigRead,
    CourseAttainmentConfigUpsert,
    CourseAttainmentReport,
    ProgramAnalyticsSummary,
    ProgramAttainmentConfigRead,
    ProgramAttainmentConfigUpsert,
    ProgramAttainmentReport,
    StudentAttainmentSummary,
    StudentMarkBulkEntry,
    StudentMarkRead,
    StudentMarkUpdate,
)
from app.schemas.grades import GradeSheetReport, GradeSubmissionRead
from app.services.attainment import (
    calculate_course_attainment,
    calculate_program_analytics_summary,
    calculate_program_attainment,
    get_student_attainment_summary,
)
from app.services.audit import write_audit_log
from app.services.faculty_scope import ensure_assigned_to_section, ensure_section_access
from app.services.grades import build_grade_sheet, submit_final_grades
from app.services.rbac import (
    get_current_user,
    get_program_scoped_db,
    require_any_grant,
    require_permission,
)

router = APIRouter()


def _get_or_404_assessment(db: Session, assessment_id: uuid.UUID) -> Assessment:
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Assessment not found")
    return assessment


def _assessment_course_section_id(db: Session, assessment_question_id: uuid.UUID) -> uuid.UUID:
    aq = db.get(AssessmentQuestion, assessment_question_id)
    if aq is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Assessment question not found")
    return _get_or_404_assessment(db, aq.assessment_id).course_section_id


def _ensure_grades_not_submitted(db: Session, course_section_id: uuid.UUID) -> None:
    """BR-10: once final grades are submitted, marks for that section are
    locked — no more saves, no matter which endpoint tries."""
    submission = (
        db.query(GradeSubmission)
        .filter(GradeSubmission.course_section_id == course_section_id)
        .one_or_none()
    )
    if submission is not None and submission.status == "submitted":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Grades for this section have been submitted and can no longer be modified.",
        )


@router.get("/student-marks", response_model=list[StudentMarkRead])
def list_student_marks(
    request: Request,
    assessment_id: uuid.UUID = Query(...),
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_any_grant("marks.enter", "assessment.view")),
) -> list[StudentMark]:
    assessment = _get_or_404_assessment(db, assessment_id)
    ensure_section_access(
        db, current_user.id, assessment.course_section_id, request.state.program_id
    )
    aq_ids = [
        row.id
        for row in db.query(AssessmentQuestion.id)
        .filter(AssessmentQuestion.assessment_id == assessment_id)
        .all()
    ]
    if not aq_ids:
        return []
    return db.query(StudentMark).filter(StudentMark.assessment_question_id.in_(aq_ids)).all()


@router.post("/student-marks/bulk", response_model=list[StudentMarkRead])
def bulk_upsert_student_marks(
    payload: StudentMarkBulkEntry,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("marks.enter", scope_type="program")),
) -> list[StudentMark]:
    if payload.entries:
        course_section_id = _assessment_course_section_id(
            db, payload.entries[0].assessment_question_id
        )
        ensure_assigned_to_section(db, current_user.id, course_section_id)
        _ensure_grades_not_submitted(db, course_section_id)
    keys = [(e.assessment_question_id, e.student_enrollment_id) for e in payload.entries]
    existing = {
        (m.assessment_question_id, m.student_enrollment_id): m
        for m in db.query(StudentMark).filter(
            StudentMark.assessment_question_id.in_({k[0] for k in keys}),
            StudentMark.student_enrollment_id.in_({k[1] for k in keys}),
        )
    }

    results: list[StudentMark] = []
    created = 0
    updated = 0
    for entry in payload.entries:
        key = (entry.assessment_question_id, entry.student_enrollment_id)
        mark = existing.get(key)
        if mark is None:
            mark = StudentMark(
                assessment_question_id=entry.assessment_question_id,
                student_enrollment_id=entry.student_enrollment_id,
                marks_obtained=entry.marks_obtained,
                entered_by=current_user.id,
            )
            db.add(mark)
            created += 1
        else:
            mark.marks_obtained = entry.marks_obtained
            mark.entered_by = current_user.id
            mark.entered_at = datetime.now(UTC)
            updated += 1
        results.append(mark)

    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="student_marks.bulk_upserted",
        entity_type="StudentMark",
        entity_id=None,
        new_value={"created": created, "updated": updated},
        **get_request_context(request),
    )
    return results


@router.patch("/student-marks/{mark_id}", response_model=StudentMarkRead)
def update_student_mark(
    mark_id: uuid.UUID,
    payload: StudentMarkUpdate,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("marks.enter", scope_type="program")),
) -> StudentMark:
    mark = db.get(StudentMark, mark_id)
    if mark is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Student mark not found")
    course_section_id = _assessment_course_section_id(db, mark.assessment_question_id)
    ensure_assigned_to_section(db, current_user.id, course_section_id)
    _ensure_grades_not_submitted(db, course_section_id)
    previous_value = {"marks_obtained": str(mark.marks_obtained)}
    mark.marks_obtained = payload.marks_obtained
    mark.entered_by = current_user.id
    mark.entered_at = datetime.now(UTC)
    db.add(mark)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="student_marks.updated",
        entity_type="StudentMark",
        entity_id=mark.id,
        previous_value=previous_value,
        new_value={"marks_obtained": str(payload.marks_obtained)},
        **get_request_context(request),
    )
    return mark


@router.delete("/student-marks/{mark_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student_mark(
    mark_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("marks.enter", scope_type="program")),
) -> None:
    mark = db.get(StudentMark, mark_id)
    if mark is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Student mark not found")
    course_section_id = _assessment_course_section_id(db, mark.assessment_question_id)
    ensure_assigned_to_section(db, current_user.id, course_section_id)
    _ensure_grades_not_submitted(db, course_section_id)
    db.delete(mark)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="student_marks.deleted",
        entity_type="StudentMark",
        entity_id=mark_id,
        **get_request_context(request),
    )


# --- Attainment configuration ---
@router.get("/attainment-config", response_model=CourseAttainmentConfigRead | None)
def get_attainment_config(
    course_version_id: uuid.UUID = Query(...),
    db: Session = Depends(get_program_scoped_db),
    _current_user: User = Depends(
        require_any_grant("attainment.calculate", "assessment.approve", "assessment.view")
    ),
) -> CourseAttainmentConfig | None:
    return (
        db.query(CourseAttainmentConfig)
        .filter(CourseAttainmentConfig.course_version_id == course_version_id)
        .one_or_none()
    )


@router.put("/attainment-config", response_model=CourseAttainmentConfigRead)
def upsert_attainment_config(
    payload: CourseAttainmentConfigUpsert,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_any_grant("attainment.calculate", "assessment.approve")),
) -> CourseAttainmentConfig:
    config = (
        db.query(CourseAttainmentConfig)
        .filter(CourseAttainmentConfig.course_version_id == payload.course_version_id)
        .one_or_none()
    )
    previous_value = None
    if config is None:
        config = CourseAttainmentConfig(**payload.model_dump())
        db.add(config)
        action = "attainment_config.created"
    else:
        previous_value = {
            "min_marks_percent": str(config.min_marks_percent),
            "min_students_percent": str(config.min_students_percent),
            "wi_treatment": config.wi_treatment,
        }
        config.min_marks_percent = payload.min_marks_percent
        config.min_students_percent = payload.min_students_percent
        config.wi_treatment = payload.wi_treatment
        action = "attainment_config.updated"
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action=action,
        entity_type="CourseAttainmentConfig",
        entity_id=config.id,
        previous_value=previous_value,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return config


# --- Attainment report ---
@router.get("/attainment-report", response_model=CourseAttainmentReport)
def get_attainment_report(
    request: Request,
    course_section_id: uuid.UUID = Query(...),
    batch_year: int | None = Query(default=None),
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(
        require_any_grant("attainment.calculate", "assessment.approve", "assessment.view")
    ),
) -> CourseAttainmentReport:
    ensure_section_access(db, current_user.id, course_section_id, request.state.program_id)
    return calculate_course_attainment(db, course_section_id, batch_year=batch_year)


# --- Grades tab (spec §21-24): consolidated grade sheet + final submission ---
@router.get("/grade-sheet", response_model=GradeSheetReport)
def get_grade_sheet(
    request: Request,
    course_section_id: uuid.UUID = Query(...),
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_any_grant("marks.enter", "assessment.view")),
) -> GradeSheetReport:
    ensure_section_access(db, current_user.id, course_section_id, request.state.program_id)
    return build_grade_sheet(db, course_section_id)


@router.post("/sections/{course_section_id}/grades/submit", response_model=GradeSubmissionRead)
def submit_section_grades(
    course_section_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("marks.enter", scope_type="program")),
) -> GradeSubmission:
    ensure_assigned_to_section(db, current_user.id, course_section_id)
    submission = submit_final_grades(db, course_section_id, current_user.id)
    write_audit_log(
        db,
        user_id=current_user.id,
        action="grades.submitted",
        entity_type="GradeSubmission",
        entity_id=submission.id,
        new_value={"course_section_id": str(course_section_id)},
        **get_request_context(request),
    )
    return submission


# --- PO attainment configuration ---
_PO_VIEW_GRANTS = ("program.view", "attainment.calculate", "assessment.approve", "assessment.view")
_PO_MANAGE_GRANTS = ("program.manage", "attainment.calculate")


@router.get("/program-attainment-config", response_model=ProgramAttainmentConfigRead | None)
def get_program_attainment_config(
    program_version_id: uuid.UUID = Query(...),
    db: Session = Depends(get_program_scoped_db),
    _current_user: User = Depends(require_any_grant(*_PO_VIEW_GRANTS)),
) -> ProgramAttainmentConfig | None:
    return (
        db.query(ProgramAttainmentConfig)
        .filter(ProgramAttainmentConfig.program_version_id == program_version_id)
        .one_or_none()
    )


@router.put("/program-attainment-config", response_model=ProgramAttainmentConfigRead)
def upsert_program_attainment_config(
    payload: ProgramAttainmentConfigUpsert,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_any_grant(*_PO_MANAGE_GRANTS)),
) -> ProgramAttainmentConfig:
    config = (
        db.query(ProgramAttainmentConfig)
        .filter(ProgramAttainmentConfig.program_version_id == payload.program_version_id)
        .one_or_none()
    )
    previous_value = None
    if config is None:
        config = ProgramAttainmentConfig(**payload.model_dump())
        db.add(config)
        action = "program_attainment_config.created"
    else:
        previous_value = {"min_po_attainment_percent": str(config.min_po_attainment_percent)}
        config.min_po_attainment_percent = payload.min_po_attainment_percent
        action = "program_attainment_config.updated"
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action=action,
        entity_type="ProgramAttainmentConfig",
        entity_id=config.id,
        previous_value=previous_value,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return config


# --- PO attainment report ---
@router.get("/program-attainment-report", response_model=ProgramAttainmentReport)
def get_program_attainment_report(
    program_version_id: uuid.UUID = Query(...),
    batch_year: int | None = Query(default=None),
    academic_term_id: uuid.UUID | None = Query(default=None),
    db: Session = Depends(get_program_scoped_db),
    _current_user: User = Depends(require_any_grant(*_PO_VIEW_GRANTS)),
) -> ProgramAttainmentReport:
    return calculate_program_attainment(
        db, program_version_id, batch_year=batch_year, academic_term_id=academic_term_id
    )


# --- Program analytics dashboard ---
@router.get("/program-analytics-summary", response_model=ProgramAnalyticsSummary)
def get_program_analytics_summary(
    program_version_id: uuid.UUID = Query(...),
    batch_year: int | None = Query(default=None),
    db: Session = Depends(get_program_scoped_db),
    _current_user: User = Depends(require_any_grant(*_PO_VIEW_GRANTS)),
) -> ProgramAnalyticsSummary:
    return calculate_program_analytics_summary(db, program_version_id, batch_year=batch_year)


# --- Student self-service dashboard ---
@router.get("/my-attainment", response_model=StudentAttainmentSummary)
def get_my_attainment(
    program_version_id: uuid.UUID = Query(...),
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(get_current_user),
) -> StudentAttainmentSummary:
    """No permission gate beyond authentication — deliberately: this only
    ever returns `current_user`'s own enrollments/marks/attainment (spec
    §14: "the student should only see their own information"), never
    another student's, so there is nothing here a permission check would
    protect that isn't already enforced by scoping every query to
    `current_user.id`."""
    return get_student_attainment_summary(db, current_user.id, program_version_id)


@router.get("/my-program-version")
def get_my_program_version(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, str | None]:
    """Lets the student dashboard discover which curriculum version to ask
    `/marks/my-attainment` about, without needing `program.view` (which
    students don't hold) — `StudentProfile` is institution-shared, so this
    needs no `X-Program-Code` header at all."""
    profile = (
        db.query(StudentProfile).filter(StudentProfile.user_id == current_user.id).one_or_none()
    )
    program_version_id = profile.program_version_id if profile else None
    return {"program_version_id": str(program_version_id) if program_version_id else None}
