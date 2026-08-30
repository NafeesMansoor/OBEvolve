"""On-demand CO/PO attainment calculation — no stored "run" history (see
app.models.tenant.assessments.marks module docstring for why this is a
deliberately smaller MVP than DATABASE_PLAN.md §H's full engine).

Per course section: a student attains a CO if the % of that CO's mapped-
question marks they scored (across every assessment in the section) is at
least the course's `min_marks_percent`. A CO itself is attained if at least
`min_students_percent` of *eligible* students attained it. Which students
count as "eligible" is itself configurable (spec §4): `wi_treatment ==
"exclude"` (the default) drops Withdrawn/Incomplete-enrolled students from
both the numerator and denominator; `"include"` treats them like any other
enrollment (an incomplete student with no marks entered simply scores 0%
on every CO, same as a completed student who skipped every assessment —
this is deliberate, not a bug: the spec's "include" option doesn't specify
special handling for missing marks, so "no marks recorded" here means what
it means everywhere else in this engine — zero).

PO attainment (`calculate_program_attainment`) rolls this up one level:
for each PO, average the attainment % of every CO mapped to it (weighted by
the CO-PO mapping's strength value, and by each CO's own eligible-student
count across however many sections it was assessed in), restricted to
mappings whose strength is > 0 — a "No" mapping doesn't contribute at all.
This is one defensible, documented methodology, not the only one an
institution might want (spec: "do not hard-code a particular calculation
method unless explicitly configured") — revisit if multiple methodologies
need to coexist.

Cohort filtering (spec §13) reuses `StudentProfile.batch_year` as the
cohort key rather than introducing a separate `Cohort` entity: the spec's
own examples ("Spring 2025 Cohort", "Fall 2025 Cohort") are exactly an
intake-year grouping, which `batch_year` already captures, and every
student profile already has one. Both calculation functions take an
optional `batch_year` filter; omitting it reports across every cohort
combined. Student-level PO status is still out of scope for this pass —
that's a materially different question (what did *one* student attain)
from "restrict the aggregate to one cohort."
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.tenant.assessments import (
    Assessment,
    AssessmentQuestion,
    CourseAttainmentConfig,
    ProgramAttainmentConfig,
    QuestionCourseOutcomeMapping,
    StudentMark,
)
from app.models.tenant.courses.catalog import Course, CourseVersion
from app.models.tenant.courses.delivery import CourseOffering, CourseSection, StudentEnrollment
from app.models.tenant.courses.grading import GradingBand, GradingPolicy
from app.models.tenant.identity import StudentProfile
from app.models.tenant.mappings import CourseOutcomePOMapping, MappingScaleLevel
from app.models.tenant.obe import CourseOutcome, ProgramOutcome
from app.models.tenant.obe.improvement import ImprovementPlan
from app.models.tenant.org import AcademicTerm, ProgramVersion
from app.schemas.attainment import (
    COContribution,
    CourseAttainmentReport,
    CourseAttainmentSummary,
    CourseOutcomeAttainment,
    ImprovementPlanCounts,
    ProgramAnalyticsSummary,
    ProgramAttainmentReport,
    ProgramOutcomeAttainment,
    StudentAssessmentMark,
    StudentAttainmentSummary,
    StudentCourseOutcomeStatus,
    StudentEnrollmentAttainment,
    StudentProgramOutcomeStatus,
)

_DEFAULT_MIN_MARKS_PERCENT = Decimal("60")
_DEFAULT_MIN_STUDENTS_PERCENT = Decimal("60")
_DEFAULT_MIN_PO_ATTAINMENT_PERCENT = Decimal("60")
_DEFAULT_WI_TREATMENT = "exclude"
_WI_STATUSES = frozenset({"withdrawn", "incomplete"})


def _resolve_course_version_id(db: Session, course_section_id: uuid.UUID) -> uuid.UUID:
    section = db.get(CourseSection, course_section_id)
    if section is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Course section not found")
    offering = db.get(CourseOffering, section.course_offering_id)
    if offering is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Course offering not found")
    return offering.course_version_id


def calculate_course_attainment(
    db: Session, course_section_id: uuid.UUID, *, batch_year: int | None = None
) -> CourseAttainmentReport:
    course_version_id = _resolve_course_version_id(db, course_section_id)

    config = (
        db.query(CourseAttainmentConfig)
        .filter(CourseAttainmentConfig.course_version_id == course_version_id)
        .one_or_none()
    )
    min_marks_percent = config.min_marks_percent if config else _DEFAULT_MIN_MARKS_PERCENT
    min_students_percent = (
        config.min_students_percent if config else _DEFAULT_MIN_STUDENTS_PERCENT
    )
    wi_treatment = config.wi_treatment if config else _DEFAULT_WI_TREATMENT

    enrollments = (
        db.query(StudentEnrollment)
        .filter(StudentEnrollment.course_section_id == course_section_id)
        .all()
    )
    if batch_year is not None:
        cohort_user_ids = {
            row.user_id
            for row in db.query(StudentProfile.user_id)
            .filter(StudentProfile.batch_year == batch_year)
            .all()
        }
        enrollments = [e for e in enrollments if e.student_user_id in cohort_user_ids]
    eligible_enrollments = (
        enrollments
        if wi_treatment == "include"
        else [e for e in enrollments if e.enrollment_status not in _WI_STATUSES]
    )
    eligible_ids = [e.id for e in eligible_enrollments]

    assessment_ids = [
        a.id
        for a in db.query(Assessment.id)
        .filter(Assessment.course_section_id == course_section_id)
        .all()
    ]

    assessment_questions = (
        db.query(AssessmentQuestion)
        .filter(AssessmentQuestion.assessment_id.in_(assessment_ids))
        .all()
        if assessment_ids
        else []
    )
    aq_by_id = {aq.id: aq for aq in assessment_questions}
    question_ids = {aq.question_id for aq in assessment_questions}

    co_mappings = (
        db.query(QuestionCourseOutcomeMapping)
        .filter(QuestionCourseOutcomeMapping.question_id.in_(question_ids))
        .all()
        if question_ids
        else []
    )
    aq_ids_by_co: dict[uuid.UUID, list[uuid.UUID]] = {}
    for aq in assessment_questions:
        for mapping in co_mappings:
            if mapping.question_id == aq.question_id:
                aq_ids_by_co.setdefault(mapping.course_outcome_id, []).append(aq.id)

    all_aq_ids = list(aq_by_id.keys())
    marks_rows = (
        db.query(StudentMark)
        .filter(
            StudentMark.assessment_question_id.in_(all_aq_ids),
            StudentMark.student_enrollment_id.in_(eligible_ids),
        )
        .all()
        if all_aq_ids and eligible_ids
        else []
    )
    marks_by_student_aq: dict[tuple[uuid.UUID, uuid.UUID], Decimal] = {
        (m.student_enrollment_id, m.assessment_question_id): m.marks_obtained for m in marks_rows
    }

    course_outcomes = (
        db.query(CourseOutcome)
        .filter(CourseOutcome.course_version_id == course_version_id)
        .order_by(CourseOutcome.sequence)
        .all()
    )

    outcomes: list[CourseOutcomeAttainment] = []
    for co in course_outcomes:
        aq_ids = aq_ids_by_co.get(co.id, [])
        if not aq_ids or not eligible_enrollments:
            outcomes.append(
                CourseOutcomeAttainment(
                    course_outcome_id=co.id, code=co.code, statement=co.statement, assessed=False
                )
            )
            continue

        marks_allocated = sum((aq_by_id[aq_id].marks_allocated for aq_id in aq_ids), Decimal(0))
        if marks_allocated <= 0:
            outcomes.append(
                CourseOutcomeAttainment(
                    course_outcome_id=co.id, code=co.code, statement=co.statement, assessed=False
                )
            )
            continue

        students_attained = 0
        for enrollment in eligible_enrollments:
            obtained = sum(
                (marks_by_student_aq.get((enrollment.id, aq_id), Decimal(0)) for aq_id in aq_ids),
                Decimal(0),
            )
            student_percent = (obtained / marks_allocated) * 100
            if student_percent >= min_marks_percent:
                students_attained += 1

        attainment_percent = (
            Decimal(students_attained) / Decimal(len(eligible_enrollments)) * 100
        ).quantize(Decimal("0.01"))
        outcomes.append(
            CourseOutcomeAttainment(
                course_outcome_id=co.id,
                code=co.code,
                statement=co.statement,
                assessed=True,
                marks_allocated=marks_allocated,
                students_attained=students_attained,
                eligible_students=len(eligible_enrollments),
                attainment_percent=attainment_percent,
                is_attained=attainment_percent >= min_students_percent,
            )
        )

    return CourseAttainmentReport(
        course_section_id=course_section_id,
        course_version_id=course_version_id,
        min_marks_percent=min_marks_percent,
        min_students_percent=min_students_percent,
        batch_year=batch_year,
        total_enrolled=len(enrollments),
        excluded_wi=len(enrollments) - len(eligible_enrollments),
        eligible_students=len(eligible_enrollments),
        outcomes=outcomes,
    )


def calculate_program_attainment(
    db: Session,
    program_version_id: uuid.UUID,
    *,
    batch_year: int | None = None,
    academic_term_id: uuid.UUID | None = None,
) -> ProgramAttainmentReport:
    program_version = db.get(ProgramVersion, program_version_id)
    if program_version is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Program version not found")

    config = (
        db.query(ProgramAttainmentConfig)
        .filter(ProgramAttainmentConfig.program_version_id == program_version_id)
        .one_or_none()
    )
    min_po_attainment_percent = (
        config.min_po_attainment_percent if config else _DEFAULT_MIN_PO_ATTAINMENT_PERCENT
    )

    offering_query = db.query(CourseOffering.id).filter(
        CourseOffering.program_version_id == program_version_id
    )
    if academic_term_id is not None:
        offering_query = offering_query.filter(
            CourseOffering.academic_term_id == academic_term_id
        )
    offering_ids = [row.id for row in offering_query.all()]
    sections = (
        db.query(CourseSection)
        .filter(CourseSection.course_offering_id.in_(offering_ids))
        .all()
        if offering_ids
        else []
    )

    # Every CO's (attainment_percent, eligible_students) sample from each
    # section it was actually assessed in — aggregated below into one
    # eligible-student-weighted average per CO.
    co_samples: dict[uuid.UUID, list[tuple[Decimal, int]]] = {}
    for section in sections:
        section_report = calculate_course_attainment(db, section.id, batch_year=batch_year)
        for co in section_report.outcomes:
            if co.assessed and co.attainment_percent is not None and co.eligible_students:
                co_samples.setdefault(co.course_outcome_id, []).append(
                    (co.attainment_percent, co.eligible_students)
                )

    def co_aggregate_percent(co_id: uuid.UUID) -> Decimal | None:
        samples = co_samples.get(co_id)
        if not samples:
            return None
        total_students = sum(n for _pct, n in samples)
        if total_students == 0:
            return None
        weighted_sum = sum(pct * n for pct, n in samples)
        return (weighted_sum / Decimal(total_students)).quantize(Decimal("0.01"))

    program_outcomes = (
        db.query(ProgramOutcome)
        .filter(ProgramOutcome.program_version_id == program_version_id)
        .order_by(ProgramOutcome.sequence)
        .all()
    )

    course_outcome_cache: dict[uuid.UUID, CourseOutcome] = {}
    course_code_cache: dict[uuid.UUID, str] = {}  # course_version_id -> course code

    def course_code_for(course_version_id: uuid.UUID) -> str:
        if course_version_id not in course_code_cache:
            cv = db.get(CourseVersion, course_version_id)
            course = db.get(Course, cv.course_id) if cv else None
            course_code_cache[course_version_id] = course.code if course else "?"
        return course_code_cache[course_version_id]

    outcomes: list[ProgramOutcomeAttainment] = []
    for po in program_outcomes:
        mapping_rows = (
            db.query(CourseOutcomePOMapping, MappingScaleLevel)
            .join(
                MappingScaleLevel,
                CourseOutcomePOMapping.mapping_scale_level_id == MappingScaleLevel.id,
            )
            .filter(CourseOutcomePOMapping.program_outcome_id == po.id)
            .all()
        )

        contributions: list[COContribution] = []
        weighted_sum = Decimal(0)
        total_weight = Decimal(0)
        for mapping, level in mapping_rows:
            if level.value <= 0:
                continue  # "No" mapping strength — doesn't contribute to the PO at all
            co = course_outcome_cache.get(mapping.course_outcome_id) or db.get(
                CourseOutcome, mapping.course_outcome_id
            )
            if co is None:
                continue
            course_outcome_cache[co.id] = co
            co_percent = co_aggregate_percent(co.id)
            contributions.append(
                COContribution(
                    course_outcome_id=co.id,
                    course_code=course_code_for(co.course_version_id),
                    co_code=co.code,
                    mapping_strength=level.value,
                    co_attainment_percent=co_percent,
                )
            )
            if co_percent is not None:
                weighted_sum += co_percent * level.value
                total_weight += level.value

        if total_weight > 0:
            po_percent = (weighted_sum / total_weight).quantize(Decimal("0.01"))
            outcomes.append(
                ProgramOutcomeAttainment(
                    program_outcome_id=po.id,
                    code=po.code,
                    statement=po.statement,
                    assessed=True,
                    attainment_percent=po_percent,
                    is_attained=po_percent >= min_po_attainment_percent,
                    contributions=contributions,
                )
            )
        else:
            outcomes.append(
                ProgramOutcomeAttainment(
                    program_outcome_id=po.id,
                    code=po.code,
                    statement=po.statement,
                    assessed=False,
                    contributions=contributions,
                )
            )

    return ProgramAttainmentReport(
        program_version_id=program_version_id,
        min_po_attainment_percent=min_po_attainment_percent,
        batch_year=batch_year,
        sections_included=len(sections),
        outcomes=outcomes,
    )


def calculate_program_analytics_summary(
    db: Session, program_version_id: uuid.UUID, *, batch_year: int | None = None
) -> ProgramAnalyticsSummary:
    """Spec §15's program dashboard: the PO summary (reused as-is from
    `calculate_program_attainment`) plus a per-course rollup (average CO
    attainment, how many COs are below threshold — "courses with weak
    attainment", "COs below threshold") and continuous-improvement plan
    counts by status."""
    po_report = calculate_program_attainment(db, program_version_id, batch_year=batch_year)

    offering_rows = (
        db.query(CourseOffering)
        .filter(CourseOffering.program_version_id == program_version_id)
        .all()
    )
    offering_by_id = {o.id: o for o in offering_rows}
    sections = (
        db.query(CourseSection)
        .filter(CourseSection.course_offering_id.in_(offering_by_id.keys()))
        .all()
        if offering_by_id
        else []
    )

    sections_by_course_version: dict[uuid.UUID, list[CourseSection]] = {}
    for section in sections:
        offering = offering_by_id.get(section.course_offering_id)
        if offering is None:
            continue
        sections_by_course_version.setdefault(offering.course_version_id, []).append(section)

    course_summaries: list[CourseAttainmentSummary] = []
    for course_version_id, secs in sections_by_course_version.items():
        cv = db.get(CourseVersion, course_version_id)
        course = db.get(Course, cv.course_id) if cv else None
        config = (
            db.query(CourseAttainmentConfig)
            .filter(CourseAttainmentConfig.course_version_id == course_version_id)
            .one_or_none()
        )
        threshold = config.min_students_percent if config else _DEFAULT_MIN_STUDENTS_PERCENT

        co_samples: dict[uuid.UUID, list[tuple[Decimal, int]]] = {}
        for section in secs:
            report = calculate_course_attainment(db, section.id, batch_year=batch_year)
            for co in report.outcomes:
                if co.assessed and co.attainment_percent is not None and co.eligible_students:
                    co_samples.setdefault(co.course_outcome_id, []).append(
                        (co.attainment_percent, co.eligible_students)
                    )

        co_percents: list[Decimal] = []
        for samples in co_samples.values():
            total_students = sum(n for _pct, n in samples)
            if total_students:
                co_percents.append(sum(pct * n for pct, n in samples) / Decimal(total_students))

        course_summaries.append(
            CourseAttainmentSummary(
                course_version_id=course_version_id,
                course_code=course.code if course else "?",
                course_title=course.title if course else "?",
                cos_assessed=len(co_percents),
                cos_below_threshold=sum(1 for p in co_percents if p < threshold),
                average_co_attainment_percent=(
                    (sum(co_percents) / Decimal(len(co_percents))).quantize(Decimal("0.01"))
                    if co_percents
                    else None
                ),
            )
        )
    course_summaries.sort(
        key=lambda c: (
            c.average_co_attainment_percent is None,
            c.average_co_attainment_percent or Decimal(0),
        )
    )

    plan_counts_query = (
        db.query(ImprovementPlan.status, func.count(ImprovementPlan.id))
        .join(CourseSection, ImprovementPlan.course_section_id == CourseSection.id)
        .filter(CourseSection.course_offering_id.in_(offering_by_id.keys()))
        .group_by(ImprovementPlan.status)
        .all()
        if offering_by_id
        else []
    )
    counts = ImprovementPlanCounts()
    counts_by_status = dict(plan_counts_query)
    counts.proposed = counts_by_status.get("proposed", 0)
    counts.approved = counts_by_status.get("approved", 0)
    counts.rejected = counts_by_status.get("rejected", 0)
    counts.implemented = counts_by_status.get("implemented", 0)
    counts.total = counts.proposed + counts.approved + counts.rejected + counts.implemented

    return ProgramAnalyticsSummary(
        program_version_id=program_version_id,
        batch_year=batch_year,
        po_outcomes=po_report.outcomes,
        course_summaries=course_summaries,
        improvement_plan_counts=counts,
    )


def resolve_letter_grade(
    db: Session, program_version_id: uuid.UUID, percent: Decimal
) -> tuple[str | None, Decimal | None]:
    """A program's own grading policy wins over the institution-wide
    default (`GradingPolicy.is_default`, `program_version_id IS NULL`) —
    same precedence a program-specific policy is meant to express. Returns
    (None, None) if no policy is configured at all, or if `percent` falls
    outside every band (e.g. a negative sentinel like I/W/AW's -1.00,
    which is deliberately unreachable by a real percentage)."""
    policy = (
        db.query(GradingPolicy)
        .filter(GradingPolicy.program_version_id == program_version_id)
        .one_or_none()
    )
    if policy is None:
        policy = (
            db.query(GradingPolicy)
            .filter(GradingPolicy.program_version_id.is_(None), GradingPolicy.is_default.is_(True))
            .one_or_none()
        )
    if policy is None:
        return None, None

    band = (
        db.query(GradingBand)
        .filter(
            GradingBand.grading_policy_id == policy.id,
            GradingBand.min_percentage <= percent,
            GradingBand.max_percentage >= percent,
        )
        .one_or_none()
    )
    if band is None:
        return None, None
    return band.letter_grade, band.grade_point


def get_student_attainment_summary(
    db: Session, student_user_id: uuid.UUID, program_version_id: uuid.UUID
) -> StudentAttainmentSummary:
    """Spec §14's student dashboard: marks, per-CO score/threshold/status,
    and PO status — all scoped to `student_user_id`'s own enrollments only
    (the caller is responsible for ensuring `student_user_id` is the
    requesting user; see the `/marks/my-attainment` endpoint, which never
    takes a student id from the client). PO status here is a genuinely
    different question from `calculate_program_attainment`'s aggregate: it
    asks "did *this student* attain enough of the COs mapped to this PO",
    using the same `min_po_attainment_percent` threshold but applied to one
    student's own attained/not-attained COs rather than a cohort-wide %."""
    offering_ids = [
        row.id
        for row in db.query(CourseOffering.id)
        .filter(CourseOffering.program_version_id == program_version_id)
        .all()
    ]
    sections = (
        db.query(CourseSection)
        .filter(CourseSection.course_offering_id.in_(offering_ids))
        .all()
        if offering_ids
        else []
    )
    section_by_id = {s.id: s for s in sections}
    offering_rows = (
        db.query(CourseOffering).filter(CourseOffering.id.in_(offering_ids)).all()
        if offering_ids
        else []
    )
    offering_by_id = {o.id: o for o in offering_rows}

    my_enrollments = (
        db.query(StudentEnrollment)
        .filter(
            StudentEnrollment.student_user_id == student_user_id,
            StudentEnrollment.course_section_id.in_(section_by_id.keys()),
        )
        .all()
        if section_by_id
        else []
    )

    enrollment_reports: list[StudentEnrollmentAttainment] = []
    co_attained_by_id: dict[uuid.UUID, list[bool]] = {}

    for enrollment in my_enrollments:
        section = section_by_id[enrollment.course_section_id]
        offering = offering_by_id[section.course_offering_id]
        course_version_id = offering.course_version_id
        cv = db.get(CourseVersion, course_version_id)
        course = db.get(Course, cv.course_id) if cv else None
        term = db.get(AcademicTerm, offering.academic_term_id)

        config = (
            db.query(CourseAttainmentConfig)
            .filter(CourseAttainmentConfig.course_version_id == course_version_id)
            .one_or_none()
        )
        min_marks_percent = config.min_marks_percent if config else _DEFAULT_MIN_MARKS_PERCENT

        assessments = db.query(Assessment).filter(Assessment.course_section_id == section.id).all()
        assessment_marks: list[StudentAssessmentMark] = []
        total_obtained = Decimal(0)
        total_max = Decimal(0)
        for a in assessments:
            aq_ids = [
                row.id
                for row in db.query(AssessmentQuestion.id)
                .filter(AssessmentQuestion.assessment_id == a.id)
                .all()
            ]
            marks_rows = (
                db.query(StudentMark)
                .filter(
                    StudentMark.assessment_question_id.in_(aq_ids),
                    StudentMark.student_enrollment_id == enrollment.id,
                )
                .all()
                if aq_ids
                else []
            )
            obtained = (
                sum((m.marks_obtained for m in marks_rows), Decimal(0)) if marks_rows else None
            )
            assessment_marks.append(
                StudentAssessmentMark(
                    assessment_id=a.id, title=a.title, max_marks=a.max_marks, obtained=obtained
                )
            )
            total_max += a.max_marks
            if obtained is not None:
                total_obtained += obtained

        all_aqs = (
            db.query(AssessmentQuestion)
            .join(Assessment, AssessmentQuestion.assessment_id == Assessment.id)
            .filter(Assessment.course_section_id == section.id)
            .all()
        )
        aq_by_id = {aq.id: aq for aq in all_aqs}
        question_ids = {aq.question_id for aq in all_aqs}
        co_mappings = (
            db.query(QuestionCourseOutcomeMapping)
            .filter(QuestionCourseOutcomeMapping.question_id.in_(question_ids))
            .all()
            if question_ids
            else []
        )
        aq_ids_by_co: dict[uuid.UUID, list[uuid.UUID]] = {}
        for aq in all_aqs:
            for m in co_mappings:
                if m.question_id == aq.question_id:
                    aq_ids_by_co.setdefault(m.course_outcome_id, []).append(aq.id)

        marks_by_aq = {
            m.assessment_question_id: m.marks_obtained
            for m in db.query(StudentMark)
            .filter(StudentMark.student_enrollment_id == enrollment.id)
            .all()
        }

        course_outcomes = (
            db.query(CourseOutcome)
            .filter(CourseOutcome.course_version_id == course_version_id)
            .order_by(CourseOutcome.sequence)
            .all()
        )
        co_statuses: list[StudentCourseOutcomeStatus] = []
        for co in course_outcomes:
            aq_ids = aq_ids_by_co.get(co.id, [])
            marks_allocated = sum((aq_by_id[i].marks_allocated for i in aq_ids), Decimal(0))
            if not aq_ids or marks_allocated <= 0:
                co_statuses.append(
                    StudentCourseOutcomeStatus(
                        course_outcome_id=co.id,
                        code=co.code,
                        statement=co.statement,
                        threshold_percent=min_marks_percent,
                    )
                )
                continue
            obtained = sum((marks_by_aq.get(i, Decimal(0)) for i in aq_ids), Decimal(0))
            score_percent = (obtained / marks_allocated * 100).quantize(Decimal("0.01"))
            attained = score_percent >= min_marks_percent
            co_statuses.append(
                StudentCourseOutcomeStatus(
                    course_outcome_id=co.id,
                    code=co.code,
                    statement=co.statement,
                    score_percent=score_percent,
                    threshold_percent=min_marks_percent,
                    attained=attained,
                )
            )
            co_attained_by_id.setdefault(co.id, []).append(attained)

        # Only resolve a letter grade once every assessment has been marked —
        # an in-progress term (some assessments still `obtained=None`) would
        # otherwise score as if the ungraded work were a zero, understating
        # the grade rather than just omitting it.
        fully_graded = len(assessment_marks) > 0 and all(
            a.obtained is not None for a in assessment_marks
        )
        if fully_graded and total_max > 0:
            percent = (total_obtained / total_max * 100).quantize(Decimal("0.01"))
            letter_grade, grade_point = resolve_letter_grade(db, program_version_id, percent)
        else:
            letter_grade, grade_point = None, None

        enrollment_reports.append(
            StudentEnrollmentAttainment(
                course_section_id=section.id,
                course_code=course.code if course else "?",
                course_title=course.title if course else "?",
                section_code=section.section_code,
                academic_term_id=offering.academic_term_id,
                term_name=term.name if term else "?",
                enrollment_status=enrollment.enrollment_status,
                assessments=assessment_marks,
                total_obtained=total_obtained,
                total_max=total_max,
                letter_grade=letter_grade,
                grade_point=grade_point,
                course_outcomes=co_statuses,
            )
        )

    po_config = (
        db.query(ProgramAttainmentConfig)
        .filter(ProgramAttainmentConfig.program_version_id == program_version_id)
        .one_or_none()
    )
    min_po_attainment_percent = (
        po_config.min_po_attainment_percent if po_config else _DEFAULT_MIN_PO_ATTAINMENT_PERCENT
    )

    program_outcomes = (
        db.query(ProgramOutcome)
        .filter(ProgramOutcome.program_version_id == program_version_id)
        .order_by(ProgramOutcome.sequence)
        .all()
    )
    po_status: list[StudentProgramOutcomeStatus] = []
    for po in program_outcomes:
        mapping_rows = (
            db.query(CourseOutcomePOMapping, MappingScaleLevel)
            .join(
                MappingScaleLevel,
                CourseOutcomePOMapping.mapping_scale_level_id == MappingScaleLevel.id,
            )
            .filter(CourseOutcomePOMapping.program_outcome_id == po.id)
            .all()
        )
        total = 0
        attained_count = 0
        for mapping, level in mapping_rows:
            if level.value <= 0:
                continue
            attempts = co_attained_by_id.get(mapping.course_outcome_id)
            if not attempts:
                continue
            total += 1
            if any(attempts):
                attained_count += 1

        po_status.append(
            StudentProgramOutcomeStatus(
                program_outcome_id=po.id,
                code=po.code,
                statement=po.statement,
                contributing_cos_total=total,
                contributing_cos_attained=attained_count,
                attained=(
                    (Decimal(attained_count) / Decimal(total) * 100) >= min_po_attainment_percent
                    if total
                    else None
                ),
            )
        )

    return StudentAttainmentSummary(
        program_version_id=program_version_id,
        enrollments=enrollment_reports,
        po_status=po_status,
    )
