""""My sections only" query-scoping for faculty-facing endpoints (Faculty
Module spec — BR-03 "Course Ownership": faculty can only manage courses and
sections to which they are currently assigned).

Deliberately *not* a new RBAC scope type: every program-schema endpoint
already requires `require_permission(code, scope_type="program")`, whose
grant-matching demands an exact `(scope_type, scope_id)` match — a second,
independent scope dimension couldn't also satisfy that already-mandatory
check. Instead, ownership is derived straight from `FacultyAssignment`
(already the single source of truth for who teaches what) and applied as an
explicit query filter inside each endpoint:

- A caller holding the broader authoring permission for a resource
  (`section.manage`, checked via `is_section_authority`) — Program
  Coordinator, Program/Course Administrator — sees/acts on every section in
  the program, exactly as today.
- A caller who only holds the narrower permission (`section.view`,
  `assessment.create`, `marks.enter`, ...) — Faculty, Course Coordinator —
  is restricted to sections where they have a `FacultyAssignment` row.

`ensure_section_access`'s `section.manage` bypass is correct for genuinely
*administrative* actions (managing offerings/sections/enrollments — the
things `section.manage` is actually named for). It is **wrong** for actions
that are a personal attestation of having delivered the course — entering
marks, submitting final grades, authoring an assessment, uploading course
files — because a Program Coordinator's program-wide `section.manage`
grant would then let them silently act on a section they never taught,
corrupting exactly the "who taught/assessed this offering" audit trail the
platform exists to guarantee (found live: a Program Coordinator account was
able to enter marks for a section with no `FacultyAssignment` row for
them). Use `ensure_assigned_to_section` for that category instead — it has
no authority bypass at all. If a coordinator genuinely needs to act as
instructor on a section, the correct path is creating a `FacultyAssignment`
row for themselves first (their `section.manage` grant already allows
that), not bypassing this check.
"""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.tenant.courses.delivery import CourseOffering, CourseSection, FacultyAssignment
from app.models.tenant.org import AcademicTerm
from app.services.rbac import user_has_permission


def get_my_course_section_ids(db: Session, user_id: uuid.UUID) -> set[uuid.UUID]:
    """Every `CourseSection` id the given user has a `FacultyAssignment` on,
    regardless of role ("coordinator" or "instructor") — both are scoped to
    their own assigned sections, they just differ in which actions their
    role's permission grants allow within that scope."""
    rows = (
        db.query(FacultyAssignment.course_section_id)
        .filter(FacultyAssignment.faculty_user_id == user_id)
        .all()
    )
    return {row[0] for row in rows}


def is_section_authority(
    db: Session, user_id: uuid.UUID, program_id: uuid.UUID | None = None
) -> bool:
    """True for a caller who administers sections institution/program-wide
    (Program Coordinator, Program/Course Administrator) rather than only the
    ones they're personally assigned to. `section.manage` is the one
    permission code every such role holds and no purely-teaching role
    (Faculty, Course Coordinator) does — see `app.seed.default_roles`.

    Checks both an unscoped grant (a true institution-wide role) and one
    scoped to `program_id`: every real Coordinator/Administrator grant in
    this codebase is created `scope_type="program"` (see e.g.
    `app.services.rbac.get_program_context`'s docstring), so a bare
    unscoped-only check would silently never match any real deployment —
    pass the request's already-resolved `request.state.program_id` here
    (set by `get_program_context`, a dependency every program-scoped
    endpoint already declares transitively via `require_permission(...,
    scope_type="program")`)."""
    if user_has_permission(db, user_id, "section.manage"):
        return True
    return program_id is not None and user_has_permission(
        db, user_id, "section.manage", scope_type="program", scope_id=program_id
    )


def ensure_section_access(
    db: Session,
    user_id: uuid.UUID,
    course_section_id: uuid.UUID,
    program_id: uuid.UUID | None = None,
) -> None:
    """403s unless the caller either administers the whole program
    (`is_section_authority`) or is personally assigned to
    `course_section_id`. Call this from every endpoint that reads or writes
    a specific section's assessments/marks/students once the target
    section id is known (either from the path/query or from a fetched row);
    pass `request.state.program_id` as `program_id` so a Coordinator's
    normal program-scoped grant is recognized — see `is_section_authority`."""
    if is_section_authority(db, user_id, program_id):
        return
    if course_section_id not in get_my_course_section_ids(db, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not assigned to this course section",
        )


def ensure_current_term(db: Session, course_section_id: uuid.UUID) -> None:
    """403s if `course_section_id`'s `AcademicTerm` is not the active one
    (BR-01: "Faculty editing capabilities apply only to courses in the
    current active semester"). A previous-semester section is still fully
    readable — every read endpoint stays on `ensure_section_access` or no
    check at all — this only guards the write path, via
    `ensure_assigned_to_section` below."""
    is_active = (
        db.query(AcademicTerm.is_active)
        .join(CourseOffering, CourseOffering.academic_term_id == AcademicTerm.id)
        .join(CourseSection, CourseSection.course_offering_id == CourseOffering.id)
        .filter(CourseSection.id == course_section_id)
        .scalar()
    )
    if not is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This course is from a previous semester and is read-only",
        )


def ensure_assigned_to_section(
    db: Session, user_id: uuid.UUID, course_section_id: uuid.UUID
) -> None:
    """403s unless the caller has an actual `FacultyAssignment` row on
    `course_section_id` — no `section.manage`/authority bypass, unlike
    `ensure_section_access`. Use this for entering marks, submitting final
    grades, authoring assessments/questions, and uploading course files —
    see this module's docstring for why those must stay strictly tied to
    real assignment even for a program-wide administrator. Also enforces
    BR-01 (`ensure_current_term`): every caller of this function is
    attempting a write, and every such write is only ever legitimate in the
    section's own active term."""
    if course_section_id not in get_my_course_section_ids(db, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not assigned to this course section",
        )
    ensure_current_term(db, course_section_id)


def filter_to_my_sections(
    db: Session, user_id: uuid.UUID, program_id: uuid.UUID | None = None
) -> set[uuid.UUID] | None:
    """For list endpoints: returns `None` (no filter — caller sees every
    section in the program) if the user is a section authority; otherwise
    returns the set of section ids their query should be restricted to
    (`Model.course_section_id.in_(result)` — empty set means "no sections",
    not "no filter", so callers must check for `None` specifically, not
    falsiness). Pass `request.state.program_id` — see `is_section_authority`."""
    if is_section_authority(db, user_id, program_id):
        return None
    return get_my_course_section_ids(db, user_id)
