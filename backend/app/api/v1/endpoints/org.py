"""CRUD for organizational structure & academic calendar
(campuses/schools/departments/programs/program_versions, academic years/terms).

Reads require `*.view`, writes require `*.manage` (or `program.approve` for
the program-version workflow transition) — never a role-name check
(ARCHITECTURE.md §3).
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.base import WorkflowStatus
from app.db.session import session_scope
from app.db.tenancy import get_db
from app.middleware.audit import get_request_context
from app.models.public.institution import Institution
from app.models.tenant.identity import StudentProfile, User
from app.models.tenant.org import (
    AcademicTerm,
    AcademicYear,
    Campus,
    Cohort,
    Department,
    Program,
    ProgramVersion,
    School,
    TermEffectiveCurriculum,
)
from app.schemas.academic import StudentRead
from app.schemas.institution import InstitutionRead, InstitutionUpdate
from app.schemas.org import (
    AcademicTermCreate,
    AcademicTermRead,
    AcademicTermUpdate,
    AcademicYearCreate,
    AcademicYearRead,
    CampusCreate,
    CampusRead,
    CampusUpdate,
    CohortChangeCurriculum,
    CohortCreate,
    CohortRead,
    CohortUpdate,
    DepartmentCreate,
    DepartmentRead,
    DepartmentUpdate,
    ProgramCreate,
    ProgramRead,
    ProgramUpdate,
    ProgramVersionCreate,
    ProgramVersionRead,
    SchoolCreate,
    SchoolRead,
    SchoolUpdate,
    TermEffectiveCurriculumCreate,
    TermEffectiveCurriculumRead,
)
from app.services.academic_terms import validate_calendar_order
from app.services.audit import write_audit_log
from app.services.rbac import get_current_user, get_program_scoped_db, require_permission
from app.services.tenancy import (
    InvalidProgramCodeError,
    ProgramProvisioningError,
    provision_program_schema,
)

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


@router.patch("/campuses/{campus_id}", response_model=CampusRead)
def update_campus(
    campus_id: uuid.UUID,
    payload: CampusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("org.manage")),
) -> Campus:
    campus = _get_or_404(db, Campus, campus_id, "Campus")
    changes = payload.model_dump(exclude_unset=True)
    previous_value = {field: getattr(campus, field) for field in changes}
    for field, value in changes.items():
        setattr(campus, field, value)
    db.add(campus)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="campus.updated",
        entity_type="Campus",
        entity_id=campus.id,
        previous_value={k: str(v) for k, v in previous_value.items()},
        new_value=changes,
        **get_request_context(request),
    )
    return campus


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


@router.patch("/schools/{school_id}", response_model=SchoolRead)
def update_school(
    school_id: uuid.UUID,
    payload: SchoolUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("org.manage")),
) -> School:
    school = _get_or_404(db, School, school_id, "School")
    changes = payload.model_dump(exclude_unset=True)
    if "campus_id" in changes:
        _get_or_404(db, Campus, changes["campus_id"], "Campus")
    previous_value = {field: getattr(school, field) for field in changes}
    for field, value in changes.items():
        setattr(school, field, value)
    db.add(school)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="school.updated",
        entity_type="School",
        entity_id=school.id,
        previous_value={k: str(v) for k, v in previous_value.items()},
        new_value=changes,
        **get_request_context(request),
    )
    return school


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


@router.patch("/departments/{department_id}", response_model=DepartmentRead)
def update_department(
    department_id: uuid.UUID,
    payload: DepartmentUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("org.manage")),
) -> Department:
    department = _get_or_404(db, Department, department_id, "Department")
    changes = payload.model_dump(exclude_unset=True)
    if "school_id" in changes:
        _get_or_404(db, School, changes["school_id"], "School")
    previous_value = {field: getattr(department, field) for field in changes}
    for field, value in changes.items():
        setattr(department, field, value)
    db.add(department)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="department.updated",
        entity_type="Department",
        entity_id=department.id,
        previous_value={k: str(v) for k, v in previous_value.items()},
        new_value=changes,
        **get_request_context(request),
    )
    return department


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
    program_id, program_code = program.id, program.code

    # Commit the Program row *now*, before provisioning its schema — not
    # after, as this used to. The new program schema's `program_versions`
    # table carries a real FK back to this very row (ProgramVersion.program_id),
    # so creating it needs a lock on `programs` that this request's own
    # still-open INSERT already holds. Provisioning used to run inside that
    # same open transaction: Postgres can't detect that as a deadlock (this
    # session isn't waiting on any lock, just synchronously blocked in
    # Python on the migration finishing) and the request would hang
    # indefinitely instead of failing fast — the real mechanism behind
    # "tried to add new program but failed to add any," reproduced and
    # confirmed live (a stuck `idle in transaction` session holding the
    # lock, migration waiting on it, both stuck for 100+ minutes) while
    # fixing this. Committing first releases the lock before provisioning
    # begins; a provisioning failure now needs its own explicit rollback
    # (the row is no longer undone for free by get_db's except-block, since
    # it's already durable) instead of relying on the whole-session rollback
    # that used to make this "atomic."
    db.commit()

    try:
        provision_program_schema(request.state.schema_name, program_code)
    except InvalidProgramCodeError as exc:
        # A Core-style bulk delete, not `db.delete(<ORM object>)`: the ORM
        # form would load `Program.versions` to evaluate cascade rules, and
        # that relationship lives in the "program" schema_translate_map key
        # — never bound on this plain `get_db` session (only
        # `get_program_scoped_db` binds it), so it'd fail trying to resolve
        # a schema literally named "program". The program's own schema was
        # never created in this branch anyway (code validation failed
        # before that step), so there's nothing there to clean up.
        db.query(Program).filter(Program.id == program_id).delete()
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"{exc} The program code is used to derive a database schema name, so it "
                "can only contain lowercase letters, digits, and hyphens."
            ),
        ) from exc
    except ProgramProvisioningError as exc:
        db.query(Program).filter(Program.id == program_id).delete()
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Program creation failed and was rolled back: {exc}",
        ) from exc

    program = db.get(Program, program_id)
    write_audit_log(
        db,
        user_id=current_user.id,
        action="program.created",
        entity_type="Program",
        entity_id=program_id,
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


@router.patch("/programs/{program_id}", response_model=ProgramRead)
def update_program(
    program_id: uuid.UUID,
    payload: ProgramUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("program.manage")),
) -> Program:
    program = _get_or_404(db, Program, program_id, "Program")
    changes = payload.model_dump(exclude_unset=True)
    if "department_id" in changes:
        _get_or_404(db, Department, changes["department_id"], "Department")
    previous_value = {field: getattr(program, field) for field in changes}
    for field, value in changes.items():
        setattr(program, field, value)
    db.add(program)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="program.updated",
        entity_type="Program",
        entity_id=program.id,
        previous_value={k: str(v) for k, v in previous_value.items()},
        new_value=changes,
        **get_request_context(request),
    )
    return program


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
    if payload.previous_version_id is not None:
        _get_or_404(db, ProgramVersion, payload.previous_version_id, "Previous program version")
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
        program_version_id=version.id,
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
    if next_status == WorkflowStatus.PUBLISHED:
        version.published_by = current_user.id
        version.published_at = datetime.now(UTC)
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
        program_version_id=version.id,
        **get_request_context(request),
    )
    return version


@router.post("/program-versions/{version_id}/unpublish", response_model=ProgramVersionRead)
def unpublish_program_version(
    version_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("program.approve", scope_type="program")),
) -> ProgramVersion:
    """Explicit reverse transition out of `published` (spec §23) — never a
    silent edit of a published curriculum. Distinct from the shared
    `WorkflowStatus` forward-only `_NEXT_STATUS` table above: unpublishing
    always lands back on `draft` (never `submitted`/`reviewed`/`approved`,
    which would misrepresent an unpublished version as still mid-review), so
    it does not reuse `advance_program_version`'s transition table.
    """
    version = _get_or_404(db, ProgramVersion, version_id, "Program version")
    if WorkflowStatus(version.status) != WorkflowStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only a published program version can be unpublished.",
        )
    previous_value = {"status": version.status}
    version.status = WorkflowStatus.DRAFT
    version.unpublished_by = current_user.id
    version.unpublished_at = datetime.now(UTC)
    db.add(version)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="program_version.unpublished",
        entity_type="ProgramVersion",
        entity_id=version.id,
        previous_value=previous_value,
        new_value={"status": WorkflowStatus.DRAFT.value},
        program_version_id=version.id,
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
    validate_calendar_order(
        start_date=payload.start_date,
        add_drop_last_date=payload.add_drop_last_date,
        midterm_start_date=payload.midterm_start_date,
        midterm_end_date=payload.midterm_end_date,
        final_exam_start_date=payload.final_exam_start_date,
        final_exam_end_date=payload.final_exam_end_date,
        result_due_date=payload.result_due_date,
        result_publication_date=payload.result_publication_date,
        end_date=payload.end_date,
    )
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


@router.patch("/academic-terms/{term_id}", response_model=AcademicTermRead)
def update_academic_term(
    term_id: uuid.UUID,
    payload: AcademicTermUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("academic_calendar.manage")),
) -> AcademicTerm:
    """Name/type/dates only — `is_active` is deliberately not editable here;
    see `activate_academic_term` for why."""
    term = _get_or_404(db, AcademicTerm, term_id, "Academic term")
    validate_calendar_order(
        start_date=payload.start_date,
        add_drop_last_date=payload.add_drop_last_date,
        midterm_start_date=payload.midterm_start_date,
        midterm_end_date=payload.midterm_end_date,
        final_exam_start_date=payload.final_exam_start_date,
        final_exam_end_date=payload.final_exam_end_date,
        result_due_date=payload.result_due_date,
        result_publication_date=payload.result_publication_date,
        end_date=payload.end_date,
    )
    previous_value = {
        "name": term.name, "term_type": term.term_type,
        "start_date": term.start_date.isoformat(), "end_date": term.end_date.isoformat(),
    }
    for field, value in payload.model_dump().items():
        setattr(term, field, value)
    db.add(term)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="academic_term.updated",
        entity_type="AcademicTerm",
        entity_id=term.id,
        previous_value=previous_value,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return term


@router.post("/academic-terms/{term_id}/activate", response_model=AcademicTermRead)
def activate_academic_term(
    term_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("academic_calendar.manage")),
) -> AcademicTerm:
    """The one place `AcademicTerm.is_active` is ever set — atomically
    deactivates every other term in the tenant first, so exactly one term
    is ever "current" (docs/course_level_settings_and_approval_workflow.md
    §8/§11: current-semester filtering is driven by this flag, never a
    hardcoded date, so more than one active term silently pollutes every
    "current courses" view in the app with a stale semester's data — found
    live: `tenant_demo` had two terms flagged active at once with no UI
    that could have prevented or fixed it, since this action didn't exist
    yet). A bare `is_active` field on the generic update endpoint would let
    a caller re-introduce that bug by flipping one term on without
    flipping the others off."""
    term = _get_or_404(db, AcademicTerm, term_id, "Academic term")
    previously_active = [
        t.id for t in db.query(AcademicTerm).filter(AcademicTerm.is_active.is_(True))
    ]
    db.query(AcademicTerm).filter(AcademicTerm.id != term_id).update({"is_active": False})
    term.is_active = True
    db.add(term)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="academic_term.activated",
        entity_type="AcademicTerm",
        entity_id=term.id,
        previous_value={"previously_active_term_ids": [str(t) for t in previously_active]},
        new_value={"active_term_id": str(term.id)},
        **get_request_context(request),
    )
    return term


# --- Term effective curricula (spec §4) ---
# `section.manage` (not `academic_calendar.manage`): this is the Program
# Coordinator's own trimester-setup step (spec §27 "Select Effective
# Curriculum(s)"), the same permission tier that already gates course
# offerings/sections/faculty assignment for this program.
@router.post(
    "/term-effective-curricula",
    response_model=TermEffectiveCurriculumRead,
    status_code=status.HTTP_201_CREATED,
)
def create_term_effective_curriculum(
    payload: TermEffectiveCurriculumCreate,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("section.manage", scope_type="program")),
) -> TermEffectiveCurriculum:
    _get_or_404(db, AcademicTerm, payload.academic_term_id, "Academic term")
    _get_or_404(db, ProgramVersion, payload.program_version_id, "Program version")
    existing = (
        db.query(TermEffectiveCurriculum)
        .filter(
            TermEffectiveCurriculum.academic_term_id == payload.academic_term_id,
            TermEffectiveCurriculum.program_version_id == payload.program_version_id,
        )
        .one_or_none()
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This curriculum is already marked effective for this term.",
        )
    effective = TermEffectiveCurriculum(**payload.model_dump(), created_by=current_user.id)
    db.add(effective)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="term_effective_curriculum.created",
        entity_type="TermEffectiveCurriculum",
        entity_id=effective.id,
        new_value=payload.model_dump(mode="json"),
        academic_term_id=effective.academic_term_id,
        program_version_id=effective.program_version_id,
        **get_request_context(request),
    )
    return effective


@router.get("/term-effective-curricula", response_model=list[TermEffectiveCurriculumRead])
def list_term_effective_curricula(
    academic_term_id: uuid.UUID | None = None,
    db: Session = Depends(get_program_scoped_db),
    _current_user: User = Depends(require_permission("section.view", scope_type="program")),
) -> list[TermEffectiveCurriculum]:
    query = db.query(TermEffectiveCurriculum)
    if academic_term_id is not None:
        query = query.filter(TermEffectiveCurriculum.academic_term_id == academic_term_id)
    return query.all()


@router.delete("/term-effective-curricula/{effective_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_term_effective_curriculum(
    effective_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("section.manage", scope_type="program")),
) -> None:
    effective = _get_or_404(db, TermEffectiveCurriculum, effective_id, "Term effective curriculum")
    write_audit_log(
        db,
        user_id=current_user.id,
        action="term_effective_curriculum.deleted",
        entity_type="TermEffectiveCurriculum",
        entity_id=effective.id,
        previous_value={"program_version_id": str(effective.program_version_id)},
        academic_term_id=effective.academic_term_id,
        program_version_id=effective.program_version_id,
        **get_request_context(request),
    )
    db.delete(effective)


# --- Cohorts (spec §5) ---
@router.post("/cohorts", response_model=CohortRead, status_code=status.HTTP_201_CREATED)
def create_cohort(
    payload: CohortCreate,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("section.manage", scope_type="program")),
) -> Cohort:
    _get_or_404(db, AcademicTerm, payload.intake_term_id, "Academic term")
    _get_or_404(db, ProgramVersion, payload.program_version_id, "Program version")
    cohort = Cohort(**payload.model_dump(), status="active")
    db.add(cohort)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="cohort.created",
        entity_type="Cohort",
        entity_id=cohort.id,
        new_value=payload.model_dump(mode="json"),
        academic_term_id=cohort.intake_term_id,
        program_version_id=cohort.program_version_id,
        **get_request_context(request),
    )
    return cohort


@router.get("/cohorts", response_model=list[CohortRead])
def list_cohorts(
    db: Session = Depends(get_program_scoped_db),
    _current_user: User = Depends(require_permission("section.view", scope_type="program")),
) -> list[Cohort]:
    return db.query(Cohort).order_by(Cohort.intake_year.desc(), Cohort.code).all()


@router.get("/cohorts/{cohort_id}", response_model=CohortRead)
def get_cohort(
    cohort_id: uuid.UUID,
    db: Session = Depends(get_program_scoped_db),
    _current_user: User = Depends(require_permission("section.view", scope_type="program")),
) -> Cohort:
    return _get_or_404(db, Cohort, cohort_id, "Cohort")


@router.patch("/cohorts/{cohort_id}", response_model=CohortRead)
def update_cohort(
    cohort_id: uuid.UUID,
    payload: CohortUpdate,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("section.manage", scope_type="program")),
) -> Cohort:
    cohort = _get_or_404(db, Cohort, cohort_id, "Cohort")
    changes = payload.model_dump(exclude_unset=True)
    previous_value = {field: getattr(cohort, field) for field in changes}
    for field, value in changes.items():
        setattr(cohort, field, value)
    db.add(cohort)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="cohort.updated",
        entity_type="Cohort",
        entity_id=cohort.id,
        previous_value=previous_value,
        new_value=changes,
        academic_term_id=cohort.intake_term_id,
        program_version_id=cohort.program_version_id,
        **get_request_context(request),
    )
    return cohort


@router.post("/cohorts/{cohort_id}/change-curriculum", response_model=CohortRead)
def change_cohort_curriculum(
    cohort_id: uuid.UUID,
    payload: CohortChangeCurriculum,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("program.manage", scope_type="program")),
) -> Cohort:
    """spec §5: "not a routine operation" — deliberately gated on
    `program.manage` (Institution/Program Administrator), one tier above the
    `section.manage` that Program Coordinator uses for everyday cohort
    CRUD above, and always requires a `reason` recorded in the audit trail.
    """
    cohort = _get_or_404(db, Cohort, cohort_id, "Cohort")
    _get_or_404(db, ProgramVersion, payload.program_version_id, "Program version")
    previous_program_version_id = cohort.program_version_id
    cohort.program_version_id = payload.program_version_id
    db.add(cohort)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="cohort.curriculum_changed",
        entity_type="Cohort",
        entity_id=cohort.id,
        previous_value={"program_version_id": str(previous_program_version_id)},
        new_value={
            "program_version_id": str(payload.program_version_id),
            "reason": payload.reason,
        },
        academic_term_id=cohort.intake_term_id,
        program_version_id=cohort.program_version_id,
        **get_request_context(request),
    )
    return cohort


@router.get("/cohorts/{cohort_id}/students", response_model=list[StudentRead])
def list_cohort_students(
    cohort_id: uuid.UUID,
    db: Session = Depends(get_program_scoped_db),
    _current_user: User = Depends(require_permission("section.view", scope_type="program")),
) -> list[StudentRead]:
    """spec §36: "loading" a cohort surfaces its current member list for the
    coordinator to work with in the current trimester context — cohort
    membership itself isn't a per-term relationship in this data model (a
    student stays in their cohort across terms), so there is nothing to
    "move"; this just lists who is in it right now. Each member's `status`
    is exactly whatever it already was (spec §38: never auto-reactivated
    here)."""
    _get_or_404(db, Cohort, cohort_id, "Cohort")
    profiles = db.query(StudentProfile).filter(StudentProfile.cohort_id == cohort_id).all()
    if not profiles:
        return []
    users_by_id = {
        u.id: u
        for u in db.query(User).filter(User.id.in_([p.user_id for p in profiles])).all()
    }
    return [
        StudentRead(
            user_id=p.user_id,
            email=users_by_id[p.user_id].email,
            full_name=users_by_id[p.user_id].full_name,
            is_active=users_by_id[p.user_id].is_active,
            student_code=p.student_code,
            program_id=p.program_id,
            program_version_id=p.program_version_id,
            batch_year=p.batch_year,
            status=p.status,
        )
        for p in profiles
        if p.user_id in users_by_id
    ]
