"""Schemas for Course Settings change requests (Faculty Module spec §4.2)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CourseChangeRequestCreate(BaseModel):
    course_section_id: uuid.UUID
    target_field: str = Field(min_length=1, max_length=30)
    current_value_json: dict | None = None
    proposed_value_json: dict
    reason: str = Field(min_length=1)


class CourseChangeRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    course_section_id: uuid.UUID
    target_field: str
    current_value_json: dict | None
    proposed_value_json: dict
    reason: str
    status: str
    requested_by: uuid.UUID
    reviewed_by: uuid.UUID | None
    review_note: str | None
    reviewed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class CourseChangeRequestReview(BaseModel):
    status: str = Field(pattern="^(approved|rejected)$")
    review_note: str | None = None
