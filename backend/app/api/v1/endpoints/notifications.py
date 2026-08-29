"""Top-bar notifications panel: the user's own `notifications` rows, plus a
synthesized "what's pending your review" summary
(`GET /pending-approvals`) — nothing writes real `notifications` rows yet
(that lands in a later phase, see app/models/tenant/audit.py's
`Notification` docstring), so the pending-approvals summary is computed
live from the same tables the real "pending review" endpoints already
query, not read back from `notifications`.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.tenancy import get_db
from app.models.tenant.assessments.assessment import Assessment, AssessmentDocument
from app.models.tenant.audit import Notification
from app.models.tenant.identity import User
from app.models.tenant.obe.improvement import ImprovementPlan
from app.models.tenant.org import Program
from app.models.tenant.raw_data import RawDataChangeRequest
from app.schemas.notifications import (
    NotificationRead,
    PendingApprovalItem,
    PendingApprovalsSummary,
    ReadAllResult,
    UnreadCount,
)
from app.services.rbac import (
    get_current_user,
    get_program_context,
    get_program_scoped_db,
    get_user_permission_grants,
    grants_satisfy_permission,
)

router = APIRouter()


@router.get("", response_model=list[NotificationRead])
def list_notifications(
    unread_only: bool = Query(default=False),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Notification]:
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    if unread_only:
        query = query.filter(Notification.is_read.is_(False))
    return query.order_by(Notification.created_at.desc()).offset(offset).limit(limit).all()


@router.get("/unread-count", response_model=UnreadCount)
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UnreadCount:
    count = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id, Notification.is_read.is_(False))
        .count()
    )
    return UnreadCount(count=count)


@router.post("/{notification_id}/read", response_model=NotificationRead)
def mark_notification_read(
    notification_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Notification:
    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == current_user.id)
        .one_or_none()
    )
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    notification.is_read = True
    db.flush()
    return notification


@router.post("/read-all", response_model=ReadAllResult)
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReadAllResult:
    unread = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id, Notification.is_read.is_(False))
        .all()
    )
    for notification in unread:
        notification.is_read = True
    db.flush()
    return ReadAllResult(updated=len(unread))


# --- Synthesized "pending your review" summary ------------------------------


def _programs_administered_for_raw_data(
    grants: list[tuple[str, str | None, uuid.UUID | None]],
) -> set[uuid.UUID]:
    """Mirrors `raw_data.py`'s `_programs_administered` — the set of
    programs this user holds a scoped `raw_data.approve` grant for."""
    return {
        scope_id
        for code, scope_type, scope_id in grants
        if code == "raw_data.approve" and scope_type == "program" and scope_id is not None
    }


@router.get("/pending-approvals", response_model=PendingApprovalsSummary)
def get_pending_approvals(
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(get_current_user),
    program: Program = Depends(get_program_context),
) -> PendingApprovalsSummary:
    """Badge + dropdown summary for the top bar — aggregates counts across
    everything the current user actually has review authority over right
    now, reusing the same query shape as each category's real "pending"
    endpoint (assessment.py's `list_pending_assessment_documents`,
    raw_data.py's `list_pending_changes`, improvement.py's
    `status="proposed"` filter) but scoped to this one user's own grants
    instead of returning full rows.

    Bound to the currently-active program (`X-Program-Code`, same as every
    other program-scoped endpoint) since two of the three categories
    (assessment documents, improvement plans) are program-schema tables —
    a user with no grant on *any* program can't reach this at all, but that
    matches every other program-scoped endpoint in this app. `program` is
    the same request-cached dependency `get_program_scoped_db` itself
    depends on, resolved here only to know which program id to check
    scoped `assessment.approve` grants against.
    """
    grants = get_user_permission_grants(db, current_user.id)
    items: list[PendingApprovalItem] = []

    can_review_assessment_docs = grants_satisfy_permission(
        grants, "assessment.approve", scope_type="program", scope_id=program.id
    )
    if can_review_assessment_docs:
        pending_docs = (
            db.query(AssessmentDocument)
            .join(Assessment, AssessmentDocument.assessment_id == Assessment.id)
            .filter(AssessmentDocument.status == "pending")
            .count()
        )
        if pending_docs:
            items.append(
                PendingApprovalItem(
                    type="assessment_document",
                    count=pending_docs,
                    label="Assessment documents pending review",
                )
            )

    raw_data_program_ids = _programs_administered_for_raw_data(grants)
    if raw_data_program_ids:
        pending_changes = (
            db.query(RawDataChangeRequest)
            .filter(
                RawDataChangeRequest.scope_type == "program",
                RawDataChangeRequest.scope_id.in_(raw_data_program_ids),
                RawDataChangeRequest.status == "pending",
            )
            .count()
        )
        if pending_changes:
            items.append(
                PendingApprovalItem(
                    type="raw_data_change",
                    count=pending_changes,
                    label="Raw-data changes pending approval",
                )
            )

    if can_review_assessment_docs:
        pending_plans = (
            db.query(ImprovementPlan).filter(ImprovementPlan.status == "proposed").count()
        )
        if pending_plans:
            items.append(
                PendingApprovalItem(
                    type="improvement_plan",
                    count=pending_plans,
                    label="Improvement plans pending review",
                )
            )

    return PendingApprovalsSummary(total=sum(item.count for item in items), items=items)
