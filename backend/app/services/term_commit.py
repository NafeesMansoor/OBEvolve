"""Final Commit: the one permanent, program-scoped lock on assessment/
marks/attainment writes for a term (see `app.models.tenant.term_commit.
TermCommit`'s docstring for the product framing).

Before a term is committed, a Course Teacher has *full* write access
regardless of any in-flight workflow status — this module is also where
that "full access" is actually implemented, not just where the final lock
lives:

- `revert_if_published` — editing a `PUBLISHED`/`ARCHIVED` assessment
  doesn't get blocked; it silently reverts the assessment to `APPROVED`
  first (an implicit "un-publish"), so a re-approval/re-publish is needed
  before students see it "live" again, but the edit itself is never
  refused. Called from `update_assessment` right before applying the patch.
- `reopen_grade_submission_if_submitted` — editing marks after
  `submit_final_grades` has already run doesn't get blocked either; it
  resets the section's `GradeSubmission` back to `"draft"` (an implicit
  "un-submit"), so a re-submission (which also regenerates that
  submission's `AttainmentSnapshot` rows — see `app.services.grades.
  submit_final_grades`) is needed to re-finalize, but the mark edit itself
  is never refused. Called from the marks-mutation endpoints instead of
  the old hard `_ensure_grades_not_submitted` block.

`ensure_term_not_committed` is the only thing that actually raises — call
it (after `ensure_assigned_to_section`/`ensure_section_access`, same
placement as those) from every one of these write paths.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.base import WorkflowStatus
from app.models.tenant.assessments.assessment import Assessment
from app.models.tenant.assessments.marks import GradeSubmission
from app.models.tenant.courses.delivery import CourseOffering, CourseSection
from app.models.tenant.org import AcademicTerm
from app.models.tenant.term_commit import TermCommit


def _resolve_academic_term(db: Session, course_section_id: uuid.UUID) -> AcademicTerm | None:
    return (
        db.query(AcademicTerm)
        .join(CourseOffering, CourseOffering.academic_term_id == AcademicTerm.id)
        .join(CourseSection, CourseSection.course_offering_id == CourseOffering.id)
        .filter(CourseSection.id == course_section_id)
        .one_or_none()
    )


def get_term_commit(db: Session, academic_term_id: uuid.UUID) -> TermCommit | None:
    return (
        db.query(TermCommit).filter(TermCommit.academic_term_id == academic_term_id).one_or_none()
    )


def is_committable(term: AcademicTerm, commit: TermCommit | None) -> bool:
    """Past the term's own end_date, or a Program Administrator has
    explicitly enabled early commit for it — see `TermCommit.manually_enabled`."""
    return date.today() >= term.end_date or bool(commit and commit.manually_enabled)


def ensure_term_not_committed(db: Session, course_section_id: uuid.UUID) -> None:
    """403s if this section's term has already been Final Committed in
    this program. A section whose offering has no resolvable term (or
    whose program has never touched Final Commit for that term at all) is
    never blocked by this — only an actual commit row with
    `is_committed=True` locks anything."""
    term = _resolve_academic_term(db, course_section_id)
    if term is None:
        return
    commit = get_term_commit(db, term.id)
    if commit is not None and commit.is_committed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"{term.name} has been finally committed — no further changes are allowed.",
        )


def set_early_enable(
    db: Session, academic_term_id: uuid.UUID, enabled: bool
) -> TermCommit:
    commit = get_term_commit(db, academic_term_id)
    if commit is None:
        commit = TermCommit(academic_term_id=academic_term_id)
        db.add(commit)
    commit.manually_enabled = enabled
    db.flush()
    return commit


def commit_term(db: Session, term: AcademicTerm, committed_by: uuid.UUID) -> TermCommit:
    commit = get_term_commit(db, term.id)
    if commit is not None and commit.is_committed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=f"{term.name} is already committed."
        )
    if not is_committable(term, commit):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"{term.name} hasn't ended yet — enable early commit first if you need to "
            "commit it now.",
        )
    if commit is None:
        commit = TermCommit(academic_term_id=term.id)
        db.add(commit)
    commit.is_committed = True
    commit.committed_by = committed_by
    commit.committed_at = datetime.now(UTC)
    db.flush()
    return commit


def revert_if_published(assessment: Assessment) -> bool:
    """Editing a PUBLISHED/ARCHIVED assessment un-publishes it back to
    APPROVED instead of being blocked. Returns True if it reverted
    anything (so the caller can mention it in the audit log)."""
    if assessment.status in (WorkflowStatus.PUBLISHED, WorkflowStatus.ARCHIVED):
        assessment.status = WorkflowStatus.APPROVED
        return True
    return False


def reopen_grade_submission_if_submitted(
    db: Session, course_section_id: uuid.UUID
) -> GradeSubmission | None:
    """Editing marks after final submission un-submits the section's
    `GradeSubmission` back to draft instead of being blocked. Returns the
    submission if it reopened one, else None (nothing to reopen)."""
    submission = (
        db.query(GradeSubmission)
        .filter(GradeSubmission.course_section_id == course_section_id)
        .one_or_none()
    )
    if submission is None or submission.status != "submitted":
        return None
    submission.status = "draft"
    submission.submitted_by = None
    submission.submitted_at = None
    db.add(submission)
    return submission
