"""CO-failure -> continuous-improvement workflow (spec §5): when a CO
misses its course-level attainment threshold, a faculty/coordinator can
record an improvement/action plan for it. No automatic background flagging
job — the attainment report already marks a CO `is_attained=False` on every
view, and the frontend offers "create a plan" right there; a plan is a
record of intent/response, not a queue that needs to be drained.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import TenantBase, TimestampMixin, UUIDPKMixin


class ImprovementPlan(UUIDPKMixin, TimestampMixin, TenantBase):
    """One improvement/action plan against one CO, in the context of one
    course section (spec §5's "problem/observation, proposed action,
    reason, expected improvement, implementation semester, responsible
    person, status, evidence").

    `status` is a small plan-specific lifecycle ("proposed" -> "approved" |
    "rejected" -> "implemented"), deliberately NOT `app.db.base.WorkflowStatus`
    (draft/submitted/reviewed/approved/published/archived) — that shape fits
    a document being drafted and published, not a propose/approve/implement
    action-tracking flow; reusing it here would force meaningless states.

    schema="program": see docs/adr/0003-schema-per-program.md.
    `course_section_id` targets `course_sections` — also schema="program" —
    and needs the explicit `program.` prefix (see
    `app.models.tenant.obe.outcomes.PEO`'s docstring for why).
    `course_outcome_id`/`implementation_term_id`/`created_by`/
    `responsible_user_id`/`reviewed_by` point into the institution-shared
    schema (the `None` translate-map key) and need no schema= override.
    """

    __tablename__ = "improvement_plans"
    __table_args__ = {"schema": "program"}

    course_section_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("program.course_sections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    course_outcome_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("course_outcomes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    problem_observation: Mapped[str] = mapped_column(Text, nullable=False)
    proposed_action: Mapped[str] = mapped_column(String(50), nullable=False)
    proposed_action_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    expected_improvement: Mapped[str] = mapped_column(Text, nullable=False)
    implementation_term_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("academic_terms.id", ondelete="SET NULL"), nullable=True
    )
    responsible_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="proposed")
    evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
