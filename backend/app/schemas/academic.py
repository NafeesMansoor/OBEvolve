"""Schemas for course delivery (offerings/sections/faculty assignments/
enrollment) and student profile + curriculum alignment
(DATABASE_PLAN.md §C)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# --- CourseOffering ---
class CourseOfferingCreate(BaseModel):
    course_version_id: uuid.UUID
    academic_term_id: uuid.UUID
    program_version_id: uuid.UUID | None = None


class CourseOfferingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    course_version_id: uuid.UUID
    academic_term_id: uuid.UUID
    program_version_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


# --- CourseSection ---
class CourseSectionCreate(BaseModel):
    course_offering_id: uuid.UUID
    section_code: str = Field(min_length=1, max_length=20)
    max_students: int | None = None


class CourseSectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    course_offering_id: uuid.UUID
    section_code: str
    max_students: int | None
    created_at: datetime
    updated_at: datetime


# --- FacultyAssignment ---
class FacultyAssignmentCreate(BaseModel):
    course_section_id: uuid.UUID
    faculty_user_id: uuid.UUID
    role: Literal["coordinator", "instructor"]


class FacultyAssignmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    course_section_id: uuid.UUID
    faculty_user_id: uuid.UUID
    role: str
    created_at: datetime
    updated_at: datetime


# --- StudentEnrollment ---
class StudentEnrollmentCreate(BaseModel):
    student_user_id: uuid.UUID
    course_section_id: uuid.UUID
    enrollment_status: str = Field(default="enrolled", max_length=20)


class StudentEnrollmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    student_user_id: uuid.UUID
    course_section_id: uuid.UUID
    enrollment_status: str
    enrolled_at: datetime


# --- Student (User + StudentProfile) ---
class StudentCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=255)
    student_code: str = Field(min_length=1, max_length=50)
    program_id: uuid.UUID | None = None
    program_version_id: uuid.UUID | None = None
    batch_year: int | None = None


class StudentRead(BaseModel):
    user_id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    student_code: str
    program_id: uuid.UUID | None
    program_version_id: uuid.UUID | None
    batch_year: int | None
    status: str


class StudentAlignmentUpdate(BaseModel):
    """Curriculum alignment update — program/version/batch/status."""

    program_id: uuid.UUID | None = None
    program_version_id: uuid.UUID | None = None
    batch_year: int | None = None
    status: str | None = Field(default=None, max_length=20)
