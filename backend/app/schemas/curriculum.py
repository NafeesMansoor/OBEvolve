"""Schemas for curriculum/outcomes/mappings (DATABASE_PLAN.md §D/§E):
accreditation frameworks (read-only), courses/course versions, PEOs, program
outcomes, course outcomes, mapping scales, and CO-PO / PEO-PO mappings.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.db.base import WorkflowStatus


# --- Accreditation frameworks (read-only) ---
class AccreditationBodyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    code: str
    description: str | None
    is_active: bool


class AccreditationFrameworkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    accreditation_body_id: uuid.UUID
    name: str
    version: str
    effective_date: date
    expiry_date: date | None
    description: str | None
    is_active: bool


class FrameworkPORead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    framework_id: uuid.UUID
    code: str
    statement: str
    sequence: int
    is_active: bool


class AccreditationFrameworkDetailRead(AccreditationFrameworkRead):
    framework_pos: list[FrameworkPORead] = Field(default_factory=list)


class KnowledgeProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    framework_id: uuid.UUID
    code: str
    title: str | None
    description: str
    sequence: int
    is_active: bool


class ProblemAttributeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    framework_id: uuid.UUID
    code: str
    title: str | None
    description: str
    sequence: int
    is_active: bool


class EngineeringActivityRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    framework_id: uuid.UUID
    code: str
    title: str | None
    description: str
    sequence: int
    is_active: bool


# --- Courses ---
class CourseCreate(BaseModel):
    department_id: uuid.UUID
    code: str = Field(min_length=1, max_length=50)
    title: str = Field(min_length=1, max_length=255)
    description: str | None = None
    credits: Decimal
    contact_hours: int | None = None
    course_type: str | None = None
    co_offered_with_id: uuid.UUID | None = None


class CourseUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=50)
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    credits: Decimal | None = None
    contact_hours: int | None = None
    course_type: str | None = None
    is_active: bool | None = None
    co_offered_with_id: uuid.UUID | None = None


class CourseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    department_id: uuid.UUID
    code: str
    title: str
    description: str | None
    credits: Decimal
    contact_hours: int | None
    course_type: str | None
    is_active: bool
    co_offered_with_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


# --- Course versions ---
class CourseVersionCreate(BaseModel):
    course_id: uuid.UUID
    version_label: str = Field(min_length=1, max_length=50)
    effective_academic_year_id: uuid.UUID | None = None


class CourseVersionUpdate(BaseModel):
    objectives: str | None = None
    tla_items: str | None = None
    learning_materials: str | None = None
    target_assessment_weights: str | None = None


class CourseVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    course_id: uuid.UUID
    version_label: str
    effective_academic_year_id: uuid.UUID | None
    status: WorkflowStatus
    objectives: str | None
    tla_items: str | None
    learning_materials: str | None
    target_assessment_weights: str | None
    created_by: uuid.UUID | None
    approved_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


# --- PEOs ---
class PEOCreate(BaseModel):
    program_version_id: uuid.UUID
    code: str = Field(min_length=1, max_length=20)
    statement: str = Field(min_length=1)
    description: str | None = None
    sequence: int
    effective_from: date | None = None
    effective_to: date | None = None


class PEOUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=20)
    statement: str | None = Field(default=None, min_length=1)
    description: str | None = None
    sequence: int | None = None
    is_active: bool | None = None
    effective_from: date | None = None
    effective_to: date | None = None


class PEORead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    program_version_id: uuid.UUID
    code: str
    statement: str
    description: str | None
    sequence: int
    is_active: bool
    status: WorkflowStatus
    effective_from: date | None
    effective_to: date | None
    created_by: uuid.UUID | None
    approved_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


# --- Program outcomes ---
class ProgramOutcomeCreate(BaseModel):
    program_version_id: uuid.UUID
    framework_po_id: uuid.UUID | None = None
    code: str = Field(min_length=1, max_length=20)
    title: str | None = None
    statement: str = Field(min_length=1)
    sequence: int
    effective_from: date | None = None
    effective_to: date | None = None


class ProgramOutcomeUpdate(BaseModel):
    framework_po_id: uuid.UUID | None = None
    code: str | None = Field(default=None, min_length=1, max_length=20)
    title: str | None = None
    statement: str | None = Field(default=None, min_length=1)
    sequence: int | None = None
    is_active: bool | None = None
    effective_from: date | None = None
    effective_to: date | None = None


class ProgramOutcomeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    program_version_id: uuid.UUID
    framework_po_id: uuid.UUID | None
    code: str
    title: str | None
    statement: str
    sequence: int
    is_active: bool
    status: WorkflowStatus
    effective_from: date | None
    effective_to: date | None
    created_at: datetime
    updated_at: datetime


# --- Bloom levels (catalogue, seeded with 6 defaults per institution) ---
class BloomLevelCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    sequence_order: int
    is_active: bool = True


class BloomLevelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    sequence_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


# --- Course outcomes ---
class CourseOutcomeCreate(BaseModel):
    course_version_id: uuid.UUID
    code: str = Field(min_length=1, max_length=20)
    statement: str = Field(min_length=1)
    sequence: int
    bloom_target_level_id: uuid.UUID | None = None
    delivery_methods: str | None = None
    assessment_tools: str | None = None


class CourseOutcomeUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=20)
    statement: str | None = Field(default=None, min_length=1)
    sequence: int | None = None
    bloom_target_level_id: uuid.UUID | None = None
    delivery_methods: str | None = None
    assessment_tools: str | None = None
    is_active: bool | None = None


class CourseOutcomeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    course_version_id: uuid.UUID
    code: str
    statement: str
    sequence: int
    bloom_target_level_id: uuid.UUID | None
    delivery_methods: str | None
    assessment_tools: str | None
    is_active: bool
    status: WorkflowStatus
    created_at: datetime
    updated_at: datetime


# --- Mapping scales ---
class MappingScaleLevelCreate(BaseModel):
    value: int
    label: str = Field(min_length=1, max_length=50)
    sequence: int


class MappingScaleLevelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    mapping_scale_id: uuid.UUID
    value: int
    label: str
    sequence: int


class MappingScaleCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None
    levels: list[MappingScaleLevelCreate] = Field(min_length=1)


class MappingScaleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    is_default: bool
    levels: list[MappingScaleLevelRead] = Field(default_factory=list)


# --- CO-PO mappings ---
class CourseOutcomePOMappingCreate(BaseModel):
    course_outcome_id: uuid.UUID
    program_outcome_id: uuid.UUID
    mapping_scale_level_id: uuid.UUID
    remarks: str | None = None


class CourseOutcomePOMappingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    course_outcome_id: uuid.UUID
    program_outcome_id: uuid.UUID
    mapping_scale_level_id: uuid.UUID
    remarks: str | None
    created_at: datetime
    updated_at: datetime


# --- PEO-PO mappings ---
class ProgramOutcomePEOMappingCreate(BaseModel):
    program_outcome_id: uuid.UUID
    peo_id: uuid.UUID
    mapping_scale_level_id: uuid.UUID
    remarks: str | None = None


class ProgramOutcomePEOMappingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    program_outcome_id: uuid.UUID
    peo_id: uuid.UUID
    mapping_scale_level_id: uuid.UUID
    remarks: str | None
    created_at: datetime
    updated_at: datetime
