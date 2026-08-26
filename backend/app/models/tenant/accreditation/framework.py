"""Accreditation body / framework / framework-PO catalogue (DATABASE_PLAN.md §D).

Immutable reference data seeded verbatim from an accrediting body's manual
(e.g. BAETE v3.0 — see `app/seed/baete_v3.py`). Distinct from a program's own
*adopted* outcomes (`app.models.tenant.obe.ProgramOutcome`) — see
docs/adr/0002-framework-aware-outcomes.md.
"""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TenantBase, TimestampMixin, UUIDPKMixin


class AccreditationBody(UUIDPKMixin, TimestampMixin, TenantBase):
    __tablename__ = "accreditation_bodies"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    frameworks: Mapped[list[AccreditationFramework]] = relationship(back_populates="body")


class AccreditationFramework(UUIDPKMixin, TimestampMixin, TenantBase):
    __tablename__ = "accreditation_frameworks"

    accreditation_body_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accreditation_bodies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    body: Mapped[AccreditationBody] = relationship(back_populates="frameworks")
    framework_pos: Mapped[list[FrameworkPO]] = relationship(back_populates="framework")


class FrameworkPO(UUIDPKMixin, TimestampMixin, TenantBase):
    """The framework's own official PO catalogue (e.g. BAETE v3.0's PO1-PO12,
    verbatim). See docs/adr/0002-framework-aware-outcomes.md."""

    __tablename__ = "framework_pos"

    framework_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accreditation_frameworks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    framework: Mapped[AccreditationFramework] = relationship(back_populates="framework_pos")


class KnowledgeProfile(UUIDPKMixin, TimestampMixin, TenantBase):
    """WK1-WK9 — BAETE v3.0 Table 6.1 (or the equivalent for other frameworks)."""

    __tablename__ = "knowledge_profiles"

    framework_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accreditation_frameworks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class ProblemAttribute(UUIDPKMixin, TimestampMixin, TenantBase):
    """WP1-WP7 — BAETE v3.0 Table 6.2 (or the equivalent for other frameworks)."""

    __tablename__ = "problem_attributes"

    framework_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accreditation_frameworks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class EngineeringActivity(UUIDPKMixin, TimestampMixin, TenantBase):
    """EA1-EA5 — BAETE v3.0 Table 6.3 (or the equivalent for other frameworks)."""

    __tablename__ = "engineering_activities"

    framework_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accreditation_frameworks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
