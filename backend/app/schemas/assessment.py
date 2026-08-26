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
    status: WorkflowStatus
    created_at: datetime
    updated_at: datetime


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
