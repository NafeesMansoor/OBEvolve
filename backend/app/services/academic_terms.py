"""Current-semester resolution
(docs/course_level_settings_and_approval_workflow.md §8/§9): the one place
that decides what "current" means for course-selection list endpoints,
driven by `AcademicTerm.is_active` rather than hardcoded dates or names
(spec §11's explicit requirement) — the same flag
`app.services.faculty_scope.ensure_current_term` already gates writes on,
just resolved here as an id set for use as a list-endpoint query filter
rather than a per-section boolean check.
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.tenant.org import AcademicTerm


def get_current_term_ids(db: Session) -> set[uuid.UUID]:
    """Every `AcademicTerm.id` currently marked `is_active=True`. A set, not
    a single id: the schema has no uniqueness constraint on `is_active` (an
    institution could transition terms with a brief overlap), so callers
    should treat all of them as "current" rather than assuming exactly one."""
    rows = db.query(AcademicTerm.id).filter(AcademicTerm.is_active.is_(True)).all()
    return {row[0] for row in rows}
