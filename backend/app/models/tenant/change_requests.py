"""Course Settings modification requests (Faculty Module spec §4.2): a
faculty member proposes a change to admin-controlled course information
(description, outcomes, TLA mapping, learning materials, assessment
weights, grading policy) instead of editing it directly. Shape mirrors
`app.models.tenant.raw_data.RawDataChangeRequest` (pending/approved/rejected,
current/proposed JSON snapshots, reviewer audit fields) but approving one
does **not** auto-apply the change — several target fields (Course
Outcomes, TLA mapping) are relational sets, not scalar columns, so a
generic JSON-patch-apply would be unsafe; a Coordinator makes the real edit
through the existing admin Course Settings UI, with the approved request
serving as the audited justification.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import TenantBase, TimestampMixin, UUIDPKMixin


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
    # description | outcomes | tla_mapping | learning_materials | weights | grading_policy
    target_field: Mapped[str] = mapped_column(String(30), nullable=False)
    current_value_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    proposed_value_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="pending")
    requested_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
