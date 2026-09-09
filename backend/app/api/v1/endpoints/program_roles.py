"""Program-scoped role management: lets a Program Administrator/Coordinator
grant/revoke Faculty, Section Coordinator, and Course Administrator roles for
people within their own program — the scoped counterpart to the
institution-wide `role.manage` surface in `app.api.v1.endpoints.users`,
which neither of those roles holds (see docs/course_level_settings_and_
approval_workflow.md's follow-up discussion: extending the institution-wide
endpoints to accept `scope_type="program"` without also restricting *what*
they can see/grant would let a Program Coordinator list every institution
user or grant Institution Administrator to anyone — a real privilege-
escalation risk, not just a permission-check gap. This is a deliberately
separate, narrower surface instead.

Two restrictions keep this safe regardless of what `program_role.manage`
grant shape a caller holds:

1. `ASSIGNABLE_ROLE_NAMES` is a fixed allowlist — never Institution
   Administrator, Super Administrator, or any other role, no matter what
   `role_id` a caller passes. This is a business-policy restriction on top
   of the (permission-code-based, per ARCHITECTURE.md §3) authorization
   check, not a role-name-based auth decision — callers still need a real
   `program_role.manage` grant on this program to reach these endpoints at
   all.
2. Every write is scoped to the program `get_program_scoped_db` already
   authorized the caller against (via `X-Program-Code` + `get_program_context`)
   — a "course" grant is only accepted if that course actually has a
   `CourseOffering` inside *this* program's own schema (checked via a plain
   query on the already-program-bound session, so it structurally cannot
   see another program's offerings), and a "program" grant is always
   scoped to this exact program, never institution-wide.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.security import generate_temporary_password, hash_password
from app.middleware.audit import get_request_context
from app.models.tenant.courses.catalog import Course, CourseVersion
from app.models.tenant.courses.delivery import CourseOffering, CourseSection, FacultyAssignment
from app.models.tenant.identity import FacultyProfile, Role, User, UserRole
from app.schemas.program_roles import (
    FacultyCreate,
    FacultyCreateResult,
    ProgramCourseRead,
    ProgramFacultyRead,
    ProgramRoleGrantCreate,
    ProgramRoleGrantRead,
    ProgramRosterRead,
)
from app.services.audit import write_audit_log
from app.services.rbac import get_program_scoped_db, require_permission

router = APIRouter()

#: The only roles grantable through this surface — see module docstring.
ASSIGNABLE_ROLE_NAMES: tuple[str, ...] = ("Faculty", "Section Coordinator", "Course Administrator")

#: Section Coordinator's real-world meaning is "faculty who already teaches
#: this course, elevated to also own its assessment plan" — a grant without
#: an existing FacultyAssignment on one of the course's sections would let
#: someone approve marks entry for a course they have no teaching record on.
_SECTION_COORDINATOR_ROLE_NAME = "Section Coordinator"


def _program_course_ids(db: Session) -> list[uuid.UUID]:
    """Every `Course.id` with at least one `CourseOffering` in the caller's
    own program schema — the session is already bound to that one program
    (via `get_program_scoped_db`), so this cannot reach another program's
    offerings no matter what the caller passes elsewhere."""
    rows = (
        db.query(Course.id)
        .join(CourseVersion, CourseVersion.course_id == Course.id)
        .join(CourseOffering, CourseOffering.course_version_id == CourseVersion.id)
        .distinct()
        .all()
    )
    return [r[0] for r in rows]


@router.get("/roster", response_model=ProgramRosterRead)
def get_program_roster(
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    _current_user: User = Depends(require_permission("program_role.manage", scope_type="program")),
) -> ProgramRosterRead:
    """Everything the role-assignment UI needs in one call: the faculty
    pool (anyone already assigned to a section here, or already holding an
    assignable role scoped here), the fixed assignable-role list, this
    program's own courses, and the relevant existing grants."""
    course_ids = _program_course_ids(db)
    program_id = request.state.program_id

    assigned_user_ids = {
        row[0]
        for row in db.query(FacultyAssignment.faculty_user_id).distinct().all()
    }

    roles = db.query(Role).filter(Role.name.in_(ASSIGNABLE_ROLE_NAMES)).all()
    role_ids = [r.id for r in roles]

    scoped_grants = (
        db.query(UserRole)
        .filter(
            UserRole.role_id.in_(role_ids),
            (UserRole.scope_type.is_(None))
            | ((UserRole.scope_type == "program") & (UserRole.scope_id == program_id))
            | ((UserRole.scope_type == "course") & (UserRole.scope_id.in_(course_ids))),
        )
        .all()
    )
    granted_user_ids = {g.user_id for g in scoped_grants}

    faculty_ids = assigned_user_ids | granted_user_ids
    faculty = (
        db.query(User).filter(User.id.in_(faculty_ids)).order_by(User.full_name).all()
        if faculty_ids
        else []
    )

    courses = (
        db.query(Course).filter(Course.id.in_(course_ids)).order_by(Course.code).all()
        if course_ids
        else []
    )

    return ProgramRosterRead(
        faculty=[ProgramFacultyRead.model_validate(u) for u in faculty],
        assignable_roles=[{"id": str(r.id), "name": r.name} for r in roles],
        courses=[ProgramCourseRead(id=c.id, code=c.code, title=c.title) for c in courses],
        grants=[ProgramRoleGrantRead.model_validate(g) for g in scoped_grants],
    )


@router.post(
    "/user-roles", response_model=ProgramRoleGrantRead, status_code=status.HTTP_201_CREATED
)
def create_program_role_grant(
    payload: ProgramRoleGrantCreate,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("program_role.manage", scope_type="program")),
) -> UserRole:
    role = db.get(Role, payload.role_id)
    if role is None or role.name not in ASSIGNABLE_ROLE_NAMES:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail=f"Only {', '.join(ASSIGNABLE_ROLE_NAMES)} can be granted here.",
        )
    if db.get(User, payload.user_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="User not found")

    if payload.scope_type == "course":
        if payload.course_id is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="course_id is required")
        if payload.course_id not in _program_course_ids(db):
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, detail="That course is not offered in this program."
            )
        if role.name == _SECTION_COORDINATOR_ROLE_NAME:
            has_assignment = (
                db.query(FacultyAssignment.id)
                .join(CourseSection, FacultyAssignment.course_section_id == CourseSection.id)
                .join(CourseOffering, CourseSection.course_offering_id == CourseOffering.id)
                .join(CourseVersion, CourseOffering.course_version_id == CourseVersion.id)
                .filter(
                    FacultyAssignment.faculty_user_id == payload.user_id,
                    CourseVersion.course_id == payload.course_id,
                )
                .first()
                is not None
            )
            if not has_assignment:
                raise HTTPException(
                    status.HTTP_400_BAD_REQUEST,
                    detail=(
                        "This user must already hold a faculty assignment on a section of "
                        "this course before they can be made Section Coordinator for it."
                    ),
                )
        scope_id = payload.course_id
    else:
        scope_id = request.state.program_id

    grant = UserRole(
        user_id=payload.user_id, role_id=payload.role_id,
        scope_type=payload.scope_type, scope_id=scope_id,
    )
    db.add(grant)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="program_role.granted",
        entity_type="UserRole",
        entity_id=grant.id,
        new_value={
            "user_id": str(payload.user_id), "role_name": role.name,
            "scope_type": payload.scope_type, "scope_id": str(scope_id),
        },
        **get_request_context(request),
    )
    return grant


@router.delete("/user-roles/{grant_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_program_role_grant(
    grant_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("program_role.manage", scope_type="program")),
) -> None:
    grant = db.get(UserRole, grant_id)
    if grant is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Role grant not found")
    role = db.get(Role, grant.role_id)
    if role is None or role.name not in ASSIGNABLE_ROLE_NAMES:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="That role cannot be revoked here.")
    # Re-verify the grant's own scope actually belongs to this program —
    # never trust that a grant id passed in the URL is one this caller is
    # authorized to touch just because they hold *some* program_role.manage
    # grant somewhere. An unscoped (institution-wide) grant is deliberately
    # never revocable here even if it happens to be one of the allowlisted
    # role names — revoking it would affect that person everywhere, not
    # just this program, which is outside what this narrower surface may do.
    if grant.scope_type is None:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail="This is an institution-wide grant — revoke it from Users & Roles instead.",
        )
    belongs_to_this_program = (
        grant.scope_type == "program" and grant.scope_id == request.state.program_id
    ) or (grant.scope_type == "course" and grant.scope_id in _program_course_ids(db))
    if not belongs_to_this_program:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, detail="That grant belongs to another program."
        )

    previous_value = {
        "user_id": str(grant.user_id), "role_name": role.name,
        "scope_type": grant.scope_type, "scope_id": str(grant.scope_id) if grant.scope_id else None,
    }
    db.delete(grant)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="program_role.revoked",
        entity_type="UserRole",
        entity_id=grant_id,
        previous_value=previous_value,
        **get_request_context(request),
    )


# --- Faculty Management (spec §30: "Add Individually") ---
# A brand-new user account, not a role grant on an existing one — the gap
# this closes: `POST /users` (users.py) requires `user.manage`, which
# Program Coordinator does not hold, so before this endpoint they could
# only grant Faculty to a user an Institution Administrator had already
# created, never bring a new faculty member into the tenant themselves.
@router.post(
    "/faculty", response_model=FacultyCreateResult, status_code=status.HTTP_201_CREATED
)
def create_faculty(
    payload: FacultyCreate,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("program_role.manage", scope_type="program")),
) -> FacultyCreateResult:
    if db.query(User).filter(User.email == payload.email).one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already in use")

    faculty_role = db.query(Role).filter(Role.name == "Faculty").one_or_none()
    if faculty_role is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="The 'Faculty' system role is missing from this tenant.",
        )

    temporary_password = generate_temporary_password()
    user = User(
        email=payload.email,
        password_hash=hash_password(temporary_password),
        full_name=payload.full_name,
        is_active=True,
        must_change_password=True,
    )
    db.add(user)
    db.flush()

    profile = FacultyProfile(
        user_id=user.id,
        employee_code=payload.employee_code,
        designation=payload.designation,
        contract_type=payload.contract_type,
        department_id=payload.department_id,
    )
    db.add(profile)

    grant = UserRole(
        user_id=user.id,
        role_id=faculty_role.id,
        scope_type="program",
        scope_id=request.state.program_id,
    )
    db.add(grant)
    db.flush()

    write_audit_log(
        db,
        user_id=current_user.id,
        action="faculty.created",
        entity_type="User",
        entity_id=user.id,
        new_value={
            "email": payload.email,
            "full_name": payload.full_name,
            "employee_code": payload.employee_code,
            "contract_type": payload.contract_type,
        },
        **get_request_context(request),
    )
    return FacultyCreateResult(
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        temporary_password=temporary_password,
    )
