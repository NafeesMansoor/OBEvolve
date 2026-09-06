"""Final Commit: once a program commits an academic term, every assessment/
marks/attainment write for that term in this program is permanently locked
— a one-way action, never reversible (a mistake found after commit needs a
separate, explicitly-audited exception process later; this repo doesn't
build that yet). Before commit, a Course Teacher has full write access to
assessments and marks regardless of `WorkflowStatus`/`GradeSubmission`
status — editing a published assessment or already-submitted marks just
reverts that one row's status rather than being blocked (see
`app.services.term_commit`'s docstring for the exact mechanics) — Final
Commit is the *only* hard, permanent gate.

schema="program": one term can be committed independently per program
(the spec calls for "after the semester ends, admin commits" — read as
"the program's own admin commits their own program's data," not one
cross-program action) — see docs/course_level_settings_and_approval_workflow.md's
follow-up discussion. `academic_term_id` points into the institution-shared
schema (the `None` translate-map key) and needs no schema= override — same
pattern as `app.models.tenant.courses.delivery.CourseOffering.academic_term_id`.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import TenantBase, TimestampMixin, UUIDPKMixin


class TermCommit(UUIDPKMixin, TimestampMixin, TenantBase):
    __tablename__ = "term_commits"
    __table_args__ = {"schema": "program"}

    academic_term_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_terms.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    is_committed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Lets a Program Administrator allow commit before the term's own
    # end_date has passed ("or the admin sets it enable" — spec request).
    # Without this, `is_committable` only turns true once the term has
    # actually ended.
    manually_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    committed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    committed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
