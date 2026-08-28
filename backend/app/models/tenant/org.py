"""Organizational structure & academic calendar (DATABASE_PLAN.md §A).

`institutions → campuses → schools → departments → programs → program_versions`,
plus `academic_years → academic_terms`.
"""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TenantBase, TimestampMixin, UUIDPKMixin, WorkflowStatus


class Campus(UUIDPKMixin, TimestampMixin, TenantBase):
    __tablename__ = "campuses"

    # The one cross-schema FK: tenant schema -> public schema. Explicit
    # schema="public" is required here because schema_translate_map only
    # rewrites the `None` (tenant) schema key, never an explicitly-set one —
    # see docs/adr/0001-schema-per-tenant.md.
    institution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public.institutions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    schools: Mapped[list[School]] = relationship(back_populates="campus")


class School(UUIDPKMixin, TimestampMixin, TenantBase):
    __tablename__ = "schools"

    campus_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("campuses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    campus: Mapped[Campus] = relationship(back_populates="schools")
    departments: Mapped[list[Department]] = relationship(back_populates="school")


class Department(UUIDPKMixin, TimestampMixin, TenantBase):
    __tablename__ = "departments"

    school_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    school: Mapped[School] = relationship(back_populates="departments")
    programs: Mapped[list[Program]] = relationship(back_populates="department")


class Program(UUIDPKMixin, TimestampMixin, TenantBase):
    __tablename__ = "programs"

    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    degree_level: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    department: Mapped[Department] = relationship(back_populates="programs")
    versions: Mapped[list[ProgramVersion]] = relationship(back_populates="program")


class ProgramVersion(UUIDPKMixin, TimestampMixin, TenantBase):
    """Historical program versions are never edited after `published`; a new
    curriculum change creates a new row (spec §6, §10).

    schema="program": lives in the per-program schema
    (tenant_<institution>__<program_code>), not the institution-shared one —
    see docs/adr/0003-schema-per-program.md. `program_id` still resolves
    correctly across the schema boundary: schema_translate_map's `None` key
    (institution schema) and `"program"` key are both active on every
    program-scoped session, so the plain `ForeignKey("programs.id")` below
    (no explicit schema=) is translated independently of this table's own
    schema — same mechanism as any same-schema FK, just spanning two
    translate-map keys instead of one.
    """

    __tablename__ = "program_versions"
    __table_args__ = {"schema": "program"}

    program_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("programs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_label: Mapped[str] = mapped_column(String(50), nullable=False)
    effective_academic_year_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="RESTRICT"),
        nullable=False,
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

    program: Mapped[Program] = relationship(back_populates="versions")


class AcademicYear(UUIDPKMixin, TenantBase):
    __tablename__ = "academic_years"
    __table_args__ = (UniqueConstraint("label", name="uq_academic_years_label"),)

    label: Mapped[str] = mapped_column(String(20), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    terms: Mapped[list[AcademicTerm]] = relationship(back_populates="academic_year")


class AcademicTerm(UUIDPKMixin, TenantBase):
    __tablename__ = "academic_terms"

    academic_year_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_years.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    term_type: Mapped[str] = mapped_column(String(30), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    academic_year: Mapped[AcademicYear] = relationship(back_populates="terms")
