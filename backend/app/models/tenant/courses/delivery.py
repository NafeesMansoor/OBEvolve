"""Course delivery/scheduling (DATABASE_PLAN.md §C — implemented): offerings,
sections, faculty assignments, student enrollment.

Distinct from `courses.catalog` (the curriculum-level `Course`/`CourseVersion`
definition, which is versioned and institution-wide) — these tables are the
per-term operational layer: a `CourseVersion` is *offered* in a given
`AcademicTerm`, split into `CourseSection`s, staffed by `FacultyAssignment`s,
and students `StudentEnrollment` into a specific section.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TenantBase, TimestampMixin, UUIDPKMixin


class CourseOffering(UUIDPKMixin, TimestampMixin, TenantBase):
    """One `CourseVersion` scheduled in one `AcademicTerm`, optionally scoped
    to a specific `ProgramVersion` (nullable — the same offering can serve
    multiple programs' students).

    schema="program": see docs/adr/0003-schema-per-program.md.
    `course_version_id`/`academic_term_id` point into the institution-shared
    schema (the `None` translate-map key) and need no schema= override, but
    `program_version_id` targets `program_versions` — also schema="program"
    — and needs the explicit `program.` prefix (see
    `app.models.tenant.obe.outcomes.PEO`'s docstring for why).
    """

    __tablename__ = "course_offerings"
    __table_args__ = {"schema": "program"}

    course_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("course_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    academic_term_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_terms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    program_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("program.program_versions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    sections: Mapped[list[CourseSection]] = relationship(back_populates="course_offering")


class CourseSection(UUIDPKMixin, TimestampMixin, TenantBase):
    """One taught section of a `CourseOffering` (e.g. "Section A").

    schema="program": see docs/adr/0003-schema-per-program.md. `course_offering_id`
    targets `course_offerings` — also schema="program" — so it needs the
    explicit `program.` prefix (see `app.models.tenant.obe.outcomes.PEO`'s
    docstring for why).
    """

    __tablename__ = "course_sections"
    __table_args__ = {"schema": "program"}

    course_offering_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("program.course_offerings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    section_code: Mapped[str] = mapped_column(String(20), nullable=False)
    max_students: Mapped[int | None] = mapped_column(Integer, nullable=True)

    course_offering: Mapped[CourseOffering] = relationship(back_populates="sections")


class FacultyAssignment(UUIDPKMixin, TimestampMixin, TenantBase):
    """A faculty member's role on a `CourseSection` — "coordinator" or
    "instructor". Kept as a free string rather than an enum table since the
    role set is small and institution-invariant (mirrors `Course.course_type`'s
    precedent for simple free-text categorical columns).

    schema="program": see docs/adr/0003-schema-per-program.md.
    `faculty_user_id` points into the institution-shared schema (the `None`
    translate-map key) and needs no schema= override, but `course_section_id`
    targets `course_sections` — also schema="program" — and needs the
    explicit `program.` prefix (see `app.models.tenant.obe.outcomes.PEO`'s
    docstring for why).
    """

    __tablename__ = "faculty_assignments"
    __table_args__ = {"schema": "program"}

    course_section_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("program.course_sections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    faculty_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    # Faculty Module spec §4.1: the only Course Settings fields a faculty
    # member can edit directly (everything else routes through a change
    # request) — properties of *this instructor teaching this section*, not
    # of the section itself, so they live here rather than on CourseSection
    # (two co-instructors of the same section could hold different office
    # hours). Editable only by the row's own `faculty_user_id`.
    office_location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    consultation_hours: Mapped[str | None] = mapped_column(String(255), nullable=True)
    meeting_link: Mapped[str | None] = mapped_column(String(500), nullable=True)


class StudentEnrollment(UUIDPKMixin, TenantBase):
    """A student's enrollment into one `CourseSection`. No `TimestampMixin`
    `updated_at` churn expected here beyond `enrollment_status`, but
    `enrolled_at` is tracked explicitly (server-side `now()`) since it is a
    domain fact, not bookkeeping metadata.

    schema="program": see docs/adr/0003-schema-per-program.md.
    `student_user_id` points into the institution-shared schema (the `None`
    translate-map key) and needs no schema= override, but `course_section_id`
    targets `course_sections` — also schema="program" — and needs the
    explicit `program.` prefix (see `app.models.tenant.obe.outcomes.PEO`'s
    docstring for why).
    """

    __tablename__ = "student_enrollments"
    __table_args__ = {"schema": "program"}

    student_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    course_section_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("program.course_sections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    enrollment_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="enrolled"
    )
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
