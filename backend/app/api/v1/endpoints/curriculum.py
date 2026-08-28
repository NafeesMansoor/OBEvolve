"""CRUD for curriculum/outcomes/mappings (DATABASE_PLAN.md §D/§E):
accreditation frameworks (read-only here), courses & course versions, PEOs,
program outcomes, course outcomes, mapping scales, and CO-PO / PEO-PO
mappings.

Reads require `curriculum.view`; creates require `outcome.create` (curriculum
entities) or `mapping.create` (mapping scales & mapping rows); workflow
advances require `outcome.approve` — never a role-name check
(ARCHITECTURE.md §3). Follows the exact `_get_or_404` / `write_audit_log` /
`WorkflowStatus` advance pattern established in `app/api/v1/endpoints/org.py`.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session, selectinload

from app.db.base import WorkflowStatus
from app.db.tenancy import get_db
from app.middleware.audit import get_request_context
from app.models.tenant.accreditation import (
    AccreditationFramework,
    EngineeringActivity,
    FrameworkPO,
    KnowledgeProfile,
    ProblemAttribute,
)
from app.models.tenant.courses import Course, CourseVersion
from app.models.tenant.identity import User
from app.models.tenant.mappings import (
    CourseOutcomePOMapping,
    MappingScale,
    MappingScaleLevel,
    ProgramOutcomePEOMapping,
)
from app.models.tenant.obe import PEO, BloomLevel, CourseOutcome, ProgramOutcome
from app.schemas.curriculum import (
    AccreditationFrameworkDetailRead,
    AccreditationFrameworkRead,
    BloomLevelRead,
    CourseCreate,
    CourseOutcomeCreate,
    CourseOutcomePOMappingCreate,
    CourseOutcomePOMappingRead,
    CourseOutcomeRead,
    CourseOutcomeUpdate,
    CourseRead,
    CourseUpdate,
    CourseVersionCreate,
    CourseVersionRead,
    EngineeringActivityRead,
    FrameworkPORead,
    KnowledgeProfileRead,
    MappingScaleCreate,
    MappingScaleRead,
    PEOCreate,
    PEORead,
    PEOUpdate,
    ProblemAttributeRead,
    ProgramOutcomeCreate,
    ProgramOutcomePEOMappingCreate,
    ProgramOutcomePEOMappingRead,
    ProgramOutcomeRead,
    ProgramOutcomeUpdate,
)
from app.services.audit import write_audit_log
from app.services.rbac import get_program_scoped_db, require_permission

router = APIRouter()


def _get_or_404(db: Session, model, obj_id: uuid.UUID, label: str):
    obj = db.get(model, obj_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{label} not found")
    return obj


# Valid forward transitions of the shared workflow (ARCHITECTURE.md §4),
# identical to org.py's ProgramVersion transition table.
_NEXT_STATUS: dict[WorkflowStatus, WorkflowStatus] = {
    WorkflowStatus.DRAFT: WorkflowStatus.SUBMITTED,
    WorkflowStatus.SUBMITTED: WorkflowStatus.REVIEWED,
    WorkflowStatus.REVIEWED: WorkflowStatus.APPROVED,
    WorkflowStatus.APPROVED: WorkflowStatus.PUBLISHED,
}


def _advance(
    db: Session,
    request: Request,
    current_user: User,
    obj,
    *,
    entity_type: str,
    action: str,
    approved_by_field: str | None = None,
):
    current_status = WorkflowStatus(obj.status)
    next_status = _NEXT_STATUS.get(current_status)
    if next_status is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"{entity_type} in status {current_status.value!r} cannot be advanced further.",
        )
    previous_value = {"status": current_status.value}
    obj.status = next_status
    if approved_by_field and next_status == WorkflowStatus.APPROVED:
        setattr(obj, approved_by_field, current_user.id)
    db.add(obj)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action=action,
        entity_type=entity_type,
        entity_id=obj.id,
        previous_value=previous_value,
        new_value={"status": next_status.value},
        **get_request_context(request),
    )
    return obj


# --- Accreditation frameworks (read-only) ---
@router.get("/frameworks", response_model=list[AccreditationFrameworkRead])
def list_frameworks(
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("curriculum.view")),
) -> list[AccreditationFramework]:
    return db.query(AccreditationFramework).order_by(AccreditationFramework.name).all()


@router.get("/frameworks/{framework_id}", response_model=AccreditationFrameworkDetailRead)
def get_framework(
    framework_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("curriculum.view")),
) -> AccreditationFramework:
    framework = _get_or_404(db, AccreditationFramework, framework_id, "Accreditation framework")
    framework.framework_pos.sort(key=lambda fpo: fpo.sequence)
    return framework


@router.get("/frameworks/{framework_id}/pos", response_model=list[FrameworkPORead])
def list_framework_pos(
    framework_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("curriculum.view")),
) -> list[FrameworkPO]:
    _get_or_404(db, AccreditationFramework, framework_id, "Accreditation framework")
    return (
        db.query(FrameworkPO)
        .filter(FrameworkPO.framework_id == framework_id)
        .order_by(FrameworkPO.sequence)
        .all()
    )


@router.get(
    "/frameworks/{framework_id}/knowledge-profiles", response_model=list[KnowledgeProfileRead]
)
def list_knowledge_profiles(
    framework_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("curriculum.view")),
) -> list[KnowledgeProfile]:
    _get_or_404(db, AccreditationFramework, framework_id, "Accreditation framework")
    return (
        db.query(KnowledgeProfile)
        .filter(KnowledgeProfile.framework_id == framework_id)
        .order_by(KnowledgeProfile.sequence)
        .all()
    )


@router.get(
    "/frameworks/{framework_id}/problem-attributes", response_model=list[ProblemAttributeRead]
)
def list_problem_attributes(
    framework_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("curriculum.view")),
) -> list[ProblemAttribute]:
    _get_or_404(db, AccreditationFramework, framework_id, "Accreditation framework")
    return (
        db.query(ProblemAttribute)
        .filter(ProblemAttribute.framework_id == framework_id)
        .order_by(ProblemAttribute.sequence)
        .all()
    )


@router.get(
    "/frameworks/{framework_id}/engineering-activities",
    response_model=list[EngineeringActivityRead],
)
def list_engineering_activities(
    framework_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("curriculum.view")),
) -> list[EngineeringActivity]:
    _get_or_404(db, AccreditationFramework, framework_id, "Accreditation framework")
    return (
        db.query(EngineeringActivity)
        .filter(EngineeringActivity.framework_id == framework_id)
        .order_by(EngineeringActivity.sequence)
        .all()
    )


# --- Courses ---
@router.post("/courses", response_model=CourseRead, status_code=status.HTTP_201_CREATED)
def create_course(
    payload: CourseCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("outcome.create")),
) -> Course:
    course = Course(**payload.model_dump())
    db.add(course)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="course.created",
        entity_type="Course",
        entity_id=course.id,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return course


@router.get("/courses", response_model=list[CourseRead])
def list_courses(
    department_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("curriculum.view")),
) -> list[Course]:
    query = db.query(Course)
    if department_id is not None:
        query = query.filter(Course.department_id == department_id)
    return query.order_by(Course.code).all()


@router.get("/courses/{course_id}", response_model=CourseRead)
def get_course(
    course_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("curriculum.view")),
) -> Course:
    return _get_or_404(db, Course, course_id, "Course")


@router.patch("/courses/{course_id}", response_model=CourseRead)
def update_course(
    course_id: uuid.UUID,
    payload: CourseUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("outcome.create")),
) -> Course:
    course = _get_or_404(db, Course, course_id, "Course")
    changes = payload.model_dump(exclude_unset=True)
    previous_value = {field: getattr(course, field) for field in changes}
    for field, value in changes.items():
        setattr(course, field, value)
    db.add(course)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="course.updated",
        entity_type="Course",
        entity_id=course.id,
        previous_value={k: str(v) for k, v in previous_value.items()},
        new_value=payload.model_dump(mode="json", exclude_unset=True),
        **get_request_context(request),
    )
    return course


# --- Course versions ---
@router.post(
    "/course-versions", response_model=CourseVersionRead, status_code=status.HTTP_201_CREATED
)
def create_course_version(
    payload: CourseVersionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("outcome.create")),
) -> CourseVersion:
    _get_or_404(db, Course, payload.course_id, "Course")
    version = CourseVersion(
        **payload.model_dump(), status=WorkflowStatus.DRAFT, created_by=current_user.id
    )
    db.add(version)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="course_version.created",
        entity_type="CourseVersion",
        entity_id=version.id,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return version


@router.get("/course-versions", response_model=list[CourseVersionRead])
def list_course_versions(
    course_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("curriculum.view")),
) -> list[CourseVersion]:
    query = db.query(CourseVersion)
    if course_id is not None:
        query = query.filter(CourseVersion.course_id == course_id)
    return query.order_by(CourseVersion.version_label).all()


@router.get("/course-versions/{version_id}", response_model=CourseVersionRead)
def get_course_version(
    version_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("curriculum.view")),
) -> CourseVersion:
    return _get_or_404(db, CourseVersion, version_id, "Course version")


@router.post("/course-versions/{version_id}/advance", response_model=CourseVersionRead)
def advance_course_version(
    version_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("outcome.approve")),
) -> CourseVersion:
    version = _get_or_404(db, CourseVersion, version_id, "Course version")
    return _advance(
        db,
        request,
        current_user,
        version,
        entity_type="CourseVersion",
        action="course_version.status_changed",
        approved_by_field="approved_by",
    )


# --- PEOs, program outcomes, and the mapping junctions between them all live
# in the per-program schema (docs/adr/0003-schema-per-program.md) — every
# route below needs the `X-Program-Code` header, resolved and authorized by
# get_program_scoped_db (see app.services.rbac.get_program_context) before a
# session bound to that program's schema is ever opened. Course/CourseVersion/
# CourseOutcome/MappingScale routes above stay institution-shared (get_db).
@router.post("/peos", response_model=PEORead, status_code=status.HTTP_201_CREATED)
def create_peo(
    payload: PEOCreate,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("outcome.create", scope_type="program")),
) -> PEO:
    peo = PEO(**payload.model_dump(), status=WorkflowStatus.DRAFT, created_by=current_user.id)
    db.add(peo)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="peo.created",
        entity_type="PEO",
        entity_id=peo.id,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return peo


@router.get("/peos", response_model=list[PEORead])
def list_peos(
    program_version_id: uuid.UUID | None = None,
    db: Session = Depends(get_program_scoped_db),
    _current_user: User = Depends(require_permission("curriculum.view", scope_type="program")),
) -> list[PEO]:
    query = db.query(PEO)
    if program_version_id is not None:
        query = query.filter(PEO.program_version_id == program_version_id)
    return query.order_by(PEO.sequence).all()


@router.get("/peos/{peo_id}", response_model=PEORead)
def get_peo(
    peo_id: uuid.UUID,
    db: Session = Depends(get_program_scoped_db),
    _current_user: User = Depends(require_permission("curriculum.view", scope_type="program")),
) -> PEO:
    return _get_or_404(db, PEO, peo_id, "PEO")


@router.patch("/peos/{peo_id}", response_model=PEORead)
def update_peo(
    peo_id: uuid.UUID,
    payload: PEOUpdate,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("outcome.create", scope_type="program")),
) -> PEO:
    peo = _get_or_404(db, PEO, peo_id, "PEO")
    changes = payload.model_dump(exclude_unset=True)
    previous_value = {field: getattr(peo, field) for field in changes}
    for field, value in changes.items():
        setattr(peo, field, value)
    db.add(peo)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="peo.updated",
        entity_type="PEO",
        entity_id=peo.id,
        previous_value={k: str(v) for k, v in previous_value.items()},
        new_value=payload.model_dump(mode="json", exclude_unset=True),
        **get_request_context(request),
    )
    return peo


@router.post("/peos/{peo_id}/advance", response_model=PEORead)
def advance_peo(
    peo_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("outcome.approve", scope_type="program")),
) -> PEO:
    peo = _get_or_404(db, PEO, peo_id, "PEO")
    return _advance(
        db,
        request,
        current_user,
        peo,
        entity_type="PEO",
        action="peo.status_changed",
        approved_by_field="approved_by",
    )


# --- Program outcomes ---
@router.post(
    "/program-outcomes", response_model=ProgramOutcomeRead, status_code=status.HTTP_201_CREATED
)
def create_program_outcome(
    payload: ProgramOutcomeCreate,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("outcome.create", scope_type="program")),
) -> ProgramOutcome:
    if payload.framework_po_id is not None:
        _get_or_404(db, FrameworkPO, payload.framework_po_id, "Framework PO")
    outcome = ProgramOutcome(**payload.model_dump(), status=WorkflowStatus.DRAFT)
    db.add(outcome)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="program_outcome.created",
        entity_type="ProgramOutcome",
        entity_id=outcome.id,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return outcome


@router.get("/program-outcomes", response_model=list[ProgramOutcomeRead])
def list_program_outcomes(
    program_version_id: uuid.UUID | None = None,
    db: Session = Depends(get_program_scoped_db),
    _current_user: User = Depends(require_permission("curriculum.view", scope_type="program")),
) -> list[ProgramOutcome]:
    query = db.query(ProgramOutcome)
    if program_version_id is not None:
        query = query.filter(ProgramOutcome.program_version_id == program_version_id)
    return query.order_by(ProgramOutcome.sequence).all()


@router.get("/program-outcomes/{program_outcome_id}", response_model=ProgramOutcomeRead)
def get_program_outcome(
    program_outcome_id: uuid.UUID,
    db: Session = Depends(get_program_scoped_db),
    _current_user: User = Depends(require_permission("curriculum.view", scope_type="program")),
) -> ProgramOutcome:
    return _get_or_404(db, ProgramOutcome, program_outcome_id, "Program outcome")


@router.patch("/program-outcomes/{program_outcome_id}", response_model=ProgramOutcomeRead)
def update_program_outcome(
    program_outcome_id: uuid.UUID,
    payload: ProgramOutcomeUpdate,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("outcome.create", scope_type="program")),
) -> ProgramOutcome:
    outcome = _get_or_404(db, ProgramOutcome, program_outcome_id, "Program outcome")
    changes = payload.model_dump(exclude_unset=True)
    if "framework_po_id" in changes and changes["framework_po_id"] is not None:
        _get_or_404(db, FrameworkPO, changes["framework_po_id"], "Framework PO")
    previous_value = {field: getattr(outcome, field) for field in changes}
    for field, value in changes.items():
        setattr(outcome, field, value)
    db.add(outcome)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="program_outcome.updated",
        entity_type="ProgramOutcome",
        entity_id=outcome.id,
        previous_value={k: str(v) for k, v in previous_value.items()},
        new_value=payload.model_dump(mode="json", exclude_unset=True),
        **get_request_context(request),
    )
    return outcome


@router.post("/program-outcomes/{program_outcome_id}/advance", response_model=ProgramOutcomeRead)
def advance_program_outcome(
    program_outcome_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("outcome.approve", scope_type="program")),
) -> ProgramOutcome:
    outcome = _get_or_404(db, ProgramOutcome, program_outcome_id, "Program outcome")
    return _advance(
        db,
        request,
        current_user,
        outcome,
        entity_type="ProgramOutcome",
        action="program_outcome.status_changed",
    )


# --- Bloom levels (read-only catalogue; seeded per institution at creation
# time by app.seed.bloom_defaults — see app/services/tenancy.py) ---
@router.get("/bloom-levels", response_model=list[BloomLevelRead])
def list_bloom_levels(
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("curriculum.view")),
) -> list[BloomLevel]:
    return (
        db.query(BloomLevel)
        .filter(BloomLevel.is_active.is_(True))
        .order_by(BloomLevel.sequence_order)
        .all()
    )


# --- Course outcomes ---
@router.post(
    "/course-outcomes", response_model=CourseOutcomeRead, status_code=status.HTTP_201_CREATED
)
def create_course_outcome(
    payload: CourseOutcomeCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("outcome.create")),
) -> CourseOutcome:
    _get_or_404(db, CourseVersion, payload.course_version_id, "Course version")
    outcome = CourseOutcome(**payload.model_dump(), status=WorkflowStatus.DRAFT)
    db.add(outcome)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="course_outcome.created",
        entity_type="CourseOutcome",
        entity_id=outcome.id,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return outcome


@router.get("/course-outcomes", response_model=list[CourseOutcomeRead])
def list_course_outcomes(
    course_version_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("curriculum.view")),
) -> list[CourseOutcome]:
    query = db.query(CourseOutcome)
    if course_version_id is not None:
        query = query.filter(CourseOutcome.course_version_id == course_version_id)
    return query.order_by(CourseOutcome.sequence).all()


@router.get("/course-outcomes/{course_outcome_id}", response_model=CourseOutcomeRead)
def get_course_outcome(
    course_outcome_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("curriculum.view")),
) -> CourseOutcome:
    return _get_or_404(db, CourseOutcome, course_outcome_id, "Course outcome")


@router.patch("/course-outcomes/{course_outcome_id}", response_model=CourseOutcomeRead)
def update_course_outcome(
    course_outcome_id: uuid.UUID,
    payload: CourseOutcomeUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("outcome.create")),
) -> CourseOutcome:
    outcome = _get_or_404(db, CourseOutcome, course_outcome_id, "Course outcome")
    changes = payload.model_dump(exclude_unset=True)
    previous_value = {field: getattr(outcome, field) for field in changes}
    for field, value in changes.items():
        setattr(outcome, field, value)
    db.add(outcome)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="course_outcome.updated",
        entity_type="CourseOutcome",
        entity_id=outcome.id,
        previous_value={k: str(v) for k, v in previous_value.items()},
        new_value=payload.model_dump(mode="json", exclude_unset=True),
        **get_request_context(request),
    )
    return outcome


@router.post("/course-outcomes/{course_outcome_id}/advance", response_model=CourseOutcomeRead)
def advance_course_outcome(
    course_outcome_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("outcome.approve")),
) -> CourseOutcome:
    outcome = _get_or_404(db, CourseOutcome, course_outcome_id, "Course outcome")
    return _advance(
        db,
        request,
        current_user,
        outcome,
        entity_type="CourseOutcome",
        action="course_outcome.status_changed",
    )


# --- Mapping scales ---
@router.get("/mapping-scales", response_model=list[MappingScaleRead])
def list_mapping_scales(
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("curriculum.view")),
) -> list[MappingScale]:
    scales = (
        db.query(MappingScale)
        .options(selectinload(MappingScale.levels))
        .order_by(MappingScale.name)
        .all()
    )
    for scale in scales:
        scale.levels.sort(key=lambda level: level.sequence)
    return scales


@router.post(
    "/mapping-scales", response_model=MappingScaleRead, status_code=status.HTTP_201_CREATED
)
def create_mapping_scale(
    payload: MappingScaleCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("mapping.create")),
) -> MappingScale:
    scale = MappingScale(name=payload.name, description=payload.description, is_default=False)
    db.add(scale)
    db.flush()
    for level_payload in payload.levels:
        db.add(MappingScaleLevel(mapping_scale_id=scale.id, **level_payload.model_dump()))
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="mapping_scale.created",
        entity_type="MappingScale",
        entity_id=scale.id,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    scale.levels.sort(key=lambda level: level.sequence)
    return scale


# --- CO-PO mappings ---
@router.get("/course-outcome-po-mappings", response_model=list[CourseOutcomePOMappingRead])
def list_course_outcome_po_mappings(
    course_outcome_id: uuid.UUID | None = None,
    program_outcome_id: uuid.UUID | None = None,
    db: Session = Depends(get_program_scoped_db),
    _current_user: User = Depends(require_permission("curriculum.view", scope_type="program")),
) -> list[CourseOutcomePOMapping]:
    if course_outcome_id is None and program_outcome_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one of course_outcome_id or program_outcome_id is required.",
        )
    query = db.query(CourseOutcomePOMapping)
    if course_outcome_id is not None:
        query = query.filter(CourseOutcomePOMapping.course_outcome_id == course_outcome_id)
    if program_outcome_id is not None:
        query = query.filter(CourseOutcomePOMapping.program_outcome_id == program_outcome_id)
    return query.all()


@router.post(
    "/course-outcome-po-mappings",
    response_model=CourseOutcomePOMappingRead,
    status_code=status.HTTP_201_CREATED,
)
def create_course_outcome_po_mapping(
    payload: CourseOutcomePOMappingCreate,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("mapping.create", scope_type="program")),
) -> CourseOutcomePOMapping:
    _get_or_404(db, CourseOutcome, payload.course_outcome_id, "Course outcome")
    _get_or_404(db, ProgramOutcome, payload.program_outcome_id, "Program outcome")
    _get_or_404(db, MappingScaleLevel, payload.mapping_scale_level_id, "Mapping scale level")

    existing = (
        db.query(CourseOutcomePOMapping)
        .filter(
            CourseOutcomePOMapping.course_outcome_id == payload.course_outcome_id,
            CourseOutcomePOMapping.program_outcome_id == payload.program_outcome_id,
        )
        .one_or_none()
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "A mapping already exists for this course_outcome_id/program_outcome_id pair; "
                "delete it and POST a new one to change the level."
            ),
        )

    mapping = CourseOutcomePOMapping(**payload.model_dump())
    db.add(mapping)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="course_outcome_po_mapping.created",
        entity_type="CourseOutcomePOMapping",
        entity_id=mapping.id,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return mapping


@router.delete(
    "/course-outcome-po-mappings/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_course_outcome_po_mapping(
    mapping_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("mapping.create", scope_type="program")),
) -> None:
    mapping = _get_or_404(db, CourseOutcomePOMapping, mapping_id, "CO-PO mapping")
    previous_value = {
        "course_outcome_id": str(mapping.course_outcome_id),
        "program_outcome_id": str(mapping.program_outcome_id),
        "mapping_scale_level_id": str(mapping.mapping_scale_level_id),
    }
    db.delete(mapping)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="course_outcome_po_mapping.deleted",
        entity_type="CourseOutcomePOMapping",
        entity_id=mapping_id,
        previous_value=previous_value,
        **get_request_context(request),
    )


# --- PEO-PO mappings ---
@router.get("/program-outcome-peo-mappings", response_model=list[ProgramOutcomePEOMappingRead])
def list_program_outcome_peo_mappings(
    program_outcome_id: uuid.UUID | None = None,
    peo_id: uuid.UUID | None = None,
    db: Session = Depends(get_program_scoped_db),
    _current_user: User = Depends(require_permission("curriculum.view", scope_type="program")),
) -> list[ProgramOutcomePEOMapping]:
    if program_outcome_id is None and peo_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one of program_outcome_id or peo_id is required.",
        )
    query = db.query(ProgramOutcomePEOMapping)
    if program_outcome_id is not None:
        query = query.filter(ProgramOutcomePEOMapping.program_outcome_id == program_outcome_id)
    if peo_id is not None:
        query = query.filter(ProgramOutcomePEOMapping.peo_id == peo_id)
    return query.all()


@router.post(
    "/program-outcome-peo-mappings",
    response_model=ProgramOutcomePEOMappingRead,
    status_code=status.HTTP_201_CREATED,
)
def create_program_outcome_peo_mapping(
    payload: ProgramOutcomePEOMappingCreate,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("mapping.create", scope_type="program")),
) -> ProgramOutcomePEOMapping:
    _get_or_404(db, ProgramOutcome, payload.program_outcome_id, "Program outcome")
    _get_or_404(db, PEO, payload.peo_id, "PEO")
    _get_or_404(db, MappingScaleLevel, payload.mapping_scale_level_id, "Mapping scale level")

    existing = (
        db.query(ProgramOutcomePEOMapping)
        .filter(
            ProgramOutcomePEOMapping.program_outcome_id == payload.program_outcome_id,
            ProgramOutcomePEOMapping.peo_id == payload.peo_id,
        )
        .one_or_none()
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "A mapping already exists for this program_outcome_id/peo_id pair; "
                "delete it and POST a new one to change the level."
            ),
        )

    mapping = ProgramOutcomePEOMapping(**payload.model_dump())
    db.add(mapping)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="program_outcome_peo_mapping.created",
        entity_type="ProgramOutcomePEOMapping",
        entity_id=mapping.id,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return mapping


@router.delete(
    "/program-outcome-peo-mappings/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_program_outcome_peo_mapping(
    mapping_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("mapping.create", scope_type="program")),
) -> None:
    mapping = _get_or_404(db, ProgramOutcomePEOMapping, mapping_id, "PEO-PO mapping")
    previous_value = {
        "program_outcome_id": str(mapping.program_outcome_id),
        "peo_id": str(mapping.peo_id),
        "mapping_scale_level_id": str(mapping.mapping_scale_level_id),
    }
    db.delete(mapping)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="program_outcome_peo_mapping.deleted",
        entity_type="ProgramOutcomePEOMapping",
        entity_id=mapping_id,
        previous_value=previous_value,
        **get_request_context(request),
    )
