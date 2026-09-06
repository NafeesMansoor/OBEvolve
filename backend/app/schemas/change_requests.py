"""Schemas for Course Settings change requests (Faculty Module spec §4.2;
extended by docs/course_level_settings_and_approval_workflow.md)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CourseChangeRequestCreate(BaseModel):
    course_section_id: uuid.UUID
    section_key: str = Field(pattern="^(overview|settings|students|assessments)$")
    target_field: str = Field(min_length=1, max_length=30)
    current_value_json: dict | None = None
    proposed_value_json: dict
    reason: str = Field(min_length=1)


class CourseChangeRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    course_section_id: uuid.UUID
    section_key: str
    target_field: str
    current_value_json: dict | None
    proposed_value_json: dict
    edited_value_json: dict | None
    reason: str
    status: str
    requested_by: uuid.UUID
    reviewed_by: uuid.UUID | None
    review_note: str | None
    reviewed_at: datetime | None
    program_coordinator_reviewed_by: uuid.UUID | None
    program_coordinator_review_note: str | None
    program_coordinator_reviewed_at: datetime | None
    edited_by: uuid.UUID | None
    edited_at: datetime | None
    apply_status: str | None
    apply_error: str | None
    created_at: datetime
    updated_at: datetime


class CourseChangeRequestReview(BaseModel):
    status: str = Field(pattern="^(approved|rejected|returned)$")
    review_note: str | None = None
    # If set, the reviewer is editing the proposal before accepting it
    # (spec §6) — recorded as `edited_value_json`, applied instead of
    # `proposed_value_json` on final approval. Ignored for reject/return.
    edited_value_json: dict | None = None
