"""Audit & operations (DATABASE_PLAN.md §M, Phase 1 tables)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import TenantBase, TimestampMixin, UUIDPKMixin


class AuditLog(UUIDPKMixin, TenantBase):
    """Written by the service layer (never scattered across endpoints) on
    every significant mutation — see app/services/audit.py."""

    __tablename__ = "audit_logs"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    previous_value_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    new_value_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Master_Architecture_Part1.md §44: curriculum/trimester context on an
    # audit row, so "everything that happened to this curriculum version" or
    # "...during this term" is a filtered query, not a cross-reference hunt.
    # `academic_terms` is institution-shared (the `None` translate-map key),
    # so a real FK is fine; `program_versions` is schema="program" and an
    # institution can have more than one program, so — same reasoning as
    # `StudentProfile.program_version_id`'s docstring in `identity.py` — a
    # real FK here would only ever be able to target one fixed program
    # schema. This stays a plain UUID, enforced at the application layer.
    academic_term_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("academic_terms.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    program_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )


class AuditLogSettings(UUIDPKMixin, TimestampMixin, TenantBase):
    """One row per tenant (created lazily on first `PATCH
    /audit/settings`, see app/api/v1/endpoints/audit.py) holding the
    archive-view retention window. `retention_days=None` means "never
    archive" — nothing is physically moved (see migration 0030's
    docstring), a log older than the window is just excluded from the
    default list view and can be brought back with `include_archived=true`.
    """

    __tablename__ = "audit_log_settings"

    retention_days: Mapped[int | None] = mapped_column(nullable=True)


class Notification(UUIDPKMixin, TenantBase):
    """Phase 1 table; automated triggers land in Phase 7+."""

    __tablename__ = "notifications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
