"""Course Settings modification requests (Faculty Module spec §4.2; extended
by the Course-Level Settings and Approval Workflow spec, docs/
course_level_settings_and_approval_workflow.md): a faculty member proposes a
change to admin-controlled course information instead of editing it
directly.

`section_key` (one of `app.models.tenant.course_type_config.SECTION_KEYS`)
decides two things per docs/course_level_settings_and_approval_workflow.md
§5: how many approval stages the request needs (`overview`/`students` are
single-stage — a Course Administrator finalizes; `settings`/`assessments`
are two-stage — a Program Coordinator must also sign off), and, on final
approval, which `app.services.course_type_config.SECTION_APPLIERS` handler
actually writes the change into the real target data (`apply_status`
records whether that write happened/failed — approval and application are
two different events, see that module's docstring for why).

Unlike this model's original shape (single pending/approved/rejected flip,
never auto-applying because several target fields are relational sets that
can't be safely JSON-patched blindly), an approved request now **does**
apply automatically via a per-section handler that knows how to write its
own shape safely. `proposed_value_json` is the teacher's original ask and is
never mutated after submission; `edited_value_json` is what an approver
changed it to before accepting (spec §6's three-way Original/Proposed/
Modified audit trail) — the applier uses `edited_value_json` when present,
else `proposed_value_json`.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import TenantBase, TimestampMixin, UUIDPKMixin

# draft is unreachable today (submission is a single create-and-submit
# action, mirroring every other create endpoint in this codebase) — kept as
# a valid value for forward compatibility with spec §7's status list, not
# because anything sets it yet.
STATUSES: tuple[str, ...] = (
    "draft",
    "pending_admin",
    "pending_program_coordinator",
    "approved",
    "rejected",
    "returned",
)


class CourseChangeRequest(UUIDPKMixin, TimestampMixin, TenantBase):
    """schema="program": see docs/adr/0003-schema-per-program.md —
    `course_section_id` targets `course_sections`, also schema="program",
    and needs the explicit `program.` prefix.
    """

    __tablename__ = "course_change_requests"
    __table_args__ = {"schema": "program"}

    course_section_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("program.course_sections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # overview | settings | students | assessments — see SECTION_KEYS.
    section_key: Mapped[str] = mapped_column(String(20), nullable=False, default="settings")
    # Fine-grained label within the section, e.g. "description" | "outcomes"
    # | "tla_mapping" | "learning_materials" | "weights" | "grading_policy"
    # (settings), "enrollment_add" | "enrollment_drop" | "enrollment_status"
    # (students), "assessment_details" (assessments), "description" |
    # "objectives" (overview). Display-only + selects the apply sub-handler;
    # `section_key` alone drives gating/tier.
    target_field: Mapped[str] = mapped_column(String(30), nullable=False)
    current_value_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    proposed_value_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending_admin")
    requested_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # Stage 1 (Course Administrator / Course Coordinator).
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Stage 2 (Program Coordinator) — only set for two-stage sections.
    program_coordinator_reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    program_coordinator_review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    program_coordinator_reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    # Set by whichever stage edited the proposal before accepting it (spec
    # §6). Distinct from `proposed_value_json`, which never changes after
    # submission.
    edited_value_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    edited_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    edited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Whether the final-approval write into the real target data succeeded —
    # see this module's docstring. Null until a terminal "approved" status.
    apply_status: Mapped[str | None] = mapped_column(String(10), nullable=True)
    apply_error: Mapped[str | None] = mapped_column(Text, nullable=True)
