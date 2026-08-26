"""Assessment definition (DATABASE_PLAN.md §F — implemented).

Scope stops at *defining* assessment types/rubrics/questions/assessments —
recording student scores (`student_performance`, DATABASE_PLAN.md §G) is a
separate, later feature (marks entry/gradebook), not built here.
"""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Boolean, Date, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import TenantBase, TimestampMixin, UUIDPKMixin, WorkflowStatus


class AssessmentType(UUIDPKMixin, TimestampMixin, TenantBase):
    """Seeded with a fixed default set (`app.seed.assessment_defaults`,
    `is_custom=False`); institutions may add their own (`is_custom=True`)."""

    __tablename__ = "assessment_types"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    is_custom: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


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
    __tablename__ = "assessments"

    course_section_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("course_sections.id", ondelete="CASCADE"),
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

    questions: Mapped[list[AssessmentQuestion]] = relationship(back_populates="assessment")


class AssessmentQuestion(UUIDPKMixin, TimestampMixin, TenantBase):
    __tablename__ = "assessment_questions"

    assessment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assessments.id", ondelete="CASCADE"),
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
