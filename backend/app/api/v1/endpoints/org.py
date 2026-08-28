"""CRUD for organizational structure & academic calendar
(campuses/schools/departments/programs/program_versions, academic years/terms).

Reads require `*.view`, writes require `*.manage` (or `program.approve` for
the program-version workflow transition) — never a role-name check
(ARCHITECTURE.md §3).
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.base import WorkflowStatus
from app.db.session import session_scope
from app.db.tenancy import get_db
from app.middleware.audit import get_request_context
from app.models.public.institution import Institution
from app.models.tenant.identity import User
from app.models.tenant.org import (
    AcademicTerm,
    AcademicYear,
    Campus,
    Department,
    Program,
    ProgramVersion,
    School,
)
from app.schemas.institution import InstitutionRead, InstitutionUpdate
from app.schemas.org import (
    AcademicTermCreate,
    AcademicTermRead,
    AcademicYearCreate,
    AcademicYearRead,
    CampusCreate,
    CampusRead,
    DepartmentCreate,
    DepartmentRead,
    ProgramCreate,
    ProgramRead,
    ProgramVersionCreate,
    ProgramVersionRead,
    SchoolCreate,
    SchoolRead,
)
from app.services.audit import write_audit_log
from app.services.rbac import get_current_user, get_program_scoped_db, require_permission
from app.services.tenancy import ProgramProvisioningError, provision_program_schema

router = APIRouter()


def _get_or_404(db: Session, model, obj_id: uuid.UUID, label: str):
    obj = db.get(model, obj_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{label} not found")
    return obj


# --- This institution (self-service — public.institutions is otherwise
# platform-admin-only, see app/api/v1/endpoints/institutions.py) ---
@router.get("/institution", response_model=InstitutionRead)
def get_own_institution(
    request: Request,
    _current_user: User = Depends(require_permission("institution.view")),
) -> Institution:
    with session_scope() as public_db:
        institution = public_db.get(Institution, request.state.institution_id)
        if institution is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found"
            )
        return institution


@router.patch("/institution", response_model=InstitutionRead)
def update_own_institution(
    payload: InstitutionUpdate,
    request: Request,
    current_user: User = Depends(require_permission("institution.manage")),
) -> Institution:
    with session_scope() as public_db:
        institution = public_db.get(Institution, request.state.institution_id)
        if institution is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Institution not found"
            )
        changes = payload.model_dump(exclude_unset=True)
        previous_value = {field: getattr(institution, field) for field in changes}
        for field, value in changes.items():
            setattr(institution, field, value)
        public_db.add(institution)
        public_db.flush()
        public_db.refresh(institution)
        institution_dict = InstitutionRead.model_validate(institution).model_dump(mode="json")

    # Audit logging goes to the TENANT schema (this endpoint's usual home),
    # not `public.institutions` itself, matching every other write in this
    # file — a separate tenant-bound session, opened only for the log row.
    with session_scope(schema_translate_map={None: request.state.schema_name}) as tenant_db:
        write_audit_log(
            tenant_db,
            user_id=current_user.id,
            action="institution.updated",
            entity_type="Institution",
            entity_id=request.state.institution_id,
            previous_value={k: str(v) for k, v in previous_value.items()},
            new_value=changes,
            **get_request_context(request),
        )

    return InstitutionRead.model_validate(institution_dict)


# --- Campuses ---
@router.post("/campuses", response_model=CampusRead, status_code=status.HTTP_201_CREATED)
def create_campus(
    payload: CampusCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("org.manage")),
) -> Campus:
    campus = Campus(institution_id=request.state.institution_id, **payload.model_dump())
    db.add(campus)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="campus.created",
        entity_type="Campus",
        entity_id=campus.id,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return campus


@router.get("/campuses", response_model=list[CampusRead])
def list_campuses(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[Campus]:
    return db.query(Campus).order_by(Campus.name).all()


@router.get("/campuses/{campus_id}", response_model=CampusRead)
def get_campus(
    campus_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> Campus:
    return _get_or_404(db, Campus, campus_id, "Campus")


# --- Schools ---
@router.post("/schools", response_model=SchoolRead, status_code=status.HTTP_201_CREATED)
def create_school(
    payload: SchoolCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("org.manage")),
) -> School:
    _get_or_404(db, Campus, payload.campus_id, "Campus")
    school = School(**payload.model_dump())
    db.add(school)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="school.created",
        entity_type="School",
        entity_id=school.id,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return school


@router.get("/schools", response_model=list[SchoolRead])
def list_schools(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[School]:
    return db.query(School).order_by(School.name).all()


@router.get("/schools/{school_id}", response_model=SchoolRead)
def get_school(
    school_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> School:
    return _get_or_404(db, School, school_id, "School")


# --- Departments ---
@router.post("/departments", response_model=DepartmentRead, status_code=status.HTTP_201_CREATED)
def create_department(
    payload: DepartmentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("org.manage")),
) -> Department:
    _get_or_404(db, School, payload.school_id, "School")
    department = Department(**payload.model_dump())
    db.add(department)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="department.created",
        entity_type="Department",
        entity_id=department.id,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return department


@router.get("/departments", response_model=list[DepartmentRead])
def list_departments(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[Department]:
    return db.query(Department).order_by(Department.name).all()


@router.get("/departments/{department_id}", response_model=DepartmentRead)
def get_department(
    department_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> Department:
    return _get_or_404(db, Department, department_id, "Department")


# --- Programs ---
@router.post("/programs", response_model=ProgramRead, status_code=status.HTTP_201_CREATED)
def create_program(
    payload: ProgramCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("program.manage")),
) -> Program:
    _get_or_404(db, Department, payload.department_id, "Department")
    program = Program(**payload.model_dump())
    db.add(program)
    db.flush()

    # Every program gets its own schema (docs/adr/0003-schema-per-program.md)
    # — provisioned right after the Program row exists, same
    # schema-then-migrate sequencing as provision_tenant(). A failure here
    # propagates and rolls back this request's whole session (get_db's
    # except-block), undoing the Program row insert above; a failure that
    # somehow happens *after* this call but before the request commits would
    # leave an orphaned empty schema with no matching Program row — narrow
    # enough (just the audit-log write below) to accept rather than add
    # transactional machinery for.
    try:
        provision_program_schema(request.state.schema_name, program.code)
    except ProgramProvisioningError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Program created but its schema could not be provisioned: {exc}",
        ) from exc

    write_audit_log(
        db,
        user_id=current_user.id,
        action="program.created",
        entity_type="Program",
        entity_id=program.id,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return program


@router.get("/programs", response_model=list[ProgramRead])
def list_programs(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[Program]:
    """Deliberately open to any authenticated tenant user, not gated behind
    `program.view`: every program-scoped page (assessments, marks, course
    offerings/sections/enrollments, ...) needs this list client-side just to
    populate the X-Program-Code switcher (see
    `lib/active-program-context.tsx`), regardless of whether the caller
    holds `program.view` — a Faculty/Course Coordinator/Student role has
    real grants on plenty of program-scoped endpoints without ever holding
    that specific permission, and this only returns non-sensitive directory
    metadata (name/code/department/active-status). Real authorization for
    any actual program-scoped action still happens at that action's own
    endpoint via `require_permission` plus `get_program_context`'s grant
    check — this list being open doesn't bypass either."""
    return db.query(Program).order_by(Program.name).all()


@router.get("/programs/{program_id}", response_model=ProgramRead)
def get_program(
    program_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("program.view")),
) -> Program:
    return _get_or_404(db, Program, program_id, "Program")


# --- Program versions ---
# ProgramVersion lives in the per-program schema (docs/adr/0003-schema-per-program.md)
# — these routes need the `X-Program-Code` header, resolved and authorized
# by get_program_scoped_db (see app.services.rbac.get_program_context)
# *before* opening a session bound to that program's schema.
@router.post(
    "/program-versions", response_model=ProgramVersionRead, status_code=status.HTTP_201_CREATED
)
def create_program_version(
    payload: ProgramVersionCreate,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("program.manage", scope_type="program")),
) -> ProgramVersion:
    if payload.program_id != request.state.program_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="program_id does not match the X-Program-Code header.",
        )
    _get_or_404(db, Program, payload.program_id, "Program")
    _get_or_404(db, AcademicYear, payload.effective_academic_year_id, "Academic year")
    version = ProgramVersion(
        **payload.model_dump(), status=WorkflowStatus.DRAFT, created_by=current_user.id
    )
    db.add(version)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="program_version.created",
        entity_type="ProgramVersion",
        entity_id=version.id,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return version


@router.get("/program-versions", response_model=list[ProgramVersionRead])
def list_program_versions(
    db: Session = Depends(get_program_scoped_db),
    _current_user: User = Depends(require_permission("program.view", scope_type="program")),
) -> list[ProgramVersion]:
    return db.query(ProgramVersion).order_by(ProgramVersion.version_label).all()


@router.get("/program-versions/{version_id}", response_model=ProgramVersionRead)
def get_program_version(
    version_id: uuid.UUID,
    db: Session = Depends(get_program_scoped_db),
    _current_user: User = Depends(require_permission("program.view", scope_type="program")),
) -> ProgramVersion:
    return _get_or_404(db, ProgramVersion, version_id, "Program version")


# Valid forward transitions of the shared workflow (ARCHITECTURE.md §4).
_NEXT_STATUS: dict[WorkflowStatus, WorkflowStatus] = {
    WorkflowStatus.DRAFT: WorkflowStatus.SUBMITTED,
    WorkflowStatus.SUBMITTED: WorkflowStatus.REVIEWED,
    WorkflowStatus.REVIEWED: WorkflowStatus.APPROVED,
    WorkflowStatus.APPROVED: WorkflowStatus.PUBLISHED,
}


@router.post("/program-versions/{version_id}/advance", response_model=ProgramVersionRead)
def advance_program_version(
    version_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("program.approve", scope_type="program")),
) -> ProgramVersion:
    version = _get_or_404(db, ProgramVersion, version_id, "Program version")
    current_status = WorkflowStatus(version.status)
    next_status = _NEXT_STATUS.get(current_status)
    if next_status is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Program version in status {current_status.value!r} cannot be advanced further."
            ),
        )

    previous_value = {"status": current_status.value}
    version.status = next_status
    if next_status == WorkflowStatus.APPROVED:
        version.approved_by = current_user.id
    db.add(version)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="program_version.status_changed",
        entity_type="ProgramVersion",
        entity_id=version.id,
        previous_value=previous_value,
        new_value={"status": next_status.value},
        **get_request_context(request),
    )
    return version


# --- Academic years ---
@router.post(
    "/academic-years", response_model=AcademicYearRead, status_code=status.HTTP_201_CREATED
)
def create_academic_year(
    payload: AcademicYearCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("academic_calendar.manage")),
) -> AcademicYear:
    year = AcademicYear(**payload.model_dump())
    db.add(year)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="academic_year.created",
        entity_type="AcademicYear",
        entity_id=year.id,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return year


@router.get("/academic-years", response_model=list[AcademicYearRead])
def list_academic_years(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[AcademicYear]:
    """Open to any authenticated tenant user, not gated behind
    `academic_calendar.view` — same reasoning as `list_academic_terms`
    below and `list_programs` above: non-sensitive scheduling metadata that
    Program Coordinator (and others) need for PEO/PO/course-version forms
    despite not holding that specific permission."""
    return db.query(AcademicYear).order_by(AcademicYear.start_date.desc()).all()


# --- Academic terms ---
@router.post(
    "/academic-terms", response_model=AcademicTermRead, status_code=status.HTTP_201_CREATED
)
def create_academic_term(
    payload: AcademicTermCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("academic_calendar.manage")),
) -> AcademicTerm:
    _get_or_404(db, AcademicYear, payload.academic_year_id, "Academic year")
    term = AcademicTerm(**payload.model_dump())
    db.add(term)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="academic_term.created",
        entity_type="AcademicTerm",
        entity_id=term.id,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return term


@router.get("/academic-terms", response_model=list[AcademicTermRead])
def list_academic_terms(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> list[AcademicTerm]:
    """Open to any authenticated tenant user, not gated behind
    `academic_calendar.view` — same reasoning as `list_programs` above:
    term name/dates are non-sensitive scheduling metadata that Faculty and
    Course Coordinator need for basically every program-scoped workflow
    (offerings, sections, assessments, marks entry, improvement plans)
    despite neither role holding `academic_calendar.view` — this endpoint
    was quietly 403ing for both of them (`useAcademicTermLookup` on the
    frontend swallows the error and just shows blank term names) until
    caught by testing the Assessment page as a Course Coordinator."""
    return db.query(AcademicTerm).order_by(AcademicTerm.start_date.desc()).all()
