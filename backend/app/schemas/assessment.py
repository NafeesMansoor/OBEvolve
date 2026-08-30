"""Schemas for assessment definition (DATABASE_PLAN.md §F): assessment types,
rubrics, questions, assessments. Marks entry/gradebook is a separate later
feature, not covered here."""

from __future__ import annotations

import uuid
from datetime import date as date_type
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.db.base import WorkflowStatus


# --- AssessmentType ---
class AssessmentTypeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class AssessmentTypeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    is_custom: bool
    requires_documents: bool
    requires_cep_documents: bool
    requires_oep_validation: bool


# --- Rubric ---
class RubricCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    is_reusable: bool = True


class RubricRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    is_reusable: bool
    created_at: datetime
    updated_at: datetime


# --- RubricCriterion ---
class RubricCriterionCreate(BaseModel):
    rubric_id: uuid.UUID
    criterion: str = Field(min_length=1)
    weight: Decimal


class RubricCriterionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    rubric_id: uuid.UUID
    criterion: str
    weight: Decimal
    created_at: datetime
    updated_at: datetime


# --- RubricLevel ---
class RubricLevelCreate(BaseModel):
    rubric_criterion_id: uuid.UUID
    label: str = Field(min_length=1, max_length=100)
    score: Decimal
    description: str | None = None


class RubricLevelRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    rubric_criterion_id: uuid.UUID
    label: str
    score: Decimal
    description: str | None
    created_at: datetime
    updated_at: datetime


# --- Question ---
class QuestionCreate(BaseModel):
    course_version_id: uuid.UUID
    text: str = Field(min_length=1)
    question_type: str = Field(min_length=1, max_length=50)
    difficulty: str | None = None
    marks: Decimal
    topic: str | None = None
    author_id: uuid.UUID | None = None
    # K/P/A classification — Complex Engineering Problem tasks only (§18).
    kpa: str | None = Field(default=None, max_length=1)
    # Question Bank sharing (§17) — default False, opt-in per question.
    is_globally_shared: bool = False


class QuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    course_version_id: uuid.UUID
    text: str
    question_type: str
    difficulty: str | None
    marks: Decimal
    topic: str | None
    status: WorkflowStatus
    author_id: uuid.UUID | None
    reviewer_id: uuid.UUID | None
    kpa: str | None
    is_globally_shared: bool
    created_at: datetime
    updated_at: datetime


# --- Question CO / Bloom mappings ---
class QuestionCourseOutcomeMappingCreate(BaseModel):
    question_id: uuid.UUID
    course_outcome_id: uuid.UUID


class QuestionCourseOutcomeMappingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    question_id: uuid.UUID
    course_outcome_id: uuid.UUID


class QuestionBloomMappingCreate(BaseModel):
    question_id: uuid.UUID
    bloom_level_id: uuid.UUID


class QuestionBloomMappingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    question_id: uuid.UUID
    bloom_level_id: uuid.UUID


# --- Assessment ---
class AssessmentCreate(BaseModel):
    course_section_id: uuid.UUID
    academic_term_id: uuid.UUID
    assessment_type_id: uuid.UUID
    title: str = Field(min_length=1, max_length=255)
    max_marks: Decimal
    weight: Decimal | None = None
    date: date_type | None = None
    duration_minutes: int | None = None
    rubric_id: uuid.UUID | None = None
    # Complex Engineering Problem / Open-Ended Problem "Purpose" (§18-19).
    purpose: str | None = None


class AssessmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    course_section_id: uuid.UUID
    academic_term_id: uuid.UUID
    assessment_type_id: uuid.UUID
    title: str
    max_marks: Decimal
    weight: Decimal | None
    date: date_type | None
    duration_minutes: int | None
    rubric_id: uuid.UUID | None
    purpose: str | None
    status: WorkflowStatus
    document_deadline_extended_to: date_type | None
    document_deadline_extended_by: uuid.UUID | None
    document_deadline_extended_at: datetime | None
    created_at: datetime
    updated_at: datetime


class AssessmentDocumentDeadlineExtend(BaseModel):
    new_deadline: date_type


# --- AssessmentQuestion ---
class AssessmentQuestionCreate(BaseModel):
    assessment_id: uuid.UUID
    question_id: uuid.UUID
    marks_allocated: Decimal
    sequence: int


class AssessmentQuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    assessment_id: uuid.UUID
    question_id: uuid.UUID
    marks_allocated: Decimal
    sequence: int
    created_at: datetime
    updated_at: datetime


# --- AssessmentQuestion PO mapping (Complex Engineering Problem tasks, §18) ---
class AssessmentQuestionProgramOutcomeMappingCreate(BaseModel):
    assessment_question_id: uuid.UUID
    program_outcome_id: uuid.UUID


class AssessmentQuestionProgramOutcomeMappingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    assessment_question_id: uuid.UUID
    program_outcome_id: uuid.UUID


# --- AssessmentDocument (question paper / moderation form / compliance form) ---
class AssessmentDocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    assessment_id: uuid.UUID
    document_type: str
    file_name: str
    file_size: int
    content_type: str
    status: str
    uploaded_by: uuid.UUID | None
    uploaded_at: datetime
    reviewed_by: uuid.UUID | None
    reviewed_at: datetime | None
    review_note: str | None
    created_at: datetime
    updated_at: datetime


class AssessmentDocumentReview(BaseModel):
    status: str = Field(pattern="^(approved|rejected)$")
    review_note: str | None = None


class PendingAssessmentDocument(BaseModel):
    """One row of the Course Coordinator / Program Administrator "pending
    review" aggregation — flattens in the assessment/course context a
    reviewer needs without a second round-trip per document."""

    document: AssessmentDocumentRead
    assessment_id: uuid.UUID
    assessment_title: str
    course_section_id: uuid.UUID
