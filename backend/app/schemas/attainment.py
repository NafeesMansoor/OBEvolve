"""Schemas for marks entry + attainment calculation
(app.models.tenant.assessments.marks, app.services.attainment)."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

WITreatment = Literal["exclude", "include"]


# --- StudentMark ---
class StudentMarkCreate(BaseModel):
    assessment_question_id: uuid.UUID
    student_enrollment_id: uuid.UUID
    marks_obtained: Decimal


class StudentMarkUpdate(BaseModel):
    marks_obtained: Decimal


class StudentMarkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    assessment_question_id: uuid.UUID
    student_enrollment_id: uuid.UUID
    marks_obtained: Decimal
    entered_by: uuid.UUID | None
    entered_at: datetime


class StudentMarkBulkEntry(BaseModel):
    """One grid submission from the marks-entry UI: every cell the user
    touched for one assessment, upserted in one request (unique constraint
    on (assessment_question_id, student_enrollment_id) makes this an
    insert-or-update per row)."""

    entries: list[StudentMarkCreate] = Field(min_length=1)


# --- CourseAttainmentConfig ---
class CourseAttainmentConfigUpsert(BaseModel):
    course_version_id: uuid.UUID
    min_marks_percent: Decimal = Decimal("60")
    min_students_percent: Decimal = Decimal("60")
    wi_treatment: WITreatment = "exclude"


class CourseAttainmentConfigRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    course_version_id: uuid.UUID
    min_marks_percent: Decimal
    min_students_percent: Decimal
    wi_treatment: str
    created_at: datetime
    updated_at: datetime


# --- Attainment report (calculated on demand, not stored) ---
class CourseOutcomeAttainment(BaseModel):
    course_outcome_id: uuid.UUID
    code: str
    statement: str
    assessed: bool
    marks_allocated: Decimal | None = None
    students_attained: int | None = None
    eligible_students: int | None = None
    attainment_percent: Decimal | None = None
    is_attained: bool | None = None


class CourseAttainmentReport(BaseModel):
    course_section_id: uuid.UUID
    course_version_id: uuid.UUID
    min_marks_percent: Decimal
    min_students_percent: Decimal
    batch_year: int | None = None
    total_enrolled: int
    excluded_wi: int
    eligible_students: int
    outcomes: list[CourseOutcomeAttainment]


# --- ProgramAttainmentConfig ---
class ProgramAttainmentConfigUpsert(BaseModel):
    program_version_id: uuid.UUID
    min_po_attainment_percent: Decimal = Decimal("60")


class ProgramAttainmentConfigRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    program_version_id: uuid.UUID
    min_po_attainment_percent: Decimal
    created_at: datetime
    updated_at: datetime


# --- PO attainment report (calculated on demand, rolled up from every
# course_section currently offered under the program version) ---
class COContribution(BaseModel):
    """One CO's contribution to a PO — the "CO-to-PO contribution"
    traceability the spec asks for: which course, what mapping strength,
    and that CO's own aggregate attainment % feeding into the PO figure."""

    course_outcome_id: uuid.UUID
    course_code: str
    co_code: str
    mapping_strength: int
    co_attainment_percent: Decimal | None = None


class ProgramOutcomeAttainment(BaseModel):
    program_outcome_id: uuid.UUID
    code: str
    statement: str
    assessed: bool
    attainment_percent: Decimal | None = None
    is_attained: bool | None = None
    contributions: list[COContribution] = []


class ProgramAttainmentReport(BaseModel):
    program_version_id: uuid.UUID
    min_po_attainment_percent: Decimal
    batch_year: int | None = None
    sections_included: int
    outcomes: list[ProgramOutcomeAttainment]


# --- Program analytics dashboard (spec §15): course-level rollups +
# continuous-improvement counters, alongside the PO summary above ---
class CourseAttainmentSummary(BaseModel):
    course_version_id: uuid.UUID
    course_code: str
    course_title: str
    cos_assessed: int
    cos_below_threshold: int
    average_co_attainment_percent: Decimal | None = None


class ImprovementPlanCounts(BaseModel):
    proposed: int = 0
    approved: int = 0
    rejected: int = 0
    implemented: int = 0
    total: int = 0


class ProgramAnalyticsSummary(BaseModel):
    program_version_id: uuid.UUID
    batch_year: int | None = None
    po_outcomes: list[ProgramOutcomeAttainment]
    course_summaries: list[CourseAttainmentSummary]
    improvement_plan_counts: ImprovementPlanCounts


# --- Student self-service dashboard (spec §14) — "the student should only
# see their own information": every value here is scoped to one student's
# own enrollments, never an aggregate across others. ---
class StudentAssessmentMark(BaseModel):
    assessment_id: uuid.UUID
    title: str
    max_marks: Decimal
    obtained: Decimal | None = None


class StudentCourseOutcomeStatus(BaseModel):
    course_outcome_id: uuid.UUID
    code: str
    statement: str
    score_percent: Decimal | None = None
    threshold_percent: Decimal
    attained: bool | None = None


class StudentEnrollmentAttainment(BaseModel):
    course_section_id: uuid.UUID
    course_code: str
    course_title: str
    section_code: str
    academic_term_id: uuid.UUID
    term_name: str
    enrollment_status: str
    assessments: list[StudentAssessmentMark]
    total_obtained: Decimal
    total_max: Decimal
    letter_grade: str | None = None
    grade_point: Decimal | None = None
    course_outcomes: list[StudentCourseOutcomeStatus]


class StudentProgramOutcomeStatus(BaseModel):
    program_outcome_id: uuid.UUID
    code: str
    statement: str
    contributing_cos_total: int
    contributing_cos_attained: int
    attained: bool | None = None


class StudentAttainmentSummary(BaseModel):
    program_version_id: uuid.UUID
    enrollments: list[StudentEnrollmentAttainment]
    po_status: list[StudentProgramOutcomeStatus]


# --- Assessment weight-sum validation (surfaced, not blocking) ---
class AssessmentWeightSummary(BaseModel):
    course_section_id: uuid.UUID
    assessment_count: int
    weighted_count: int
    total_weight: Decimal
    is_complete: bool
