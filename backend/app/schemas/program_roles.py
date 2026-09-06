"""Schemas for program-scoped role management (a Program Administrator/
Coordinator managing Faculty/Course Coordinator/Course Administrator roles
within their own program — see
app.api.v1.endpoints.program_roles's module docstring)."""

from __future__ import annotations

import uuid

from pydantic import BaseModel, ConfigDict, Field


class ProgramFacultyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str


class ProgramCourseRead(BaseModel):
    id: uuid.UUID
    code: str
    title: str


class ProgramRoleGrantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    role_id: uuid.UUID
    scope_type: str | None
    scope_id: uuid.UUID | None


class ProgramRosterRead(BaseModel):
    faculty: list[ProgramFacultyRead]
    assignable_roles: list[dict[str, str]]
    courses: list[ProgramCourseRead]
    grants: list[ProgramRoleGrantRead]


class ProgramRoleGrantCreate(BaseModel):
    user_id: uuid.UUID
    role_id: uuid.UUID
    # "program" grants apply across the whole program (e.g. Faculty);
    # "course" grants need course_id (e.g. Course Coordinator for one
    # specific course within this program).
    scope_type: str = Field(pattern="^(program|course)$")
    course_id: uuid.UUID | None = None
