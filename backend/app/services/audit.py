"""`write_audit_log()` — called explicitly by service functions that mutate
tenant data (DATABASE_PLAN.md §M, ARCHITECTURE.md §4).

Deliberately not wired as blanket HTTP middleware: only the service layer
knows what actually changed (previous vs. new value), so it is the layer
responsible for writing the row. See `app.middleware.audit` for the request
metadata helper this is usually called alongside.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.models.tenant.audit import AuditLog


def write_audit_log(
    db: Session,
    *,
    user_id: uuid.UUID | None,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID | None,
    previous_value: dict[str, Any] | None = None,
    new_value: dict[str, Any] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> AuditLog:
    """Create (and flush) an `audit_logs` row in the caller's session/transaction.

    Does not commit — it is meant to run inside the same transaction as the
    mutation it is recording, so a failure after this call rolls the audit
    row back too (no orphaned "audit says X happened" when X didn't commit).
    """
    entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        previous_value_json=previous_value,
        new_value_json=new_value,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(entry)
    db.flush()
    return entry
