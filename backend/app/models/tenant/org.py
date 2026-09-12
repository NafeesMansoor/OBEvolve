"""Organizational structure & academic calendar (DATABASE_PLAN.md §A).

`institutions → campuses → schools → departments → programs → program_versions`,
plus `academic_years → academic_terms`.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
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
    # Ordered session/term names for this program (e.g. ["Fall", "Spring",
    # "Summer"] or ["Semester 1", "Semester 2"]) — see migration 0029.
    # Informational: not an FK-enforced source for AcademicTerm.term_type,
    # which stays institution-wide free text (see that column's docstring).
    session_names: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)

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
    # spec §23: distinct from `approved_by`/`status` — a version can be
    # published, unpublished back to draft, edited, and republished multiple
    # times, and each of those events needs its own actor/timestamp rather
    # than overwriting a single pair of columns. The append-only history of
    # every such transition already exists for free in `audit_logs`
    # (`entity_type="ProgramVersion"`, tagged via `program_version_id` below)
    # — these four columns are just the "current state" snapshot for
    # cheap reads (spec §24's "Published by/date") without a join.
    published_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    unpublished_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    unpublished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # spec §24: "Previous version" lineage (e.g. 2024 supersedes 2022) — a
    # plain self-FK, not a separate history table, since this is one fact
    # about the version itself, not a log of events. schema="program":
    # same-marker-schema self-reference, so it needs the explicit `program.`
    # prefix (see `PEO`'s docstring in `obe/outcomes.py` for why).
    previous_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("program.program_versions.id", ondelete="SET NULL"),
        nullable=True,
    )
    # spec §12/§13/§18: PO definition method and numbering conventions are
    # curriculum-level configuration, not hard-coded. "direct" | "indicator_based"
    # drives which mapping/course-level UI and API paths are valid (spec §21) —
    # defaulted to "direct"/"numeric" so every pre-existing curriculum (seeded
    # before this column existed) keeps behaving exactly as it does today.
    po_definition_method: Mapped[str] = mapped_column(
        String(20), nullable=False, default="direct", server_default="direct"
    )
    peo_numbering_style: Mapped[str] = mapped_column(
        String(20), nullable=False, default="numeric", server_default="numeric"
    )
    po_numbering_style: Mapped[str] = mapped_column(
        String(20), nullable=False, default="numeric", server_default="numeric"
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
    # spec §3: the full academic calendar, not just start/end. Each is
    # independently nullable — a term is typically created before every
    # milestone date is known, and filled in over time — with the
    # chronological-order rule (class start -> add/drop -> midterm start ->
    # midterm end -> final start -> final end -> result due -> result
    # publication -> term end) enforced in the service layer
    # (`app.services.academic_terms.validate_calendar_order`), not a DB
    # constraint, so a partially-filled-in term is never rejected outright.
    add_drop_last_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    midterm_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    midterm_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    final_exam_start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    final_exam_end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    result_due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    result_publication_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    academic_year: Mapped[AcademicYear] = relationship(back_populates="terms")


class TermEffectiveCurriculum(UUIDPKMixin, TimestampMixin, TenantBase):
    """One effective curriculum for one trimester (spec §4) — a term may have
    several rows here when different cohorts follow different curriculum
    versions during the same trimester. Deliberately a join table, not a
    single `program_version_id` column on `AcademicTerm` (which is
    institution-shared and can't hold a program-specific FK anyway) or on
    `ProgramVersion` (one curriculum can be effective for more than one
    term over its life).

    schema="program": `program_version_id` targets `program_versions`, also
    schema="program", and needs the explicit prefix; `academic_term_id`
    points into the institution-shared schema (the `None` translate-map key)
    and needs no override — see `PEO`'s docstring in `obe/outcomes.py`.
    """

    __tablename__ = "term_effective_curricula"
    __table_args__ = (
        UniqueConstraint(
            "academic_term_id", "program_version_id", name="uq_term_effective_curricula"
        ),
        {"schema": "program"},
    )

    academic_term_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_terms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    program_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("program.program_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )


class Cohort(UUIDPKMixin, TimestampMixin, TenantBase):
    """A student intake/batch (spec §5) — the assigned curriculum
    (`program_version_id`) is meant to stay fixed for the cohort's whole
    academic lifecycle; changing it is a separate, explicitly-audited action
    (`POST /cohorts/{id}/change-curriculum`), never a plain field on the
    general update endpoint (spec: "should not be a routine operation").

    schema="program": see `PEO`'s docstring in `obe/outcomes.py`.
    """

    __tablename__ = "cohorts"
    __table_args__ = {"schema": "program"}

    code: Mapped[str] = mapped_column(String(50), nullable=False)
    intake_term_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_terms.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    intake_year: Mapped[int] = mapped_column(nullable=False)
    program_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("program.program_versions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
