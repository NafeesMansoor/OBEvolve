"""Schemas for Final Commit (app.services.term_commit)."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel


class TermCommitStatusRead(BaseModel):
    academic_term_id: uuid.UUID
    term_name: str
    term_end_date: str
    is_committed: bool
    manually_enabled: bool
    committable: bool
    committed_by: uuid.UUID | None
    committed_at: datetime | None


class EnableEarlyCommitUpdate(BaseModel):
    enabled: bool
