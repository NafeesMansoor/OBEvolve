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
    program version; a program may instead define its own policy."""

    __tablename__ = "grading_policies"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    program_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("program_versions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
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
