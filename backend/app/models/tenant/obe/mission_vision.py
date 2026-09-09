"""Institutional & Program Mission/Vision framework
(Master_Architecture_Part1.md §7-9).

Institutional mission/vision are institution-shared (tenant schema, the
`None` translate-map key) since they describe the university as a whole.
Program mission/vision — and every mapping that references a program-scoped
row — live in schema="program" alongside `PEO`/`ProgramOutcome`
(docs/adr/0003-schema-per-program.md); see `PEO`'s docstring in
`outcomes.py` for why a same-marker-schema FK still needs the explicit
`program.` prefix while a cross-schema FK into the institution-shared schema
does not.

Vision numbering is a configurable `label` string (e.g. "V1"/"PV1"), not an
auto-numeric identity column — spec §7/§8 explicitly require the numbering
format to be administrator-configurable, not hard-coded.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import TenantBase, TimestampMixin, UUIDPKMixin


class InstitutionalMission(UUIDPKMixin, TimestampMixin, TenantBase):
    __tablename__ = "institutional_missions"

    statement: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class InstitutionalVision(UUIDPKMixin, TimestampMixin, TenantBase):
    __tablename__ = "institutional_visions"

    label: Mapped[str] = mapped_column(String(20), nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class ProgramMission(UUIDPKMixin, TimestampMixin, TenantBase):
    """schema="program": see module docstring."""

    __tablename__ = "program_missions"
    __table_args__ = {"schema": "program"}

    program_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("program.program_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ProgramVision(UUIDPKMixin, TimestampMixin, TenantBase):
    """schema="program": see module docstring."""

    __tablename__ = "program_visions"
    __table_args__ = {"schema": "program"}

    program_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("program.program_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    label: Mapped[str] = mapped_column(String(20), nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class InstitutionalVisionProgramVisionMapping(UUIDPKMixin, TimestampMixin, TenantBase):
    """Structured PV -> V mapping (spec §9) — never free text.

    schema="program": `program_vision_id` targets `program_visions`, also
    schema="program", and needs the explicit prefix; `institutional_vision_id`
    points into the institution-shared schema (the `None` key) and needs no
    schema= override (see `PEO`'s docstring in `outcomes.py`).
    """

    __tablename__ = "institutional_vision_program_vision_mappings"
    __table_args__ = {"schema": "program"}

    program_vision_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("program.program_visions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    institutional_vision_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutional_visions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )


class PeoVisionMapping(UUIDPKMixin, TimestampMixin, TenantBase):
    """PEO -> Program Vision mapping (spec §11) — both sides schema="program",
    both need the explicit prefix (see `PEO`'s docstring in `outcomes.py`)."""

    __tablename__ = "peo_vision_mappings"
    __table_args__ = {"schema": "program"}

    peo_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("program.peos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    program_vision_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("program.program_visions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
