"""Pending change requests from the raw-data console's restricted tier
(Program Coordinator — `raw_data.propose_scoped`, see
app/services/raw_data.py and app/api/v1/endpoints/raw_data.py).

A row here is a *proposal*, not an applied change: `payload_json` is what
the requester wants to insert/update/delete, `previous_json` is a snapshot
of the row's prior state (for update/delete, so a reviewer can see the
diff), and nothing in the target table actually changes until a Program
Administrator approves it (see the `approve` endpoint, which applies the
staged operation for real).

`scope_type`/`scope_id` are resolved and stored at creation time (not
re-derived later) so `GET /raw-data/pending-changes` can filter to "requests
in programs I administer" with a plain equality check.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import TenantBase, TimestampMixin, UUIDPKMixin


class RawDataChangeRequest(UUIDPKMixin, TimestampMixin, TenantBase):
    __tablename__ = "raw_data_change_requests"

    requested_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    table_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    operation: Mapped[str] = mapped_column(String(10), nullable=False)  # insert|update|delete
    row_pk: Mapped[str | None] = mapped_column(String(100), nullable=True)  # null for insert
    payload_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    previous_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(10), nullable=False, default="pending")
    scope_type: Mapped[str] = mapped_column(String(20), nullable=False)
    scope_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<RawDataChangeRequest {self.table_name}:{self.operation} {self.status}>"
