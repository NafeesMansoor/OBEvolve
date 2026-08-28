"""Grading policy (DATABASE_PLAN.md §C, "Grading policy (implemented)"):
letter-grade bands used to convert a percentage into a grade + grade point.

Not part of the original DATABASE_PLAN.md §F assessment sketch — added
alongside course delivery since a grading policy is scoped the same way a
course offering is (institution-wide default, or program-version-specific).
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TenantBase, TimestampMixin, UUIDPKMixin


class GradingPolicy(UUIDPKMixin, TimestampMixin, TenantBase):
    """A named set of letter-grade bands. `program_version_id` is nullable —
    an institution-wide default policy (`is_default=True`) has no specific
    program version; a program may instead define its own policy.

    `program_version_id` is a plain UUID with NO database-level foreign key
    (unlike every other program_version_id in this codebase): this table
    stays institution-shared (docs/adr/0003-schema-per-program.md — grading
    is "one institution-wide policy... not per-program"), but
    `program_versions` now lives in a per-program schema, and an institution
    can have more than one program — a single FK constraint can only target
    one fixed schema, so a real constraint here would be architecturally
    unsound the moment a second program exists. Referential integrity for
    this column is enforced at the application layer instead. The
    tenant-schema `grading_policies_program_version_id_fkey` constraint from
    before the schema-per-program migration is dropped in
    alembic/tenant/versions/0008_program_schema_split.py.
    """

    __tablename__ = "grading_policies"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    program_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    bands: Mapped[list[GradingBand]] = relationship(back_populates="grading_policy")


class GradingBand(UUIDPKMixin, TimestampMixin, TenantBase):
    __tablename__ = "grading_bands"

    grading_policy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("grading_policies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    letter_grade: Mapped[str] = mapped_column(String(5), nullable=False)
    min_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    max_percentage: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    grade_point: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)

    grading_policy: Mapped[GradingPolicy] = relationship(back_populates="bands")
