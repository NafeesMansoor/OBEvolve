"""PO/PI <-> Knowledge Profile / Complex Engineering Problem / Complex
Engineering Activity mappings (Master_Architecture_Part1.md §17, §19).

Each row maps to exactly one PO **or** one PI, never both and never neither —
spec §19: "The system must prevent ambiguous mapping records." A DB CHECK
constraint enforces this directly rather than relying on API-layer discipline
alone, since these are junction tables reachable from any future direct
writer (raw-data console included).

schema="program": all three target tables (`program_outcomes`,
`performance_indicators`) are schema="program", so both nullable FKs need the
explicit `program.` prefix; `knowledge_profile_id`/`problem_attribute_id`/
`engineering_activity_id` point into the institution-shared framework
catalogue (the `None` translate-map key) and need no override — see
`app.models.tenant.obe.outcomes.PEO`'s docstring for why.
"""

from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import TenantBase, TimestampMixin, UUIDPKMixin

_EXACTLY_ONE_TARGET = (
    "(program_outcome_id IS NOT NULL) != (performance_indicator_id IS NOT NULL)"
)


class ProgramOutcomeKnowledgeProfileMapping(UUIDPKMixin, TimestampMixin, TenantBase):
    __tablename__ = "po_knowledge_profile_mappings"
    __table_args__ = (
        CheckConstraint(_EXACTLY_ONE_TARGET, name="ck_po_kp_mapping_exactly_one_target"),
        {"schema": "program"},
    )

    program_outcome_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("program.program_outcomes.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    performance_indicator_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("program.performance_indicators.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    knowledge_profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_profiles.id", ondelete="RESTRICT"),
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


class ProgramOutcomeProblemAttributeMapping(UUIDPKMixin, TimestampMixin, TenantBase):
    """CEP (Complex Engineering Problem) mapping — spec §15/§17/§19."""

    __tablename__ = "po_problem_attribute_mappings"
    __table_args__ = (
        CheckConstraint(_EXACTLY_ONE_TARGET, name="ck_po_cep_mapping_exactly_one_target"),
        {"schema": "program"},
    )

    program_outcome_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("program.program_outcomes.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    performance_indicator_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("program.performance_indicators.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    problem_attribute_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("problem_attributes.id", ondelete="RESTRICT"),
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


class ProgramOutcomeEngineeringActivityMapping(UUIDPKMixin, TimestampMixin, TenantBase):
    """CEA (Complex Engineering Activity) mapping — spec §16/§17/§19."""

    __tablename__ = "po_engineering_activity_mappings"
    __table_args__ = (
        CheckConstraint(_EXACTLY_ONE_TARGET, name="ck_po_cea_mapping_exactly_one_target"),
        {"schema": "program"},
    )

    program_outcome_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("program.program_outcomes.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    performance_indicator_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("program.performance_indicators.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    engineering_activity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("engineering_activities.id", ondelete="RESTRICT"),
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
