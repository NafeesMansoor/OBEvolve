"""Marks entry + attainment configuration (DATABASE_PLAN.md §G/§H sketch a
much larger multi-methodology accreditation engine — immutable calculation
runs, indirect/direct weighting, PO/PSO/PEO cascades. This is the smaller,
concrete version actually requested: enter a student's marks per assessment
question, configure thresholds, and calculate CO/PO attainment on demand
(app.services.attainment) — no stored "run" history yet. Revisit against the
fuller §H design if/when indirect methods, multi-methodology comparison, or
PEO-level cascading attainment are actually needed.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import TenantBase, TimestampMixin, UUIDPKMixin


class StudentMark(UUIDPKMixin, TenantBase):
    """One student's marks on one assessment question. No `TimestampMixin`
    `updated_at` churn tracking beyond `entered_at`/`entered_by` — a
    correction overwrites `marks_obtained` in place (unlike
    DATABASE_PLAN.md §G's immutable-with-attempt-number design) since there
    is no accreditation-evidence audit requirement driving this pass; if
    that requirement shows up later, add attempt_number then rather than
    guessing at its shape now.

    schema="program": see docs/adr/0003-schema-per-program.md. Both FKs
    target other schema="program" tables and need the explicit `program.`
    prefix (see `app.models.tenant.obe.outcomes.PEO`'s docstring for why).
    """

    __tablename__ = "student_marks"
    __table_args__ = (
        UniqueConstraint(
            "assessment_question_id",
            "student_enrollment_id",
            name="uq_student_marks_question_enrollment",
        ),
        {"schema": "program"},
    )

    assessment_question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("program.assessment_questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_enrollment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("program.student_enrollments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    marks_obtained: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    entered_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    entered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class CourseAttainmentConfig(UUIDPKMixin, TimestampMixin, TenantBase):
    """The thresholds the spec asked for, one row per course version:
    `min_marks_percent` — a student must score at least this % of a CO's
    mapped-question marks to be counted as having attained that CO;
    `min_students_percent` — a CO itself counts as attained only if at
    least this % of *eligible* students attained it; `wi_treatment` —
    whether Withdrawn/Incomplete-enrolled students are excluded from both
    the numerator and denominator (`"exclude"`, the default) or treated
    like any other student (`"include"`) — see
    app.services.attainment.calculate_course_attainment. Spec §4 also
    allows a third "partially include... according to a configurable rule"
    option; that rule's shape isn't specified, so it's left unbuilt rather
    than guessed at — only the two concrete options are implemented.
    Institution-shared like GradingPolicy (course_versions lives there
    too), not per-program — see that model's docstring for why a real
    per-program FK would be unsound the moment a second program exists.
    """

    __tablename__ = "course_attainment_configs"

    course_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("course_versions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    min_marks_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=60)
    min_students_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=60)
    wi_treatment: Mapped[str] = mapped_column(String(20), nullable=False, default="exclude")


class ProgramAttainmentConfig(UUIDPKMixin, TimestampMixin, TenantBase):
    """One threshold, one row per program version: a PO counts as attained
    only if its computed attainment % (see
    app.services.attainment.calculate_program_attainment) is at least
    `min_po_attainment_percent`.

    schema="program", unlike `CourseAttainmentConfig` above: that one is
    institution-shared because it references `course_versions`, which stays
    institution-shared even once >1 program exists. This config instead
    references `program_versions`, which already lives in the per-program
    schema — so a real FK here is architecturally sound (no
    one-FK-can-only-target-one-schema problem to route around), and this
    table belongs alongside PEO/ProgramOutcome rather than next to
    GradingPolicy's institution-shared precedent.
    """

    __tablename__ = "program_attainment_configs"
    __table_args__ = {"schema": "program"}

    program_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("program.program_versions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    min_po_attainment_percent: Mapped[Decimal] = mapped_column(
        Numeric(5, 2), nullable=False, default=60
    )


class GradeSubmission(UUIDPKMixin, TimestampMixin, TenantBase):
    """One row per `CourseSection`, created the first time a faculty member
    saves that section's grade sheet (Faculty Module spec §21-23). `status`
    flips from "draft" to "submitted" via a dedicated endpoint, never a
    generic PATCH (mirrors `WorkflowStatus`'s dedicated-`/advance`
    convention, but this is a plain two-state flag — not
    `app.db.base.WorkflowStatus` — since there's no multi-stage
    draft→review→publish lifecycle here, just "can still edit" vs "locked",
    matching `AssessmentDocument`/`RawDataChangeRequest`'s precedent for a
    lightweight status that isn't the shared 6-stage one). Once "submitted",
    `bulk_upsert_student_marks` and any grade edit for this section's
    assessments must be rejected (BR-10) — enforced by callers checking this
    row's status, not a DB trigger.

    schema="program": see docs/adr/0003-schema-per-program.md.
    """

    __tablename__ = "grade_submissions"
    __table_args__ = {"schema": "program"}

    course_section_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("program.course_sections.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="draft")
    submitted_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AttainmentSnapshot(UUIDPKMixin, TenantBase):
    """A persisted CO/PO attainment result, captured at the moment a
    `GradeSubmission` is finalized (Faculty Module spec §24: attainment must
    be "stored... as a historical record" and "reproducible from the stored
    assessment and mapping data", not only ever computed on demand). Written
    by calling the existing `app.services.attainment` calculation functions
    unchanged and persisting their output here — this table adds storage,
    not new calculation logic. Exactly one of `course_outcome_id`/
    `program_outcome_id` is set per row, per `scope`.

    No `TimestampMixin` `updated_at` — a snapshot is immutable once written;
    a re-submission creates a new `GradeSubmission` (and thus new snapshot
    rows), it doesn't mutate an old one.

    schema="program": see docs/adr/0003-schema-per-program.md.
    """

    __tablename__ = "attainment_snapshots"
    __table_args__ = {"schema": "program"}

    grade_submission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("program.grade_submissions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    scope: Mapped[str] = mapped_column(String(2), nullable=False)  # "co" | "po"
    course_outcome_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("course_outcomes.id", ondelete="CASCADE"), nullable=True
    )
    program_outcome_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("program.program_outcomes.id", ondelete="CASCADE"),
        nullable=True,
    )
    attainment_percent: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    student_count: Mapped[int] = mapped_column(Integer, nullable=False)
    computed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
