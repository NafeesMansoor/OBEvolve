"""OBE outcome hierarchy (DATABASE_PLAN.md §D), framework-aware per
docs/adr/0002-framework-aware-outcomes.md: a program's *adopted* PEOs/POs are
separate rows from an accreditation framework's own PO catalogue
(`app.models.tenant.accreditation.FrameworkPO`), optionally linked by
`ProgramOutcome.framework_po_id` — never merged or overwritten.
"""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import TenantBase, TimestampMixin, UUIDPKMixin, WorkflowStatus


class BloomLevel(UUIDPKMixin, TimestampMixin, TenantBase):
    """Configurable per institution; seeded with the 6 default levels
    (Remember -> Create)."""

    __tablename__ = "bloom_levels"

    name: Mapped[str] = mapped_column(String(50), nullable=False)
    sequence_order: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class PEO(UUIDPKMixin, TimestampMixin, TenantBase):
    """schema="program": see docs/adr/0003-schema-per-program.md.

    The FK to `program_versions` (also schema="program") MUST spell out the
    `program.` prefix (`ForeignKey("program.program_versions.id")`) even
    though both tables share the "program" marker schema — unlike the
    `None` (institution) schema, SQLAlchemy does not infer a FK target's
    schema from the referencing table's schema, so an unqualified
    `ForeignKey("program_versions.id")` would resolve against a phantom
    schema=None "program_versions" table instead of the real one. Same
    dotted-prefix convention already used for `Campus.institution_id`'s
    `ForeignKey("public.institutions.id")`.
    """

    __tablename__ = "peos"
    __table_args__ = {"schema": "program"}

    program_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("program.program_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    status: Mapped[WorkflowStatus] = mapped_column(
        String(20), nullable=False, default=WorkflowStatus.DRAFT
    )
    effective_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class ProgramOutcome(UUIDPKMixin, TimestampMixin, TenantBase):
    """The program's *adopted* POs — what the program actually publishes and
    assesses against, which may differ in wording from the framework
    (docs/adr/0002-framework-aware-outcomes.md).

    schema="program": see docs/adr/0003-schema-per-program.md.
    `framework_po_id` below points to `framework_pos` (institution-shared,
    the `None` translate-map key) and needs no schema= override, but
    `program_version_id` points to `program_versions` — also schema="program"
    — and DOES need the explicit `program.` prefix; see `PEO`'s docstring for
    why SQLAlchemy can't infer it from the referencing table's own schema.
    """

    __tablename__ = "program_outcomes"
    __table_args__ = {"schema": "program"}

    program_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("program.program_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Set only when this program PO is explicitly understood to be "the same
    # outcome slot" as a framework PO (matched by position/intent, not text
    # similarity); NULL when there's no clean correspondence.
    framework_po_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("framework_pos.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    status: Mapped[WorkflowStatus] = mapped_column(
        String(20), nullable=False, default=WorkflowStatus.DRAFT
    )
    effective_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)


class CourseOutcome(UUIDPKMixin, TimestampMixin, TenantBase):
    __tablename__ = "course_outcomes"

    course_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("course_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    bloom_target_level_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bloom_levels.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    status: Mapped[WorkflowStatus] = mapped_column(
        String(20), nullable=False, default=WorkflowStatus.DRAFT
    )
