"""Mapping scales + CO-PO / PO-PEO junction tables (DATABASE_PLAN.md §E).

All normalized junction tables — never comma-separated strings or JSON blobs
(spec §7). Left empty by the ULAB CSE seed: CO-PO and PEO-PO mapping data was
deliberately excluded from curriculum-document extraction — mappings must be
entered/approved through the application itself.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TenantBase, TimestampMixin, UUIDPKMixin


class MappingScale(UUIDPKMixin, TimestampMixin, TenantBase):
    """Correlation scales are institution-configurable (spec §14: binary
    Yes/No, ternary None/Low/High, four-level None/Low/Medium/High, etc.)."""

    __tablename__ = "mapping_scales"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    levels: Mapped[list[MappingScaleLevel]] = relationship(back_populates="mapping_scale")


class MappingScaleLevel(UUIDPKMixin, TimestampMixin, TenantBase):
    __tablename__ = "mapping_scale_levels"

    mapping_scale_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("mapping_scales.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    value: Mapped[int] = mapped_column(Integer, nullable=False)
    label: Mapped[str] = mapped_column(String(50), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)

    mapping_scale: Mapped[MappingScale] = relationship(back_populates="levels")


class CourseOutcomePOMapping(UUIDPKMixin, TimestampMixin, TenantBase):
    __tablename__ = "course_outcome_po_mappings"

    course_outcome_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("course_outcomes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    program_outcome_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("program_outcomes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    mapping_scale_level_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("mapping_scale_levels.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)


class ProgramOutcomePEOMapping(UUIDPKMixin, TimestampMixin, TenantBase):
    __tablename__ = "program_outcome_peo_mappings"

    program_outcome_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("program_outcomes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    peo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("peos.id", ondelete="CASCADE"), nullable=False, index=True
    )
    mapping_scale_level_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("mapping_scale_levels.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    remarks: Mapped[str | None] = mapped_column(Text, nullable=True)
