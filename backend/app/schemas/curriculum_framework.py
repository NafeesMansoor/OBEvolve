"""Schemas for the Mission/Vision, Performance Indicator, and PO/PI<->K/CEP/CEA
framework additions (Master_Architecture_Part1.md §7-21).

Kept separate from `app.schemas.curriculum` (which predates this spec) rather
than appended to it, matching `curriculum_framework.py` being a new endpoint
module of its own.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.base import WorkflowStatus


# --- Institutional mission/vision ---
class InstitutionalMissionCreate(BaseModel):
    statement: str = Field(min_length=1)


class InstitutionalMissionUpdate(BaseModel):
    statement: str | None = Field(default=None, min_length=1)
    is_active: bool | None = None


class InstitutionalMissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    statement: str
    is_active: bool
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class InstitutionalVisionCreate(BaseModel):
    label: str = Field(min_length=1, max_length=20)
    statement: str = Field(min_length=1)
    sequence: int


class InstitutionalVisionUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=20)
    statement: str | None = Field(default=None, min_length=1)
    sequence: int | None = None
    is_active: bool | None = None


class InstitutionalVisionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    label: str
    statement: str
    sequence: int
    is_active: bool
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


# --- Program mission/vision ---
class ProgramMissionCreate(BaseModel):
    program_version_id: uuid.UUID
    statement: str = Field(min_length=1)


class ProgramMissionUpdate(BaseModel):
    statement: str | None = Field(default=None, min_length=1)
    is_active: bool | None = None


class ProgramMissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    program_version_id: uuid.UUID
    statement: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class ProgramVisionCreate(BaseModel):
    program_version_id: uuid.UUID
    label: str = Field(min_length=1, max_length=20)
    statement: str = Field(min_length=1)
    sequence: int


class ProgramVisionUpdate(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=20)
    statement: str | None = Field(default=None, min_length=1)
    sequence: int | None = None
    is_active: bool | None = None


class ProgramVisionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    program_version_id: uuid.UUID
    label: str
    statement: str
    sequence: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


# --- Vision mappings (structured, spec §9/§11) ---
class InstitutionalVisionProgramVisionMappingCreate(BaseModel):
    program_vision_id: uuid.UUID
    institutional_vision_id: uuid.UUID


class InstitutionalVisionProgramVisionMappingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    program_vision_id: uuid.UUID
    institutional_vision_id: uuid.UUID
    created_at: datetime


class PeoVisionMappingCreate(BaseModel):
    peo_id: uuid.UUID
    program_vision_id: uuid.UUID


class PeoVisionMappingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    peo_id: uuid.UUID
    program_vision_id: uuid.UUID
    created_at: datetime


# --- Program version framework configuration (spec §12/§13) ---
class ProgramVersionFrameworkConfigUpdate(BaseModel):
    po_definition_method: str | None = Field(
        default=None, pattern="^(direct|indicator_based)$"
    )
    peo_numbering_style: str | None = Field(default=None, min_length=1, max_length=20)
    po_numbering_style: str | None = Field(default=None, min_length=1, max_length=20)


class ProgramVersionFrameworkConfigRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    po_definition_method: str
    peo_numbering_style: str
    po_numbering_style: str


# --- Performance indicators (Indicator-Based method only, spec §18) ---
class PerformanceIndicatorCreate(BaseModel):
    program_outcome_id: uuid.UUID
    statement: str = Field(min_length=1)
    sequence: int


class PerformanceIndicatorUpdate(BaseModel):
    statement: str | None = Field(default=None, min_length=1)
    sequence: int | None = None
    is_active: bool | None = None


class PerformanceIndicatorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    program_outcome_id: uuid.UUID
    code: str
    statement: str
    sequence: int
    is_active: bool
    status: WorkflowStatus
    created_at: datetime
    updated_at: datetime


# --- CO <-> PI mapping (Indicator-Based counterpart of CO<->PO, spec §21) ---
class CourseOutcomePIMappingCreate(BaseModel):
    course_outcome_id: uuid.UUID
    performance_indicator_id: uuid.UUID
    mapping_scale_level_id: uuid.UUID
    remarks: str | None = None


class CourseOutcomePIMappingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    course_outcome_id: uuid.UUID
    performance_indicator_id: uuid.UUID
    mapping_scale_level_id: uuid.UUID
    remarks: str | None
    created_at: datetime
    updated_at: datetime


# --- PO/PI <-> Knowledge Profile / CEP / CEA mappings (spec §17/§19) ---
class _POOrPIMappingCreate(BaseModel):
    program_outcome_id: uuid.UUID | None = None
    performance_indicator_id: uuid.UUID | None = None
    mapping_scale_level_id: uuid.UUID
    remarks: str | None = None


class ProgramOutcomeKnowledgeProfileMappingCreate(_POOrPIMappingCreate):
    knowledge_profile_id: uuid.UUID


class ProgramOutcomeKnowledgeProfileMappingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    program_outcome_id: uuid.UUID | None
    performance_indicator_id: uuid.UUID | None
    knowledge_profile_id: uuid.UUID
    mapping_scale_level_id: uuid.UUID
    remarks: str | None
    created_at: datetime


class ProgramOutcomeProblemAttributeMappingCreate(_POOrPIMappingCreate):
    problem_attribute_id: uuid.UUID


class ProgramOutcomeProblemAttributeMappingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    program_outcome_id: uuid.UUID | None
    performance_indicator_id: uuid.UUID | None
    problem_attribute_id: uuid.UUID
    mapping_scale_level_id: uuid.UUID
    remarks: str | None
    created_at: datetime


class ProgramOutcomeEngineeringActivityMappingCreate(_POOrPIMappingCreate):
    engineering_activity_id: uuid.UUID


class ProgramOutcomeEngineeringActivityMappingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    program_outcome_id: uuid.UUID | None
    performance_indicator_id: uuid.UUID | None
    engineering_activity_id: uuid.UUID
    mapping_scale_level_id: uuid.UUID
    remarks: str | None
    created_at: datetime


# --- Program Coordinator feedback (spec §25-26) ---
class CurriculumFeedbackCreate(BaseModel):
    entity_type: str = Field(min_length=1, max_length=30)
    entity_id: uuid.UUID
    comment: str = Field(min_length=1)


class CurriculumFeedbackReview(BaseModel):
    status: str = Field(pattern="^(accepted|ignored|resolved)$")
    review_note: str | None = None


class CurriculumFeedbackRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    entity_type: str
    entity_id: uuid.UUID
    comment: str
    status: str
    submitted_by: uuid.UUID
    reviewed_by: uuid.UUID | None
    review_note: str | None
    reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime
