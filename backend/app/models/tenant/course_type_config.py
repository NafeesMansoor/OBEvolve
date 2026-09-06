"""Per-program section-enablement for a `CourseType` (Course-Level Settings
spec §2/§3): whether the Course Overview / Course Settings / Students /
Assessments section is open for a Course Teacher to propose edits to, for
courses classified under a given `CourseType`.

schema="program": deliberately per-program even though `CourseType` itself
is tenant-shared (`app.models.tenant.courses.catalog.CourseType`) — the two
roles the spec names (Program Coordinator, Course Coordinator) are both
program-scoped, and a course's own delivery (`CourseSection`) is always
resolved inside one specific program's schema already, so there is no
cross-program ambiguity in looking up "this section's course type's config
in this program." `course_type_id` points into the institution-shared
schema (the `None` translate-map key) and needs no schema= override — see
`app.models.tenant.courses.delivery.CourseOffering.course_version_id`'s
docstring for the identical cross-schema-FK pattern.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import TenantBase, TimestampMixin, UUIDPKMixin

# The four configurable sections (spec §2) — fixed, not admin-extensible.
SECTION_KEYS: tuple[str, ...] = ("overview", "settings", "students", "assessments")


class CourseTypeSectionConfig(UUIDPKMixin, TimestampMixin, TenantBase):
    __tablename__ = "course_type_section_configs"
    __table_args__ = (
        UniqueConstraint("course_type_id", "section_key", name="uq_course_type_section"),
        {"schema": "program"},
    )

    course_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("course_types.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    section_key: Mapped[str] = mapped_column(String(20), nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
