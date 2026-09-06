"""Schemas for Course Types and their per-program section configuration
(docs/course_level_settings_and_approval_workflow.md §1-§3)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CourseTypeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    description: str | None = None


class CourseTypeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SectionConfigRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    section_key: str
    is_enabled: bool


class SectionConfigUpdate(BaseModel):
    is_enabled: bool
