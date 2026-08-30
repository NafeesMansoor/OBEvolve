"""Course catalog (DATABASE_PLAN.md §C — implemented).

Delivery/scheduling (offerings/sections/faculty assignments/enrollment) lives
in `app.models.tenant.courses.delivery`; grading policy in
`app.models.tenant.courses.grading`. `course_prerequisites` alone stays
planned — no source data for it yet.
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
    # "theory" | "lab" — distinct from the free-text `course_type` category
    # label above; this drives which Course Files checklist applies
    # (Faculty Module spec §6 vs §7), nothing else. Defaults to "theory"
    # since most courses are lecture-based; labs are the minority that need
    # explicit marking.
    delivery_format: Mapped[str] = mapped_column(String(10), nullable=False, default="theory")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    # Self-referential, nullable, one-directional: "this course is also
    # offered as/with that course" (e.g. a cross-listed course taught
    # jointly for two department-specific codes, or two labs bundled under
    # one lecture). Deliberately a single link, not a many-to-many junction
    # table — the source curriculum data models co-offering as a single pair
    # ("CSE2103 & 2104" appearing as one catalog row), and a richer network
    # of >2 co-offered courses hasn't come up; revisit if it does. SET NULL
    # on delete rather than CASCADE: deleting one side of a co-offered pair
    # should not take the other course down with it.
    co_offered_with_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    versions: Mapped[list[CourseVersion]] = relationship(back_populates="course")
    co_offered_with: Mapped[Course | None] = relationship(
        remote_side="Course.id", foreign_keys=[co_offered_with_id]
    )


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
    # Course outline content (§1/§1.6/§1.7 — deliberately excludes §1.5's
    # week-by-week delivery plan, out of scope) — one line per item,
    # rendered as a bullet list. Admin-edited (PATCH /course-versions/{id});
    # faculty only ever propose a change via CourseChangeRequest.
    objectives: Mapped[str | None] = mapped_column(Text, nullable=True)
    tla_items: Mapped[str | None] = mapped_column(Text, nullable=True)
    learning_materials: Mapped[str | None] = mapped_column(Text, nullable=True)
    target_assessment_weights: Mapped[str | None] = mapped_column(Text, nullable=True)

    course: Mapped[Course] = relationship(back_populates="versions")
