"""Final Commit endpoints — see `app.models.tenant.term_commit.TermCommit`
and `app.services.term_commit` for the design. Program-scoped: a term is
committed independently per program."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.middleware.audit import get_request_context
from app.models.tenant.identity import User
from app.models.tenant.org import AcademicTerm
from app.models.tenant.term_commit import TermCommit
from app.schemas.term_commit import EnableEarlyCommitUpdate, TermCommitStatusRead
from app.services.audit import write_audit_log
from app.services.rbac import get_program_scoped_db, require_permission
from app.services.term_commit import commit_term, get_term_commit, is_committable, set_early_enable

router = APIRouter()


def _status_read(term: AcademicTerm, commit: TermCommit | None) -> TermCommitStatusRead:
    return TermCommitStatusRead(
        academic_term_id=term.id,
        term_name=term.name,
        term_end_date=term.end_date.isoformat(),
        is_committed=bool(commit and commit.is_committed),
        manually_enabled=bool(commit and commit.manually_enabled),
        committable=is_committable(term, commit),
        committed_by=commit.committed_by if commit else None,
        committed_at=commit.committed_at if commit else None,
    )


@router.get("/{academic_term_id}", response_model=TermCommitStatusRead)
def get_term_commit_status(
    academic_term_id: uuid.UUID,
    db: Session = Depends(get_program_scoped_db),
    _current_user: User = Depends(require_permission("section.view", scope_type="program")),
) -> TermCommitStatusRead:
    term = db.get(AcademicTerm, academic_term_id)
    if term is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Academic term not found")
    commit = get_term_commit(db, academic_term_id)
    return _status_read(term, commit)


@router.post("/{academic_term_id}/enable-early", response_model=TermCommitStatusRead)
def enable_early_commit(
    academic_term_id: uuid.UUID,
    payload: EnableEarlyCommitUpdate,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("term_commit.manage", scope_type="program")),
) -> TermCommitStatusRead:
    term = db.get(AcademicTerm, academic_term_id)
    if term is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Academic term not found")
    commit = set_early_enable(db, academic_term_id, payload.enabled)
    write_audit_log(
        db,
        user_id=current_user.id,
        action="term_commit.early_enable_changed",
        entity_type="TermCommit",
        entity_id=commit.id,
        new_value={"academic_term_id": str(academic_term_id), "enabled": payload.enabled},
        **get_request_context(request),
    )
    return _status_read(term, commit)


@router.post("/{academic_term_id}/commit", response_model=TermCommitStatusRead)
def commit_academic_term(
    academic_term_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("term_commit.manage", scope_type="program")),
) -> TermCommitStatusRead:
    term = db.get(AcademicTerm, academic_term_id)
    if term is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Academic term not found")
    commit = commit_term(db, term, current_user.id)
    write_audit_log(
        db,
        user_id=current_user.id,
        action="term_commit.committed",
        entity_type="TermCommit",
        entity_id=commit.id,
        new_value={"academic_term_id": str(academic_term_id)},
        **get_request_context(request),
    )
    return _status_read(term, commit)
