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
from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.tenant.org import AcademicTerm


def get_current_term_ids(db: Session) -> set[uuid.UUID]:
    """Every `AcademicTerm.id` currently marked `is_active=True`. A set, not
    a single id: the schema has no uniqueness constraint on `is_active` (an
    institution could transition terms with a brief overlap), so callers
    should treat all of them as "current" rather than assuming exactly one."""
    rows = db.query(AcademicTerm.id).filter(AcademicTerm.is_active.is_(True)).all()
    return {row[0] for row in rows}


def validate_calendar_order(
    *,
    start_date: date,
    add_drop_last_date: date | None,
    midterm_start_date: date | None,
    midterm_end_date: date | None,
    final_exam_start_date: date | None,
    final_exam_end_date: date | None,
    result_due_date: date | None,
    result_publication_date: date | None,
    end_date: date,
) -> None:
    """Enforces Master_Architecture_Part1.md §3's fixed chronological chain:
    Class Start -> Add/Drop -> Midterm Start -> Midterm End -> Final Start ->
    Final End -> Result Due -> Result Publication -> Term End.

    Only the milestones that have actually been set are checked, in strictly
    non-decreasing order against each other — a term is normally created
    before every date is known and filled in over the setup process, so a
    still-missing milestone is never treated as a violation (spec: "must
    validate that dates are logically consistent", not "must require every
    date up front").
    """
    sequence: list[tuple[str, date | None]] = [
        ("Class Start", start_date),
        ("Add/Drop Last Date", add_drop_last_date),
        ("Midterm Start", midterm_start_date),
        ("Midterm End", midterm_end_date),
        ("Final Exam Start", final_exam_start_date),
        ("Final Exam End", final_exam_end_date),
        ("Result Due Date", result_due_date),
        ("Result Publication Date", result_publication_date),
        ("Term End", end_date),
    ]
    known = [(label, d) for label, d in sequence if d is not None]
    for (prev_label, prev_date), (label, current_date) in zip(known, known[1:], strict=False):
        if current_date < prev_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"{label} ({current_date.isoformat()}) cannot be before "
                    f"{prev_label} ({prev_date.isoformat()})."
                ),
            )
