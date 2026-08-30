"""Schemas for Course Files (Faculty Module spec §5-9): the seeded document
catalogue, admin-configured per-semester requirements, and per-section
submissions."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class CourseFileTypeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    key: str
    name: str
    category: str
    applicable_course_type: str
    is_custom: bool


class CourseFileRequirementCreate(BaseModel):
    academic_term_id: uuid.UUID
    course_file_type_id: uuid.UUID
    # Exactly one of these three should be set — see
    # app.services.course_files.resolve_requirements for precedence.
    program_version_id: uuid.UUID | None = None
    course_type: str | None = None
    course_version_id: uuid.UUID | None = None
    is_required: bool = True
    deadline: date | None = None
    soft_copy_required: bool = True
    hard_copy_required: bool = False


class CourseFileRequirementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    academic_term_id: uuid.UUID
    course_file_type_id: uuid.UUID
    program_version_id: uuid.UUID | None
    course_type: str | None
    course_version_id: uuid.UUID | None
    is_required: bool
    deadline: date | None
    soft_copy_required: bool
    hard_copy_required: bool
    created_at: datetime
    updated_at: datetime


class CourseFileRequirementImport(BaseModel):
    from_academic_term_id: uuid.UUID
    to_academic_term_id: uuid.UUID


class CourseFileSubmissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    course_section_id: uuid.UUID
    course_file_type_id: uuid.UUID
    file_name: str
    file_size: int
    content_type: str
    version: int
    hard_copy_submitted: bool
    status: str
    submitted_by: uuid.UUID | None
    submitted_at: datetime
    reviewed_by: uuid.UUID | None
    reviewed_at: datetime | None
    review_note: str | None


class CourseFileSubmissionReview(BaseModel):
    status: str  # "approved" | "rejected"
    review_note: str | None = None


class CourseFileChecklistItem(BaseModel):
    """One row of a section's resolved Course Files checklist — a file type
    paired with whichever requirement rule applies (if any) and the current
    submission (if any). Distinct upload controls per spec BR-04 — the
    frontend renders one of these per row, never one generic upload button."""

    file_type: CourseFileTypeRead
    requirement: CourseFileRequirementRead | None
    submission: CourseFileSubmissionRead | None
