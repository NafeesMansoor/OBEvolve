"""Audit-trail UI: read-only listing over `audit_logs`
(app/models/tenant/audit.py, app/services/audit.py's `write_audit_log`,
already called across 15+ mutating endpoints)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.tenancy import get_db
from app.models.tenant.audit import AuditLog, AuditLogSettings
from app.models.tenant.identity import User
from app.schemas.audit import AuditLogRead, AuditLogSettingsRead, AuditLogSettingsUpdate
from app.services.rbac import require_permission

router = APIRouter()


def _get_settings(db: Session) -> AuditLogSettings | None:
    return db.query(AuditLogSettings).first()


@router.get("/settings", response_model=AuditLogSettingsRead)
def get_audit_log_settings(
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("audit.view")),
) -> AuditLogSettingsRead:
    settings = _get_settings(db)
    return AuditLogSettingsRead(retention_days=settings.retention_days if settings else None)


@router.patch("/settings", response_model=AuditLogSettingsRead)
def update_audit_log_settings(
    payload: AuditLogSettingsUpdate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("audit.manage")),
) -> AuditLogSettingsRead:
    settings = _get_settings(db)
    if settings is None:
        settings = AuditLogSettings(retention_days=payload.retention_days)
        db.add(settings)
    else:
        settings.retention_days = payload.retention_days
    db.flush()
    return AuditLogSettingsRead(retention_days=settings.retention_days)


@router.get("", response_model=list[AuditLogRead])
def list_audit_logs(
    entity_type: str | None = Query(default=None),
    entity_id: uuid.UUID | None = Query(default=None),
    user_id: uuid.UUID | None = Query(default=None),
    action: str | None = Query(default=None),
    date_from: datetime | None = Query(default=None),
    date_to: datetime | None = Query(default=None),
    include_archived: bool = Query(
        default=False,
        description=(
            "Archived = older than the retention_days window in "
            "audit_log_settings (view-only: nothing is physically moved). "
            "False (default) excludes them; true fetches them back."
        ),
    ),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("audit.view")),
) -> list[AuditLogRead]:
    query = db.query(AuditLog)
    if entity_type is not None:
        query = query.filter(AuditLog.entity_type == entity_type)
    if entity_id is not None:
        query = query.filter(AuditLog.entity_id == entity_id)
    if user_id is not None:
        query = query.filter(AuditLog.user_id == user_id)
    if action is not None:
        query = query.filter(AuditLog.action == action)
    if date_from is not None:
        query = query.filter(AuditLog.timestamp >= date_from)
    if date_to is not None:
        query = query.filter(AuditLog.timestamp <= date_to)

    if not include_archived:
        settings = _get_settings(db)
        if settings is not None and settings.retention_days is not None:
            cutoff = datetime.now(UTC) - timedelta(days=settings.retention_days)
            query = query.filter(AuditLog.timestamp >= cutoff)

    rows = query.order_by(AuditLog.timestamp.desc()).offset(offset).limit(limit).all()

    # Bulk-resolve actor display names in one query (same pattern as
    # academic_ops.py's faculty-name lookup) rather than a per-row join,
    # since a deleted user leaves `user_id` NULL (ON DELETE SET NULL) and
    # would otherwise need a LEFT JOIN just to still show the other columns.
    actor_ids = {row.user_id for row in rows if row.user_id is not None}
    actors_by_id: dict[uuid.UUID, User] = {}
    if actor_ids:
        actors_by_id = {u.id: u for u in db.query(User).filter(User.id.in_(actor_ids)).all()}

    return [
        AuditLogRead(
            id=row.id,
            timestamp=row.timestamp,
            actor=(
                f"{actor.full_name} ({actor.email})"
                if row.user_id is not None and (actor := actors_by_id.get(row.user_id))
                else None
            ),
            action=row.action,
            entity_type=row.entity_type,
            entity_id=row.entity_id,
            previous_value_json=row.previous_value_json,
            new_value_json=row.new_value_json,
        )
        for row in rows
    ]
