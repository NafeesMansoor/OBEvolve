"""Assessment definition (DATABASE_PLAN.md §F — implemented).

Scope stops at *defining* assessment types/rubrics/questions/assessments —
recording student scores (`student_performance`, DATABASE_PLAN.md §G) is a
separate, later feature (marks entry/gradebook), not built here.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TenantBase, TimestampMixin, UUIDPKMixin, WorkflowStatus


class AssessmentType(UUIDPKMixin, TimestampMixin, TenantBase):
    """Seeded with a fixed default set (`app.seed.assessment_defaults`,
    `is_custom=False`); institutions may add their own (`is_custom=True`)."""

    __tablename__ = "assessment_types"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_custom: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Gates the question-paper/moderation-form/compliance-form/scripts upload
    # requirement (AssessmentDocument below) — a *type-level* flag rather
    # than name-matching "Midterm"/"Final Exam" strings, so it survives
    # renames and lets an institution opt a custom type in too. Seeded true
    # for Midterm/Final Exam by app.seed.assessment_defaults.
    requires_documents: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Gates the CEP-specific document set (problem definition, marked-rubric
    # sample, project reports). Seeded true only for "Complex Engineering
    # Problem" — same type-level-flag reasoning as requires_documents.
    requires_cep_documents: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class Rubric(UUIDPKMixin, TimestampMixin, TenantBase):
    __tablename__ = "rubrics"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_reusable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    criteria: Mapped[list[RubricCriterion]] = relationship(back_populates="rubric")


class RubricCriterion(UUIDPKMixin, TimestampMixin, TenantBase):
    __tablename__ = "rubric_criteria"

    rubric_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rubrics.id", ondelete="CASCADE"), nullable=False, index=True
    )
    criterion: Mapped[str] = mapped_column(Text, nullable=False)
    weight: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)

    rubric: Mapped[Rubric] = relationship(back_populates="criteria")
    levels: Mapped[list[RubricLevel]] = relationship(back_populates="rubric_criterion")


class RubricLevel(UUIDPKMixin, TimestampMixin, TenantBase):
    __tablename__ = "rubric_levels"

    rubric_criterion_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("rubric_criteria.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    rubric_criterion: Mapped[RubricCriterion] = relationship(back_populates="levels")


class Question(UUIDPKMixin, TimestampMixin, TenantBase):
    __tablename__ = "questions"

    course_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("course_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    text: Mapped[str] = mapped_column(Text, nullable=False)
    # Free string ("mcq"|"short_answer"|"essay"|"numerical"|...), not an enum —
    # mirrors Course.course_type's precedent for institution-varying labels.
    question_type: Mapped[str] = mapped_column(String(50), nullable=False)
    difficulty: Mapped[str | None] = mapped_column(String(50), nullable=True)
    marks: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    topic: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[WorkflowStatus] = mapped_column(
        String(20), nullable=False, default=WorkflowStatus.DRAFT
    )
    author_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )


class QuestionCourseOutcomeMapping(UUIDPKMixin, TimestampMixin, TenantBase):
    """Junction, no scale needed — a question either targets a CO or not."""

    __tablename__ = "question_co_mappings"

    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    course_outcome_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("course_outcomes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )


class QuestionBloomMapping(UUIDPKMixin, TimestampMixin, TenantBase):
    __tablename__ = "question_bloom_mappings"

    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    bloom_level_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bloom_levels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )


class Assessment(UUIDPKMixin, TimestampMixin, TenantBase):
    """schema="program": see docs/adr/0003-schema-per-program.md.
    `academic_term_id`/`assessment_type_id`/`rubric_id` point into the
    institution-shared schema (the `None` translate-map key) and need no
    schema= override, but `course_section_id` targets `course_sections` —
    also schema="program" — and needs the explicit `program.` prefix (see
    `app.models.tenant.obe.outcomes.PEO`'s docstring for why).
    """

    __tablename__ = "assessments"
    __table_args__ = {"schema": "program"}

    course_section_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("program.course_sections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    academic_term_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_terms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    assessment_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assessment_types.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    max_marks: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    weight: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    date: Mapped[date | None] = mapped_column(Date, nullable=True)
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rubric_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("rubrics.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[WorkflowStatus] = mapped_column(
        String(20), nullable=False, default=WorkflowStatus.DRAFT
    )
    # Document uploads (AssessmentDocument) are due by the academic term's
    # end_date unless a Program Administrator extends it here — the
    # effective deadline is `document_deadline_extended_to or
    # academic_term.end_date`, computed by callers (frontend already has
    # both values loaded), not stored redundantly.
    document_deadline_extended_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    document_deadline_extended_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    document_deadline_extended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    questions: Mapped[list[AssessmentQuestion]] = relationship(back_populates="assessment")


class AssessmentQuestion(UUIDPKMixin, TimestampMixin, TenantBase):
    """schema="program": see docs/adr/0003-schema-per-program.md.
    `question_id` points into the institution-shared schema (the `None`
    translate-map key) and needs no schema= override, but `assessment_id`
    targets `assessments` — also schema="program" — and needs the explicit
    `program.` prefix (see `app.models.tenant.obe.outcomes.PEO`'s docstring
    for why)."""

    __tablename__ = "assessment_questions"
    __table_args__ = {"schema": "program"}

    assessment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("program.assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    marks_allocated: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)

    assessment: Mapped[Assessment] = relationship(back_populates="questions")


class AssessmentDocument(UUIDPKMixin, TimestampMixin, TenantBase):
    """A supporting document an assessment needs before it's considered
    complete. Which `document_type`s are required (and how many) depends on
    `AssessmentType.requires_documents`/`requires_cep_documents` — see
    `app.api.v1.endpoints.assessment._REQUIRED_DOCUMENT_TYPES`, the single
    place that maps a type flag to its required `(document_type, min_count)`
    set. Two upload shapes coexist here, both in this one table:

    - **Singleton slots** (question_paper, moderation_form, compliance_form,
      script_highest, script_lowest, script_median, problem_definition):
      at most one row per (assessment_id, document_type) — re-uploading
      REPLACES the row in place and resets it to "pending" (no version
      history, deliberately, to keep this simple).
    - **Repeatable slots** (marked_rubric_sample, project_report): any
      number of rows per (assessment_id, document_type) are allowed —
      uploading always ADDS a new row; each is reviewed independently and
      deleted individually rather than replaced.

    There is deliberately no DB-level uniqueness constraint on
    (assessment_id, document_type) — the singleton/repeatable distinction is
    enforced in the upload endpoint, not the schema, since which behavior
    applies depends on `document_type`.

    `status` is a small purpose-built pending/approved/rejected flag — NOT
    `app.db.base.WorkflowStatus` — mirroring
    `app.models.tenant.raw_data.RawDataChangeRequest`'s precedent: a
    lightweight approval flag is a different shape than a multi-stage
    draft-to-published document lifecycle.

    schema="program": see docs/adr/0003-schema-per-program.md — lives
    alongside `assessments`.
    """

    __tablename__ = "assessment_documents"
    __table_args__ = {"schema": "program"}

    assessment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("program.assessments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # question_paper | moderation_form | compliance_form | script_highest |
    # script_lowest | script_median | problem_definition |
    # marked_rubric_sample | project_report
    document_type: Mapped[str] = mapped_column(String(30), nullable=False)
    file_key: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="pending")
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
