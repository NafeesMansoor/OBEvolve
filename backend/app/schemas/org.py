"""Schemas for the organizational structure & academic calendar
(campuses/schools/departments/programs/program_versions, academic years/terms)."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.base import WorkflowStatus


# --- Campus ---
class CampusCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    code: str = Field(min_length=1, max_length=50)
    address: str | None = None


class CampusUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    code: str | None = Field(default=None, min_length=1, max_length=50)
    address: str | None = None
    is_active: bool | None = None


class CampusRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    institution_id: uuid.UUID
    name: str
    code: str
    address: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


# --- School ---
class SchoolCreate(BaseModel):
    campus_id: uuid.UUID
    name: str = Field(min_length=1, max_length=255)
    code: str = Field(min_length=1, max_length=50)


class SchoolUpdate(BaseModel):
    campus_id: uuid.UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    code: str | None = Field(default=None, min_length=1, max_length=50)
    is_active: bool | None = None


class SchoolRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    campus_id: uuid.UUID
    name: str
    code: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


# --- Department ---
class DepartmentCreate(BaseModel):
    school_id: uuid.UUID
    name: str = Field(min_length=1, max_length=255)
    code: str = Field(min_length=1, max_length=50)


class DepartmentUpdate(BaseModel):
    school_id: uuid.UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    code: str | None = Field(default=None, min_length=1, max_length=50)
    is_active: bool | None = None


class DepartmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    school_id: uuid.UUID
    name: str
    code: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


# --- Program ---
class ProgramCreate(BaseModel):
    department_id: uuid.UUID
    name: str = Field(min_length=1, max_length=255)
    code: str = Field(min_length=1, max_length=50)
    degree_level: str | None = None
    # Ordered session/term names for this program's academic year (e.g.
    # ["Fall", "Spring", "Summer"] or ["Semester 1", "Semester 2"]) — how
    # many sessions/year a program runs, decided at creation time.
    session_names: list[str] = Field(default_factory=list)


class ProgramUpdate(BaseModel):
    # Deliberately no `code` here: it's baked into the program's own
    # database schema name at creation time
    # (tenancy.provision_program_schema) — changing it would require a real
    # schema-rename operation, not a field edit. Recreate the program under
    # a new code if the code itself was wrong.
    department_id: uuid.UUID | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    degree_level: str | None = None
    is_active: bool | None = None
    session_names: list[str] | None = None


class ProgramRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    department_id: uuid.UUID
    name: str
    code: str
    degree_level: str | None
    is_active: bool
    session_names: list[str]
    created_at: datetime
    updated_at: datetime


# --- ProgramVersion ---
class ProgramVersionCreate(BaseModel):
    program_id: uuid.UUID
    version_label: str = Field(min_length=1, max_length=50)
    effective_academic_year_id: uuid.UUID
    # spec §24: link a new revision to the version it supersedes (e.g. "2024"
    # -> previous_version_id of "2022"). Optional — a program's first-ever
    # version has nothing to point at.
    previous_version_id: uuid.UUID | None = None


class ProgramVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    program_id: uuid.UUID
    version_label: str
    effective_academic_year_id: uuid.UUID
    status: WorkflowStatus
    created_by: uuid.UUID | None
    approved_by: uuid.UUID | None
    published_by: uuid.UUID | None
    published_at: datetime | None
    unpublished_by: uuid.UUID | None
    unpublished_at: datetime | None
    previous_version_id: uuid.UUID | None
    po_definition_method: str
    peo_numbering_style: str
    po_numbering_style: str
    created_at: datetime
    updated_at: datetime


# --- AcademicYear ---
class AcademicYearCreate(BaseModel):
    label: str = Field(min_length=1, max_length=20)
    start_date: date
    end_date: date


class AcademicYearRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    label: str
    start_date: date
    end_date: date
    is_active: bool


# --- AcademicTerm ---
class AcademicTermCreate(BaseModel):
    academic_year_id: uuid.UUID
    name: str = Field(min_length=1, max_length=50)
    term_type: str = Field(min_length=1, max_length=30)
    start_date: date
    end_date: date
    add_drop_last_date: date | None = None
    midterm_start_date: date | None = None
    midterm_end_date: date | None = None
    final_exam_start_date: date | None = None
    final_exam_end_date: date | None = None
    result_due_date: date | None = None
    result_publication_date: date | None = None


class AcademicTermUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    term_type: str = Field(min_length=1, max_length=30)
    start_date: date
    end_date: date
    add_drop_last_date: date | None = None
    midterm_start_date: date | None = None
    midterm_end_date: date | None = None
    final_exam_start_date: date | None = None
    final_exam_end_date: date | None = None
    result_due_date: date | None = None
    result_publication_date: date | None = None


class AcademicTermRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    academic_year_id: uuid.UUID
    name: str
    term_type: str
    start_date: date
    end_date: date
    add_drop_last_date: date | None
    midterm_start_date: date | None
    midterm_end_date: date | None
    final_exam_start_date: date | None
    final_exam_end_date: date | None
    result_due_date: date | None
    result_publication_date: date | None
    is_active: bool


# --- Term effective curricula (spec §4) ---
class TermEffectiveCurriculumCreate(BaseModel):
    academic_term_id: uuid.UUID
    program_version_id: uuid.UUID


class TermEffectiveCurriculumRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    academic_term_id: uuid.UUID
    program_version_id: uuid.UUID
    created_by: uuid.UUID | None
    created_at: datetime


# --- Cohorts (spec §5) ---
class CohortCreate(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    intake_term_id: uuid.UUID
    intake_year: int
    program_version_id: uuid.UUID


class CohortUpdate(BaseModel):
    # Deliberately no program_version_id here — spec §5: changing a cohort's
    # curriculum is not a routine field edit, see CohortChangeCurriculum.
    code: str | None = Field(default=None, min_length=1, max_length=50)
    status: str | None = None


class CohortChangeCurriculum(BaseModel):
    program_version_id: uuid.UUID
    reason: str = Field(min_length=1)


class CohortRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    intake_term_id: uuid.UUID
    intake_year: int
    program_version_id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime
