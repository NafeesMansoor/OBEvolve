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
from app.db.tenancy import get_db
from app.middleware.audit import get_request_context
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
from app.services.rbac import require_permission

router = APIRouter()


def _get_or_404(db: Session, model, obj_id: uuid.UUID, label: str):
    obj = db.get(model, obj_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{label} not found")
    return obj


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
    _current_user: User = Depends(require_permission("org.view")),
) -> list[Campus]:
    return db.query(Campus).order_by(Campus.name).all()


@router.get("/campuses/{campus_id}", response_model=CampusRead)
def get_campus(
    campus_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("org.view")),
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
    _current_user: User = Depends(require_permission("org.view")),
) -> list[School]:
    return db.query(School).order_by(School.name).all()


@router.get("/schools/{school_id}", response_model=SchoolRead)
def get_school(
    school_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("org.view")),
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
    _current_user: User = Depends(require_permission("org.view")),
) -> list[Department]:
    return db.query(Department).order_by(Department.name).all()


@router.get("/departments/{department_id}", response_model=DepartmentRead)
def get_department(
    department_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("org.view")),
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
    _current_user: User = Depends(require_permission("program.view")),
) -> list[Program]:
    return db.query(Program).order_by(Program.name).all()


@router.get("/programs/{program_id}", response_model=ProgramRead)
def get_program(
    program_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("program.view")),
) -> Program:
    return _get_or_404(db, Program, program_id, "Program")


# --- Program versions ---
@router.post(
    "/program-versions", response_model=ProgramVersionRead, status_code=status.HTTP_201_CREATED
)
def create_program_version(
    payload: ProgramVersionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("program.manage")),
) -> ProgramVersion:
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
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("program.view")),
) -> list[ProgramVersion]:
    return db.query(ProgramVersion).order_by(ProgramVersion.version_label).all()


@router.get("/program-versions/{version_id}", response_model=ProgramVersionRead)
def get_program_version(
    version_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("program.view")),
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
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("program.approve")),
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
    _current_user: User = Depends(require_permission("academic_calendar.view")),
) -> list[AcademicYear]:
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
    _current_user: User = Depends(require_permission("academic_calendar.view")),
) -> list[AcademicTerm]:
    return db.query(AcademicTerm).order_by(AcademicTerm.start_date.desc()).all()
