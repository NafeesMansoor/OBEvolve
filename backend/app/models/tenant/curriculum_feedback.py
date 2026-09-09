"""Program Coordinator feedback on Program & Curriculum Level items
(Master_Architecture_Part1.md §25-26).

Advisory only — a comment attached to a read-only item, never a direct
write. Contrast `app.models.tenant.change_requests.CourseChangeRequest`,
which does apply automatically on final approval; there is no equivalent
"apply" step here because Program Coordinator has no edit rights at this
level at all (spec §25), only View + Feedback.

`entity_type`/`entity_id` are a polymorphic, unconstrained target — same
shape as `RawDataChangeRequest.table_name`/`row_pk`
(`app.models.tenant.raw_data`) — since the commented-on item can live in
either the institution-shared schema (institutional mission/vision) or this
program's own schema (PEO/PO/PI/program mission/vision/mappings); a single
FK can't span both.

schema="program": Program Coordinator always operates within one program
context (`X-Program-Code`), regardless of which schema the target entity
itself lives in.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import TenantBase, TimestampMixin, UUIDPKMixin

STATUSES: tuple[str, ...] = ("open", "accepted", "ignored", "resolved")

ENTITY_TYPES: tuple[str, ...] = (
    "institutional_mission",
    "institutional_vision",
    "program_mission",
    "program_vision",
    "peo",
    "program_outcome",
    "performance_indicator",
    "knowledge_profile_mapping",
    "problem_attribute_mapping",
    "engineering_activity_mapping",
    "peo_vision_mapping",
    "curriculum_structure",
)


class CurriculumFeedback(UUIDPKMixin, TimestampMixin, TenantBase):
    __tablename__ = "curriculum_feedback"
    __table_args__ = {"schema": "program"}

    entity_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")
    submitted_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
