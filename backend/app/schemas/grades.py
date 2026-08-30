"""Schemas for the Faculty Module Grades tab (spec §21-23): a consolidated
per-section grade sheet and the save/submit workflow that locks it and
triggers a persisted attainment snapshot."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class AssessmentContribution(BaseModel):
    assessment_id: uuid.UUID
    title: str
    weight: Decimal | None
    marks_obtained: Decimal
    max_marks: Decimal
    weighted_percent: Decimal | None


class GradeSheetRow(BaseModel):
    student_enrollment_id: uuid.UUID
    student_user_id: uuid.UUID
    student_name: str
    enrollment_status: str
    assessments: list[AssessmentContribution]
    overall_percent: Decimal | None
    letter_grade: str | None
    grade_point: Decimal | None


class GradeSheetReport(BaseModel):
    course_section_id: uuid.UUID
    rows: list[GradeSheetRow]
    weight_recorded_percent: Decimal
    weight_complete: bool
    marks_complete: bool
    incomplete_assessment_titles: list[str]
    submission_status: str  # "draft" | "submitted"
    submitted_at: datetime | None
    submitted_by: uuid.UUID | None


class GradeSubmissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    course_section_id: uuid.UUID
    status: str
    submitted_by: uuid.UUID | None
    submitted_at: datetime | None
