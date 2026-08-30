"""Faculty Module Grades tab (spec §21-24): a consolidated per-section grade
sheet (marks x weights x grading policy -> letter grade), the save/submit
workflow, and the CO-attainment snapshot triggered by a successful "Submit
Final Grades".

PO attainment is deliberately *not* snapshotted per section submission here:
a PO's attainment is a cross-section aggregate (`app.services.attainment.
calculate_program_attainment`), so persisting a program-wide result under
one section's `GradeSubmission` would misattribute it — the existing
on-demand `program-attainment-report` endpoint already serves "view PO
attainment" (spec §28) without that mismatch. `AttainmentSnapshot.scope`
still supports "po" rows for if/when a real per-submission PO methodology
is defined.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.tenant.assessments import (
    Assessment,
    AssessmentQuestion,
    AttainmentSnapshot,
    GradeSubmission,
    StudentMark,
)
from app.models.tenant.courses.delivery import CourseOffering, CourseSection, StudentEnrollment
from app.models.tenant.identity import User
from app.schemas.grades import AssessmentContribution, GradeSheetReport, GradeSheetRow
from app.services.attainment import calculate_course_attainment, resolve_letter_grade


def _resolve_program_version_id(db: Session, course_section_id: uuid.UUID) -> uuid.UUID | None:
    section = db.get(CourseSection, course_section_id)
    if section is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Course section not found")
    offering = db.get(CourseOffering, section.course_offering_id)
    return offering.program_version_id if offering else None


def _get_or_create_submission(db: Session, course_section_id: uuid.UUID) -> GradeSubmission:
    submission = (
        db.query(GradeSubmission)
        .filter(GradeSubmission.course_section_id == course_section_id)
        .one_or_none()
    )
    if submission is None:
        submission = GradeSubmission(course_section_id=course_section_id, status="draft")
        db.add(submission)
        db.flush()
    return submission


def build_grade_sheet(db: Session, course_section_id: uuid.UUID) -> GradeSheetReport:
    assessments = (
        db.query(Assessment).filter(Assessment.course_section_id == course_section_id).all()
    )
    weighted = [a for a in assessments if a.weight is not None]
    total_weight = sum((a.weight for a in weighted), Decimal(0))

    questions_by_assessment: dict[uuid.UUID, list[AssessmentQuestion]] = {}
    all_question_ids: list[uuid.UUID] = []
    for a in assessments:
        qs = db.query(AssessmentQuestion).filter(AssessmentQuestion.assessment_id == a.id).all()
        questions_by_assessment[a.id] = qs
        all_question_ids.extend(q.id for q in qs)

    marks_by_question_and_enrollment: dict[tuple[uuid.UUID, uuid.UUID], Decimal] = {}
    if all_question_ids:
        for m in db.query(StudentMark).filter(
            StudentMark.assessment_question_id.in_(all_question_ids)
        ):
            marks_by_question_and_enrollment[
                (m.assessment_question_id, m.student_enrollment_id)
            ] = m.marks_obtained

    enrollments = (
        db.query(StudentEnrollment)
        .filter(StudentEnrollment.course_section_id == course_section_id)
        .all()
    )
    student_ids = [e.student_user_id for e in enrollments]
    names_by_id = (
        {u.id: u.full_name for u in db.query(User).filter(User.id.in_(student_ids)).all()}
        if student_ids
        else {}
    )

    program_version_id = _resolve_program_version_id(db, course_section_id)

    incomplete_titles: list[str] = []
    rows: list[GradeSheetRow] = []
    for enrollment in enrollments:
        contributions: list[AssessmentContribution] = []
        overall_percent = Decimal(0)
        any_missing_for_student = False
        for a in assessments:
            qs = questions_by_assessment[a.id]
            if not qs:
                continue
            obtained = Decimal(0)
            missing = False
            for q in qs:
                mark = marks_by_question_and_enrollment.get((q.id, enrollment.id))
                if mark is None:
                    missing = True
                else:
                    obtained += mark
            if missing:
                any_missing_for_student = True
                if a.title not in incomplete_titles:
                    incomplete_titles.append(a.title)
            pct = (obtained / a.max_marks * 100) if a.max_marks else None
            weighted_pct = (pct / 100 * a.weight) if (pct is not None and a.weight) else None
            if weighted_pct is not None:
                overall_percent += weighted_pct
            contributions.append(
                AssessmentContribution(
                    assessment_id=a.id,
                    title=a.title,
                    weight=a.weight,
                    marks_obtained=obtained,
                    max_marks=a.max_marks,
                    weighted_percent=weighted_pct,
                )
            )

        has_full_overall = not any_missing_for_student and total_weight == Decimal(100)
        letter_grade, grade_point = (
            resolve_letter_grade(db, program_version_id or uuid.uuid4(), overall_percent)
            if has_full_overall
            else (None, None)
        )
        rows.append(
            GradeSheetRow(
                student_enrollment_id=enrollment.id,
                student_user_id=enrollment.student_user_id,
                student_name=names_by_id.get(enrollment.student_user_id, "Unknown"),
                enrollment_status=enrollment.enrollment_status,
                assessments=contributions,
                overall_percent=overall_percent if has_full_overall else None,
                letter_grade=letter_grade,
                grade_point=grade_point,
            )
        )

    submission = (
        db.query(GradeSubmission)
        .filter(GradeSubmission.course_section_id == course_section_id)
        .one_or_none()
    )

    return GradeSheetReport(
        course_section_id=course_section_id,
        rows=rows,
        weight_recorded_percent=total_weight,
        weight_complete=(len(weighted) == len(assessments) and total_weight == Decimal(100)),
        marks_complete=not incomplete_titles,
        incomplete_assessment_titles=incomplete_titles,
        submission_status=submission.status if submission else "draft",
        submitted_at=submission.submitted_at if submission else None,
        submitted_by=submission.submitted_by if submission else None,
    )


def submit_final_grades(
    db: Session, course_section_id: uuid.UUID, submitted_by: uuid.UUID
) -> GradeSubmission:
    """Faculty Module spec §22-24 / BR-09 through BR-12: validates 100% of
    assessment weight is both declared *and* recorded (every question has a
    mark for every enrolled student), locks the section's grades, and
    persists a CO-attainment snapshot from the already-existing calculation
    engine (`app.services.attainment.calculate_course_attainment`) — this
    function adds the "finalize + store" event, not new calculation logic.
    """
    submission = _get_or_create_submission(db, course_section_id)
    if submission.status == "submitted":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Grades for this section have already been submitted.",
        )

    sheet = build_grade_sheet(db, course_section_id)
    if not sheet.weight_complete:
        if sheet.weight_recorded_percent > Decimal(100):
            detail = (
                "Submission unavailable. Assessment weights sum to "
                f"{sheet.weight_recorded_percent}%, which exceeds 100% — check for "
                "duplicate or misweighted assessments."
            )
        else:
            detail = (
                "Submission unavailable. "
                f"{100 - sheet.weight_recorded_percent}% of assessment weight is "
                "still incomplete."
            )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)
    if not sheet.marks_complete:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Incomplete: marks are still missing for "
            f"{', '.join(sheet.incomplete_assessment_titles)}.",
        )

    submission.status = "submitted"
    submission.submitted_by = submitted_by
    submission.submitted_at = datetime.now(UTC)
    db.add(submission)
    db.flush()

    course_report = calculate_course_attainment(db, course_section_id)
    for outcome in course_report.outcomes:
        if not outcome.assessed or outcome.attainment_percent is None:
            continue
        db.add(
            AttainmentSnapshot(
                grade_submission_id=submission.id,
                scope="co",
                course_outcome_id=outcome.course_outcome_id,
                attainment_percent=outcome.attainment_percent,
                student_count=outcome.eligible_students or 0,
            )
        )
    db.flush()
    return submission
