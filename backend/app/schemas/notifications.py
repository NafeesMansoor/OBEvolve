"""Schemas for the top-bar notifications panel (app/models/tenant/audit.py's
`Notification`) plus the synthesized pending-approvals summary
(app/api/v1/endpoints/notifications.py)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: str
    title: str
    body: str | None
    is_read: bool
    created_at: datetime


class UnreadCount(BaseModel):
    count: int


class ReadAllResult(BaseModel):
    updated: int


PendingApprovalType = Literal["assessment_document", "raw_data_change", "improvement_plan"]


class PendingApprovalItem(BaseModel):
    type: PendingApprovalType
    count: int
    label: str


class PendingApprovalsSummary(BaseModel):
    total: int
    items: list[PendingApprovalItem]
