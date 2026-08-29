"""Lightweight cross-entity global search, scoped to the currently-active
program (same `X-Program-Code` resolution every other program-scoped
endpoint uses — see `get_program_scoped_db`) since most of what's searched
here (POs, COs, assessments) only exists inside one program's schema.

Each entity type is only searched if the current user actually holds the
same permission its real listing endpoint requires (matching the
`pending-approvals` principle in notifications.py) — a user with none of
these grants gets `{"results": []}`, not a 403.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.tenant.assessments.assessment import Assessment
from app.models.tenant.courses.catalog import Course
from app.models.tenant.identity import FacultyProfile, StudentProfile, User
from app.models.tenant.obe.outcomes import CourseOutcome, ProgramOutcome
from app.models.tenant.org import Program
from app.schemas.search import SearchResponse, SearchResultItem
from app.services.rbac import (
    get_current_user,
    get_program_context,
    get_program_scoped_db,
    get_user_permission_grants,
    grants_satisfy_permission,
)

router = APIRouter()

_PER_TYPE_LIMIT = 5
_TOTAL_LIMIT = 30


@router.get("", response_model=SearchResponse)
def global_search(
    q: str = Query(...),
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(get_current_user),
    program: Program = Depends(get_program_context),
) -> SearchResponse:
    if len(q) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Search query must be at least 2 characters",
        )
    term = f"%{q}%"
    grants = get_user_permission_grants(db, current_user.id)
    results: list[SearchResultItem] = []

    def can(code: str, *, scope_type: str | None = None) -> bool:
        scope_id = program.id if scope_type == "program" else None
        return grants_satisfy_permission(grants, code, scope_type=scope_type, scope_id=scope_id)

    def add(items: list[SearchResultItem]) -> None:
        results.extend(items[:_PER_TYPE_LIMIT])

    # Courses (institution-shared catalog) — curriculum.view, unscoped,
    # matching curriculum.py's `GET /courses`.
    if can("curriculum.view"):
        course_rows = (
            db.query(Course)
            .filter(or_(Course.code.ilike(term), Course.title.ilike(term)))
            .order_by(Course.code)
            .limit(_PER_TYPE_LIMIT)
            .all()
        )
        add(
            [
                SearchResultItem(
                    type="course",
                    id=str(c.id),
                    title=f"{c.code} — {c.title}",
                    subtitle=c.course_type,
                    url_hint="/course-settings",
                )
                for c in course_rows
            ]
        )

    # Course outcomes — curriculum.view, unscoped, matching curriculum.py's
    # `GET /course-outcomes`.
    if can("curriculum.view"):
        co_rows = (
            db.query(CourseOutcome)
            .filter(or_(CourseOutcome.code.ilike(term), CourseOutcome.statement.ilike(term)))
            .order_by(CourseOutcome.code)
            .limit(_PER_TYPE_LIMIT)
            .all()
        )
        add(
            [
                SearchResultItem(
                    type="course_outcome",
                    id=str(co.id),
                    title=co.code,
                    subtitle=co.statement[:120],
                    url_hint="/course-settings",
                )
                for co in co_rows
            ]
        )

    # Program outcomes — curriculum.view, scoped to the active program,
    # matching curriculum.py's `GET /program-outcomes`.
    if can("curriculum.view", scope_type="program"):
        po_rows = (
            db.query(ProgramOutcome)
            .filter(
                or_(
                    ProgramOutcome.code.ilike(term),
                    ProgramOutcome.statement.ilike(term),
                    ProgramOutcome.title.ilike(term),
                )
            )
            .order_by(ProgramOutcome.code)
            .limit(_PER_TYPE_LIMIT)
            .all()
        )
        add(
            [
                SearchResultItem(
                    type="program_outcome",
                    id=str(po.id),
                    title=f"{po.code} — {po.title}" if po.title else po.code,
                    subtitle=po.statement[:120],
                    url_hint="/program-settings",
                )
                for po in po_rows
            ]
        )

    # Assessments — assessment.view, scoped to the active program, matching
    # assessment.py's `GET /assessments`.
    if can("assessment.view", scope_type="program"):
        assessment_rows = (
            db.query(Assessment)
            .filter(Assessment.title.ilike(term))
            .order_by(Assessment.title)
            .limit(_PER_TYPE_LIMIT)
            .all()
        )
        add(
            [
                SearchResultItem(
                    type="assessment",
                    id=str(a.id),
                    title=a.title,
                    subtitle=f"Max marks: {a.max_marks}",
                    url_hint="/assessment",
                )
                for a in assessment_rows
            ]
        )

    # Students — student.view, unscoped, matching academic_ops.py's
    # `GET /students`.
    if can("student.view"):
        student_rows = (
            db.query(User, StudentProfile)
            .join(StudentProfile, StudentProfile.user_id == User.id)
            .filter(or_(User.full_name.ilike(term), StudentProfile.student_code.ilike(term)))
            .order_by(User.full_name)
            .limit(_PER_TYPE_LIMIT)
            .all()
        )
        add(
            [
                SearchResultItem(
                    type="student",
                    id=str(u.id),
                    title=u.full_name,
                    subtitle=f"Student — {sp.student_code}",
                    url_hint="/academic",
                )
                for u, sp in student_rows
            ]
        )

    # Faculty — open to any authenticated user, matching users.py's
    # `GET /faculty-directory` (not gated behind `user.view`).
    faculty_rows = (
        db.query(User, FacultyProfile)
        .join(FacultyProfile, FacultyProfile.user_id == User.id)
        .filter(or_(User.full_name.ilike(term), FacultyProfile.employee_code.ilike(term)))
        .order_by(User.full_name)
        .limit(_PER_TYPE_LIMIT)
        .all()
    )
    add(
        [
            SearchResultItem(
                type="faculty",
                id=str(u.id),
                title=u.full_name,
                subtitle=fp.designation or f"Faculty — {fp.employee_code}",
                url_hint="/academic",
            )
            for u, fp in faculty_rows
        ]
    )

    # Programs — open to any authenticated user, matching org.py's
    # `GET /programs`.
    prog_rows = (
        db.query(Program)
        .filter(or_(Program.name.ilike(term), Program.code.ilike(term)))
        .order_by(Program.name)
        .limit(_PER_TYPE_LIMIT)
        .all()
    )
    add(
        [
            SearchResultItem(
                type="program",
                id=str(p.id),
                title=p.name,
                subtitle=p.code,
                url_hint="/organization",
            )
            for p in prog_rows
        ]
    )

    return SearchResponse(results=results[:_TOTAL_LIMIT])
