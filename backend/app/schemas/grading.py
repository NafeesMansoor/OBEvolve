"""Schemas for grading policy (DATABASE_PLAN.md §C, "Grading policy")."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


# --- GradingPolicy ---
class GradingPolicyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    program_version_id: uuid.UUID | None = None
    is_default: bool = False
    description: str | None = None


class GradingPolicyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    program_version_id: uuid.UUID | None
    is_default: bool
    description: str | None
    created_at: datetime
    updated_at: datetime


# --- GradingBand ---
class GradingBandCreate(BaseModel):
    grading_policy_id: uuid.UUID
    letter_grade: str = Field(min_length=1, max_length=5)
    min_percentage: Decimal
    max_percentage: Decimal
    grade_point: Decimal | None = None
    sequence: int


class GradingBandRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    grading_policy_id: uuid.UUID
    letter_grade: str
    min_percentage: Decimal
    max_percentage: Decimal
    grade_point: Decimal | None
    sequence: int
    created_at: datetime
    updated_at: datetime
