"""Course catalog (DATABASE_PLAN.md §C — catalog implemented now, delivery
still planned).

`course_prerequisites` / `course_offerings` / `course_sections` /
`faculty_assignments` / `student_enrollments` stay planned — no source data
for them yet.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TenantBase, TimestampMixin, UUIDPKMixin, WorkflowStatus


class Course(UUIDPKMixin, TimestampMixin, TenantBase):
    __tablename__ = "courses"

    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    credits: Mapped[Decimal] = mapped_column(Numeric(4, 2), nullable=False)
    contact_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Free-text category label as published by the source curriculum (e.g.
    # "Major Core", "Concentration Elective (Data Science)") — not an enum,
    # since institution-specific category naming varies (DATABASE_PLAN.md §C).
    course_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    versions: Mapped[list[CourseVersion]] = relationship(back_populates="course")


class CourseVersion(UUIDPKMixin, TimestampMixin, TenantBase):
    __tablename__ = "course_versions"

    course_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("courses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_label: Mapped[str] = mapped_column(String(50), nullable=False)
    # Nullable: curriculum year may predate any academic_years seeded for a
    # fresh tenant (DATABASE_PLAN.md §C).
    effective_academic_year_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[WorkflowStatus] = mapped_column(
        String(20), nullable=False, default=WorkflowStatus.DRAFT
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    course: Mapped[Course] = relationship(back_populates="versions")
