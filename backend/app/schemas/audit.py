"""Schemas for the audit-trail UI (app/api/v1/endpoints/audit.py,
app/models/tenant/audit.py's `AuditLog`)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AuditLogRead(BaseModel):
    id: uuid.UUID
    timestamp: datetime
    # A single display string ("Full Name (email@domain)"), not a nested
    # actor object — matches frontend/src/features/audit/types.ts's
    # `actor: string | null`, already written against this endpoint. `None`
    # when the row's `user_id` is NULL (actor account deleted since,
    # `ON DELETE SET NULL` on `audit_logs.user_id`).
    actor: str | None
    action: str
    entity_type: str
    entity_id: uuid.UUID | None
    previous_value_json: dict[str, Any] | None
    new_value_json: dict[str, Any] | None
