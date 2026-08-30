"""Course-file repository (Faculty Module spec §5-9): a per-course-section
document checklist, distinct from `AssessmentDocument` (which is scoped to
one assessment and whose requirements are fixed in code). Course files are
a broader per-*section* checklist whose requirements a Program Administrator
or Coordinator configures per semester — required/optional, deadline,
course-wise or holistic — so a real configuration layer is needed here that
`AssessmentDocument` doesn't have.

Three tables:
- `CourseFileType`: the seeded catalogue of document slots (Course Outline,
  Class/Mid-Term/Final-Term Attendance, exam moderation/question/scripts,
  CEP/OEP forms, CO-PO Excel, CQI Form, ...) — same seeded-catalogue shape as
  `AssessmentType`/`BloomLevel` (`app.seed.course_file_defaults`).
- `CourseFileRequirement`: one admin-configured rule per academic term +
  file type, targeted at a program (holistic), a course type ("theory"/
  "lab"), or one specific course version (course-wise) — see
  `app.services.course_files.resolve_requirements` for the
  most-specific-wins resolution across these three nullable scope columns.
- `CourseFileSubmission`: one row per (course_section, file_type) — same
  singleton-replace-in-place + lightweight pending/approved/rejected status
  shape as `AssessmentDocument`, plus a `version` counter (spec §5 asks for
  a visible version number) incremented on each replace.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import TenantBase, TimestampMixin, UUIDPKMixin


class CourseFileType(UUIDPKMixin, TimestampMixin, TenantBase):
    """Seeded default set (`is_custom=False`, `app.seed.course_file_defaults`);
    institutions may add their own (`is_custom=True`) — same convention as
    `AssessmentType`."""

    __tablename__ = "course_file_types"
    __table_args__ = (UniqueConstraint("key", name="uq_course_file_types_key"),)

    key: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # attendance | exam_mid | exam_final | grade | cep | oep | lab | admin
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    # theory | lab | both — which course type this slot applies to (spec §6/§7)
    applicable_course_type: Mapped[str] = mapped_column(String(10), nullable=False, default="both")
    is_custom: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class CourseFileRequirement(UUIDPKMixin, TimestampMixin, TenantBase):
    """One configured rule: is `course_file_type_id` required for the target
    scope in `academic_term_id`, and by when. Exactly one of
    `program_version_id`/`course_type`/`course_version_id` is set, in
    increasing order of specificity — see this module's docstring and
    `app.services.course_files.resolve_requirements`. Institution-shared
    like `AssessmentType`/`GradingPolicy`, even though the courses/programs
    it targets may be program-scoped, because the requirement rule itself
    isn't tied to any one program's physical schema — `program_version_id`
    here is a plain UUID column, not a literal cross-schema FK (mirrors
    `RawDataChangeRequest.scope_id`'s precedent for the same reason).
    """

    __tablename__ = "course_file_requirements"

    academic_term_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_terms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    course_file_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("course_file_types.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Scope columns — most-specific-wins; see class docstring.
    program_version_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    course_type: Mapped[str | None] = mapped_column(String(10), nullable=True)
    course_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("course_versions.id", ondelete="CASCADE"), nullable=True
    )
    is_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    soft_copy_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    hard_copy_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class CourseFileSubmission(UUIDPKMixin, TimestampMixin, TenantBase):
    """schema="program": see docs/adr/0003-schema-per-program.md.
    `course_file_type_id` points into the institution-shared schema (the
    `None` translate-map key) and needs no schema= override, but
    `course_section_id` targets `course_sections` — schema="program" — and
    needs the explicit `program.` prefix.
    """

    __tablename__ = "course_file_submissions"
    __table_args__ = (
        UniqueConstraint(
            "course_section_id", "course_file_type_id", name="uq_course_file_submission_slot"
        ),
        {"schema": "program"},
    )

    course_section_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("program.course_sections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    course_file_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("course_file_types.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    file_key: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    hard_copy_submitted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="pending")
    submitted_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
