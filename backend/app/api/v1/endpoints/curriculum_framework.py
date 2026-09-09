"""CRUD for the Mission/Vision, Performance Indicator, and PO/PI<->K/CEP/CEA
framework additions (Master_Architecture_Part1.md §7-21).

Split out from `curriculum.py` (which predates this spec) to keep that file
from growing unbounded — same helpers/patterns (`_get_or_404`,
`write_audit_log`, `require_permission`), just a fresh router.

Reads require `curriculum.view`; every write here requires
`program_outcome_framework.manage` — the program-level-framework permission
introduced specifically because Program Coordinator must NOT be able to edit
this layer directly (spec §25/§43: view + feedback only), unlike the
course-level `outcome.create`/`mapping.create` codes `curriculum.py` still
uses for CourseOutcome/CO-PO work. Institutional Mission/Vision are
institution-shared (no scope_type="program" — that would force an irrelevant
X-Program-Code header onto an institution-wide edit); everything else here is
schema="program" and follows the `get_program_scoped_db` + scope_type="program"
pattern already established for PEO/ProgramOutcome in `curriculum.py`.
"""

from __future__ import annotations

import re
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.db.base import WorkflowStatus
from app.db.tenancy import get_db
from app.middleware.audit import get_request_context
from app.models.tenant.curriculum_feedback import ENTITY_TYPES, STATUSES, CurriculumFeedback
from app.models.tenant.identity import User
from app.models.tenant.mappings.framework_mappings import (
    ProgramOutcomeEngineeringActivityMapping,
    ProgramOutcomeKnowledgeProfileMapping,
    ProgramOutcomeProblemAttributeMapping,
)
from app.models.tenant.mappings.scales import CourseOutcomePIMapping
from app.models.tenant.obe.mission_vision import (
    InstitutionalMission,
    InstitutionalVision,
    InstitutionalVisionProgramVisionMapping,
    PeoVisionMapping,
    ProgramMission,
    ProgramVision,
)
from app.models.tenant.obe.outcomes import PEO, PerformanceIndicator, ProgramOutcome
from app.models.tenant.org import ProgramVersion
from app.schemas.curriculum_framework import (
    CourseOutcomePIMappingCreate,
    CourseOutcomePIMappingRead,
    CurriculumFeedbackCreate,
    CurriculumFeedbackRead,
    CurriculumFeedbackReview,
    InstitutionalMissionCreate,
    InstitutionalMissionRead,
    InstitutionalMissionUpdate,
    InstitutionalVisionCreate,
    InstitutionalVisionProgramVisionMappingCreate,
    InstitutionalVisionProgramVisionMappingRead,
    InstitutionalVisionRead,
    InstitutionalVisionUpdate,
    PeoVisionMappingCreate,
    PeoVisionMappingRead,
    PerformanceIndicatorCreate,
    PerformanceIndicatorRead,
    PerformanceIndicatorUpdate,
    ProgramMissionCreate,
    ProgramMissionRead,
    ProgramMissionUpdate,
    ProgramOutcomeEngineeringActivityMappingCreate,
    ProgramOutcomeEngineeringActivityMappingRead,
    ProgramOutcomeKnowledgeProfileMappingCreate,
    ProgramOutcomeKnowledgeProfileMappingRead,
    ProgramOutcomeProblemAttributeMappingCreate,
    ProgramOutcomeProblemAttributeMappingRead,
    ProgramVersionFrameworkConfigRead,
    ProgramVersionFrameworkConfigUpdate,
    ProgramVisionCreate,
    ProgramVisionRead,
    ProgramVisionUpdate,
)
from app.services.audit import write_audit_log
from app.services.rbac import get_program_scoped_db, require_permission

router = APIRouter()

_MANAGE = "program_outcome_framework.manage"


def _get_or_404(db: Session, model, obj_id: uuid.UUID, label: str):
    obj = db.get(model, obj_id)
    if obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{label} not found")
    return obj


def _generate_pi_code(po_code: str, sequence: int) -> str:
    """Derive a PI's code from its parent PO's code + this PI's own sequence
    (spec §18: "must automatically inherit the PO identifier"). Handles the
    spec's own example directly: PO(a) -> PI(a1). A purely numeric PO code
    (PO1) or any other convention falls back to the same bracketed-suffix
    shape so every numbering convention still produces a consistent code.
    """
    match = re.fullmatch(r"PO\((\w+)\)", po_code, flags=re.IGNORECASE)
    if match:
        return f"PI({match.group(1)}{sequence})"
    match = re.fullmatch(r"PO(\d+)", po_code, flags=re.IGNORECASE)
    if match:
        return f"PI({match.group(1)}.{sequence})"
    return f"PI({po_code}.{sequence})"


# --- Institutional mission (institution-shared) ---
@router.post(
    "/institutional-missions",
    response_model=InstitutionalMissionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_institutional_mission(
    payload: InstitutionalMissionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(_MANAGE)),
) -> InstitutionalMission:
    mission = InstitutionalMission(statement=payload.statement, created_by=current_user.id)
    db.add(mission)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="institutional_mission.created",
        entity_type="InstitutionalMission",
        entity_id=mission.id,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return mission


@router.get("/institutional-missions", response_model=list[InstitutionalMissionRead])
def list_institutional_missions(
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("curriculum.view")),
) -> list[InstitutionalMission]:
    return db.query(InstitutionalMission).order_by(InstitutionalMission.created_at).all()


@router.patch("/institutional-missions/{mission_id}", response_model=InstitutionalMissionRead)
def update_institutional_mission(
    mission_id: uuid.UUID,
    payload: InstitutionalMissionUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(_MANAGE)),
) -> InstitutionalMission:
    mission = _get_or_404(db, InstitutionalMission, mission_id, "Institutional mission")
    changes = payload.model_dump(exclude_unset=True)
    previous_value = {field: getattr(mission, field) for field in changes}
    for field, value in changes.items():
        setattr(mission, field, value)
    db.add(mission)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="institutional_mission.updated",
        entity_type="InstitutionalMission",
        entity_id=mission.id,
        previous_value={k: str(v) for k, v in previous_value.items()},
        new_value=payload.model_dump(mode="json", exclude_unset=True),
        **get_request_context(request),
    )
    return mission


# --- Institutional vision (institution-shared) ---
@router.post(
    "/institutional-visions",
    response_model=InstitutionalVisionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_institutional_vision(
    payload: InstitutionalVisionCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(_MANAGE)),
) -> InstitutionalVision:
    vision = InstitutionalVision(**payload.model_dump(), created_by=current_user.id)
    db.add(vision)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="institutional_vision.created",
        entity_type="InstitutionalVision",
        entity_id=vision.id,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return vision


@router.get("/institutional-visions", response_model=list[InstitutionalVisionRead])
def list_institutional_visions(
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("curriculum.view")),
) -> list[InstitutionalVision]:
    return db.query(InstitutionalVision).order_by(InstitutionalVision.sequence).all()


@router.patch("/institutional-visions/{vision_id}", response_model=InstitutionalVisionRead)
def update_institutional_vision(
    vision_id: uuid.UUID,
    payload: InstitutionalVisionUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(_MANAGE)),
) -> InstitutionalVision:
    vision = _get_or_404(db, InstitutionalVision, vision_id, "Institutional vision")
    changes = payload.model_dump(exclude_unset=True)
    previous_value = {field: getattr(vision, field) for field in changes}
    for field, value in changes.items():
        setattr(vision, field, value)
    db.add(vision)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="institutional_vision.updated",
        entity_type="InstitutionalVision",
        entity_id=vision.id,
        previous_value={k: str(v) for k, v in previous_value.items()},
        new_value=payload.model_dump(mode="json", exclude_unset=True),
        **get_request_context(request),
    )
    return vision


# --- Program mission (schema=program) ---
@router.post(
    "/program-missions", response_model=ProgramMissionRead, status_code=status.HTTP_201_CREATED
)
def create_program_mission(
    payload: ProgramMissionCreate,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission(_MANAGE, scope_type="program")),
) -> ProgramMission:
    mission = ProgramMission(**payload.model_dump())
    db.add(mission)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="program_mission.created",
        entity_type="ProgramMission",
        entity_id=mission.id,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return mission


@router.get("/program-missions", response_model=list[ProgramMissionRead])
def list_program_missions(
    program_version_id: uuid.UUID | None = None,
    db: Session = Depends(get_program_scoped_db),
    _current_user: User = Depends(require_permission("curriculum.view", scope_type="program")),
) -> list[ProgramMission]:
    query = db.query(ProgramMission)
    if program_version_id is not None:
        query = query.filter(ProgramMission.program_version_id == program_version_id)
    return query.all()


@router.patch("/program-missions/{mission_id}", response_model=ProgramMissionRead)
def update_program_mission(
    mission_id: uuid.UUID,
    payload: ProgramMissionUpdate,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission(_MANAGE, scope_type="program")),
) -> ProgramMission:
    mission = _get_or_404(db, ProgramMission, mission_id, "Program mission")
    changes = payload.model_dump(exclude_unset=True)
    previous_value = {field: getattr(mission, field) for field in changes}
    for field, value in changes.items():
        setattr(mission, field, value)
    db.add(mission)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="program_mission.updated",
        entity_type="ProgramMission",
        entity_id=mission.id,
        previous_value={k: str(v) for k, v in previous_value.items()},
        new_value=payload.model_dump(mode="json", exclude_unset=True),
        **get_request_context(request),
    )
    return mission


# --- Program vision (schema=program) ---
@router.post(
    "/program-visions", response_model=ProgramVisionRead, status_code=status.HTTP_201_CREATED
)
def create_program_vision(
    payload: ProgramVisionCreate,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission(_MANAGE, scope_type="program")),
) -> ProgramVision:
    vision = ProgramVision(**payload.model_dump())
    db.add(vision)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="program_vision.created",
        entity_type="ProgramVision",
        entity_id=vision.id,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return vision


@router.get("/program-visions", response_model=list[ProgramVisionRead])
def list_program_visions(
    program_version_id: uuid.UUID | None = None,
    db: Session = Depends(get_program_scoped_db),
    _current_user: User = Depends(require_permission("curriculum.view", scope_type="program")),
) -> list[ProgramVision]:
    query = db.query(ProgramVision)
    if program_version_id is not None:
        query = query.filter(ProgramVision.program_version_id == program_version_id)
    return query.order_by(ProgramVision.sequence).all()


@router.patch("/program-visions/{vision_id}", response_model=ProgramVisionRead)
def update_program_vision(
    vision_id: uuid.UUID,
    payload: ProgramVisionUpdate,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission(_MANAGE, scope_type="program")),
) -> ProgramVision:
    vision = _get_or_404(db, ProgramVision, vision_id, "Program vision")
    changes = payload.model_dump(exclude_unset=True)
    previous_value = {field: getattr(vision, field) for field in changes}
    for field, value in changes.items():
        setattr(vision, field, value)
    db.add(vision)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="program_vision.updated",
        entity_type="ProgramVision",
        entity_id=vision.id,
        previous_value={k: str(v) for k, v in previous_value.items()},
        new_value=payload.model_dump(mode="json", exclude_unset=True),
        **get_request_context(request),
    )
    return vision


# --- Institutional Vision <-> Program Vision mapping (spec §9) ---
@router.post(
    "/institutional-vision-program-vision-mappings",
    response_model=InstitutionalVisionProgramVisionMappingRead,
    status_code=status.HTTP_201_CREATED,
)
def create_institutional_vision_program_vision_mapping(
    payload: InstitutionalVisionProgramVisionMappingCreate,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission(_MANAGE, scope_type="program")),
) -> InstitutionalVisionProgramVisionMapping:
    _get_or_404(db, ProgramVision, payload.program_vision_id, "Program vision")
    _get_or_404(db, InstitutionalVision, payload.institutional_vision_id, "Institutional vision")
    mapping = InstitutionalVisionProgramVisionMapping(**payload.model_dump())
    db.add(mapping)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="institutional_vision_program_vision_mapping.created",
        entity_type="InstitutionalVisionProgramVisionMapping",
        entity_id=mapping.id,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return mapping


@router.get(
    "/institutional-vision-program-vision-mappings",
    response_model=list[InstitutionalVisionProgramVisionMappingRead],
)
def list_institutional_vision_program_vision_mappings(
    program_vision_id: uuid.UUID | None = None,
    db: Session = Depends(get_program_scoped_db),
    _current_user: User = Depends(require_permission("curriculum.view", scope_type="program")),
) -> list[InstitutionalVisionProgramVisionMapping]:
    query = db.query(InstitutionalVisionProgramVisionMapping)
    if program_vision_id is not None:
        query = query.filter(
            InstitutionalVisionProgramVisionMapping.program_vision_id == program_vision_id
        )
    return query.all()


@router.delete(
    "/institutional-vision-program-vision-mappings/{mapping_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_institutional_vision_program_vision_mapping(
    mapping_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission(_MANAGE, scope_type="program")),
) -> None:
    mapping = _get_or_404(
        db,
        InstitutionalVisionProgramVisionMapping,
        mapping_id,
        "Institutional/Program vision mapping",
    )
    write_audit_log(
        db,
        user_id=current_user.id,
        action="institutional_vision_program_vision_mapping.deleted",
        entity_type="InstitutionalVisionProgramVisionMapping",
        entity_id=mapping.id,
        previous_value={
            "program_vision_id": str(mapping.program_vision_id),
            "institutional_vision_id": str(mapping.institutional_vision_id),
        },
        **get_request_context(request),
    )
    db.delete(mapping)


# --- PEO <-> Program Vision mapping (spec §11) ---
@router.post(
    "/peo-vision-mappings", response_model=PeoVisionMappingRead, status_code=status.HTTP_201_CREATED
)
def create_peo_vision_mapping(
    payload: PeoVisionMappingCreate,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission(_MANAGE, scope_type="program")),
) -> PeoVisionMapping:
    _get_or_404(db, PEO, payload.peo_id, "PEO")
    _get_or_404(db, ProgramVision, payload.program_vision_id, "Program vision")
    mapping = PeoVisionMapping(**payload.model_dump())
    db.add(mapping)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="peo_vision_mapping.created",
        entity_type="PeoVisionMapping",
        entity_id=mapping.id,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return mapping


@router.get("/peo-vision-mappings", response_model=list[PeoVisionMappingRead])
def list_peo_vision_mappings(
    peo_id: uuid.UUID | None = None,
    program_vision_id: uuid.UUID | None = None,
    db: Session = Depends(get_program_scoped_db),
    _current_user: User = Depends(require_permission("curriculum.view", scope_type="program")),
) -> list[PeoVisionMapping]:
    query = db.query(PeoVisionMapping)
    if peo_id is not None:
        query = query.filter(PeoVisionMapping.peo_id == peo_id)
    if program_vision_id is not None:
        query = query.filter(PeoVisionMapping.program_vision_id == program_vision_id)
    return query.all()


@router.delete("/peo-vision-mappings/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_peo_vision_mapping(
    mapping_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission(_MANAGE, scope_type="program")),
) -> None:
    mapping = _get_or_404(db, PeoVisionMapping, mapping_id, "PEO-vision mapping")
    write_audit_log(
        db,
        user_id=current_user.id,
        action="peo_vision_mapping.deleted",
        entity_type="PeoVisionMapping",
        entity_id=mapping.id,
        previous_value={
            "peo_id": str(mapping.peo_id),
            "program_vision_id": str(mapping.program_vision_id),
        },
        **get_request_context(request),
    )
    db.delete(mapping)


# --- Program version framework configuration (spec §12/§13) ---
@router.patch(
    "/program-versions/{version_id}/framework-config",
    response_model=ProgramVersionFrameworkConfigRead,
)
def update_program_version_framework_config(
    version_id: uuid.UUID,
    payload: ProgramVersionFrameworkConfigUpdate,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission(_MANAGE, scope_type="program")),
) -> ProgramVersion:
    version = _get_or_404(db, ProgramVersion, version_id, "Program version")
    changes = payload.model_dump(exclude_unset=True)
    previous_value = {field: getattr(version, field) for field in changes}
    for field, value in changes.items():
        setattr(version, field, value)
    db.add(version)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="program_version.framework_config_updated",
        entity_type="ProgramVersion",
        entity_id=version.id,
        previous_value=previous_value,
        new_value=changes,
        **get_request_context(request),
    )
    return version


# --- Performance indicators (Indicator-Based method only, spec §18) ---
@router.post(
    "/performance-indicators",
    response_model=PerformanceIndicatorRead,
    status_code=status.HTTP_201_CREATED,
)
def create_performance_indicator(
    payload: PerformanceIndicatorCreate,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission(_MANAGE, scope_type="program")),
) -> PerformanceIndicator:
    program_outcome = _get_or_404(db, ProgramOutcome, payload.program_outcome_id, "Program outcome")
    code = _generate_pi_code(program_outcome.code, payload.sequence)
    indicator = PerformanceIndicator(
        program_outcome_id=payload.program_outcome_id,
        code=code,
        statement=payload.statement,
        sequence=payload.sequence,
        status=WorkflowStatus.DRAFT,
    )
    db.add(indicator)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="performance_indicator.created",
        entity_type="PerformanceIndicator",
        entity_id=indicator.id,
        new_value={**payload.model_dump(mode="json"), "code": code},
        **get_request_context(request),
    )
    return indicator


@router.get("/performance-indicators", response_model=list[PerformanceIndicatorRead])
def list_performance_indicators(
    program_outcome_id: uuid.UUID | None = None,
    program_version_id: uuid.UUID | None = None,
    db: Session = Depends(get_program_scoped_db),
    _current_user: User = Depends(require_permission("curriculum.view", scope_type="program")),
) -> list[PerformanceIndicator]:
    query = db.query(PerformanceIndicator)
    if program_outcome_id is not None:
        query = query.filter(PerformanceIndicator.program_outcome_id == program_outcome_id)
    if program_version_id is not None:
        # Every PI for a whole curriculum at once (e.g. the CO<->PI mapping
        # matrix), rather than requiring one request per PO.
        query = query.join(
            ProgramOutcome, PerformanceIndicator.program_outcome_id == ProgramOutcome.id
        ).filter(ProgramOutcome.program_version_id == program_version_id)
    return query.order_by(PerformanceIndicator.sequence).all()


@router.patch("/performance-indicators/{indicator_id}", response_model=PerformanceIndicatorRead)
def update_performance_indicator(
    indicator_id: uuid.UUID,
    payload: PerformanceIndicatorUpdate,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission(_MANAGE, scope_type="program")),
) -> PerformanceIndicator:
    indicator = _get_or_404(db, PerformanceIndicator, indicator_id, "Performance indicator")
    changes = payload.model_dump(exclude_unset=True)
    previous_value = {field: getattr(indicator, field) for field in changes}
    for field, value in changes.items():
        setattr(indicator, field, value)
    db.add(indicator)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="performance_indicator.updated",
        entity_type="PerformanceIndicator",
        entity_id=indicator.id,
        previous_value={k: str(v) for k, v in previous_value.items()},
        new_value=payload.model_dump(mode="json", exclude_unset=True),
        **get_request_context(request),
    )
    return indicator


@router.post(
    "/performance-indicators/{indicator_id}/advance", response_model=PerformanceIndicatorRead
)
def advance_performance_indicator(
    indicator_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission(_MANAGE, scope_type="program")),
) -> PerformanceIndicator:
    indicator = _get_or_404(db, PerformanceIndicator, indicator_id, "Performance indicator")
    next_status = {
        WorkflowStatus.DRAFT: WorkflowStatus.SUBMITTED,
        WorkflowStatus.SUBMITTED: WorkflowStatus.REVIEWED,
        WorkflowStatus.REVIEWED: WorkflowStatus.APPROVED,
        WorkflowStatus.APPROVED: WorkflowStatus.PUBLISHED,
    }.get(WorkflowStatus(indicator.status))
    if next_status is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Performance indicator in status {indicator.status!r} "
                "cannot be advanced further."
            ),
        )
    previous_value = {"status": indicator.status}
    indicator.status = next_status
    db.add(indicator)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="performance_indicator.status_changed",
        entity_type="PerformanceIndicator",
        entity_id=indicator.id,
        previous_value=previous_value,
        new_value={"status": next_status.value},
        **get_request_context(request),
    )
    return indicator


# --- CO <-> PI mapping (Indicator-Based counterpart of CO<->PO, spec §21) ---
# NOTE: unlike the PO/PI<->K/CEP/CEA mappings below, this endpoint does not
# reject a CO<->PI mapping when the "governing" curriculum is Direct-method —
# `CourseOutcome`/`CourseVersion` are catalog-wide and curriculum-independent
# in the existing data model (only `CourseOffering.program_version_id` ties a
# course to one specific curriculum, and only per academic term), so there is
# no single ProgramVersion to check `po_definition_method` against at the
# catalog level. The frontend (Phase 7) is expected to only present CO<->PI
# in an indicator-based curriculum's own course-configuration context.
@router.post(
    "/course-outcome-pi-mappings",
    response_model=CourseOutcomePIMappingRead,
    status_code=status.HTTP_201_CREATED,
)
def create_course_outcome_pi_mapping(
    payload: CourseOutcomePIMappingCreate,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("mapping.create", scope_type="program")),
) -> CourseOutcomePIMapping:
    _get_or_404(db, PerformanceIndicator, payload.performance_indicator_id, "Performance indicator")
    mapping = CourseOutcomePIMapping(**payload.model_dump())
    db.add(mapping)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="course_outcome_pi_mapping.created",
        entity_type="CourseOutcomePIMapping",
        entity_id=mapping.id,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return mapping


@router.get("/course-outcome-pi-mappings", response_model=list[CourseOutcomePIMappingRead])
def list_course_outcome_pi_mappings(
    course_outcome_id: uuid.UUID | None = None,
    performance_indicator_id: uuid.UUID | None = None,
    db: Session = Depends(get_program_scoped_db),
    _current_user: User = Depends(require_permission("curriculum.view", scope_type="program")),
) -> list[CourseOutcomePIMapping]:
    if course_outcome_id is None and performance_indicator_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one of course_outcome_id or performance_indicator_id is required.",
        )
    query = db.query(CourseOutcomePIMapping)
    if course_outcome_id is not None:
        query = query.filter(CourseOutcomePIMapping.course_outcome_id == course_outcome_id)
    if performance_indicator_id is not None:
        query = query.filter(
            CourseOutcomePIMapping.performance_indicator_id == performance_indicator_id
        )
    return query.all()


@router.delete("/course-outcome-pi-mappings/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course_outcome_pi_mapping(
    mapping_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission("mapping.create", scope_type="program")),
) -> None:
    mapping = _get_or_404(db, CourseOutcomePIMapping, mapping_id, "CO-PI mapping")
    write_audit_log(
        db,
        user_id=current_user.id,
        action="course_outcome_pi_mapping.deleted",
        entity_type="CourseOutcomePIMapping",
        entity_id=mapping.id,
        previous_value={
            "course_outcome_id": str(mapping.course_outcome_id),
            "performance_indicator_id": str(mapping.performance_indicator_id),
        },
        **get_request_context(request),
    )
    db.delete(mapping)


def _require_exactly_one_target(
    program_outcome_id: uuid.UUID | None, performance_indicator_id: uuid.UUID | None
) -> None:
    if (program_outcome_id is None) == (performance_indicator_id is None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Exactly one of program_outcome_id or performance_indicator_id is required.",
        )


# --- PO/PI <-> Knowledge Profile mapping (spec §17/§19) ---
@router.post(
    "/po-knowledge-profile-mappings",
    response_model=ProgramOutcomeKnowledgeProfileMappingRead,
    status_code=status.HTTP_201_CREATED,
)
def create_po_knowledge_profile_mapping(
    payload: ProgramOutcomeKnowledgeProfileMappingCreate,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission(_MANAGE, scope_type="program")),
) -> ProgramOutcomeKnowledgeProfileMapping:
    _require_exactly_one_target(payload.program_outcome_id, payload.performance_indicator_id)
    if payload.program_outcome_id is not None:
        _get_or_404(db, ProgramOutcome, payload.program_outcome_id, "Program outcome")
    if payload.performance_indicator_id is not None:
        _get_or_404(
            db, PerformanceIndicator, payload.performance_indicator_id, "Performance indicator"
        )
    mapping = ProgramOutcomeKnowledgeProfileMapping(**payload.model_dump())
    db.add(mapping)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="po_knowledge_profile_mapping.created",
        entity_type="ProgramOutcomeKnowledgeProfileMapping",
        entity_id=mapping.id,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return mapping


@router.get(
    "/po-knowledge-profile-mappings",
    response_model=list[ProgramOutcomeKnowledgeProfileMappingRead],
)
def list_po_knowledge_profile_mappings(
    program_outcome_id: uuid.UUID | None = None,
    performance_indicator_id: uuid.UUID | None = None,
    db: Session = Depends(get_program_scoped_db),
    _current_user: User = Depends(require_permission("curriculum.view", scope_type="program")),
) -> list[ProgramOutcomeKnowledgeProfileMapping]:
    query = db.query(ProgramOutcomeKnowledgeProfileMapping)
    if program_outcome_id is not None:
        query = query.filter(
            ProgramOutcomeKnowledgeProfileMapping.program_outcome_id == program_outcome_id
        )
    if performance_indicator_id is not None:
        query = query.filter(
            ProgramOutcomeKnowledgeProfileMapping.performance_indicator_id
            == performance_indicator_id
        )
    return query.all()


@router.delete(
    "/po-knowledge-profile-mappings/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_po_knowledge_profile_mapping(
    mapping_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission(_MANAGE, scope_type="program")),
) -> None:
    mapping = _get_or_404(db, ProgramOutcomeKnowledgeProfileMapping, mapping_id, "PO/PI-KP mapping")
    write_audit_log(
        db,
        user_id=current_user.id,
        action="po_knowledge_profile_mapping.deleted",
        entity_type="ProgramOutcomeKnowledgeProfileMapping",
        entity_id=mapping.id,
        previous_value={"knowledge_profile_id": str(mapping.knowledge_profile_id)},
        **get_request_context(request),
    )
    db.delete(mapping)


# --- PO/PI <-> Problem Attribute (CEP) mapping (spec §15/§17/§19) ---
@router.post(
    "/po-problem-attribute-mappings",
    response_model=ProgramOutcomeProblemAttributeMappingRead,
    status_code=status.HTTP_201_CREATED,
)
def create_po_problem_attribute_mapping(
    payload: ProgramOutcomeProblemAttributeMappingCreate,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission(_MANAGE, scope_type="program")),
) -> ProgramOutcomeProblemAttributeMapping:
    _require_exactly_one_target(payload.program_outcome_id, payload.performance_indicator_id)
    if payload.program_outcome_id is not None:
        _get_or_404(db, ProgramOutcome, payload.program_outcome_id, "Program outcome")
    if payload.performance_indicator_id is not None:
        _get_or_404(
            db, PerformanceIndicator, payload.performance_indicator_id, "Performance indicator"
        )
    mapping = ProgramOutcomeProblemAttributeMapping(**payload.model_dump())
    db.add(mapping)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="po_problem_attribute_mapping.created",
        entity_type="ProgramOutcomeProblemAttributeMapping",
        entity_id=mapping.id,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return mapping


@router.get(
    "/po-problem-attribute-mappings",
    response_model=list[ProgramOutcomeProblemAttributeMappingRead],
)
def list_po_problem_attribute_mappings(
    program_outcome_id: uuid.UUID | None = None,
    performance_indicator_id: uuid.UUID | None = None,
    db: Session = Depends(get_program_scoped_db),
    _current_user: User = Depends(require_permission("curriculum.view", scope_type="program")),
) -> list[ProgramOutcomeProblemAttributeMapping]:
    query = db.query(ProgramOutcomeProblemAttributeMapping)
    if program_outcome_id is not None:
        query = query.filter(
            ProgramOutcomeProblemAttributeMapping.program_outcome_id == program_outcome_id
        )
    if performance_indicator_id is not None:
        query = query.filter(
            ProgramOutcomeProblemAttributeMapping.performance_indicator_id
            == performance_indicator_id
        )
    return query.all()


@router.delete(
    "/po-problem-attribute-mappings/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_po_problem_attribute_mapping(
    mapping_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission(_MANAGE, scope_type="program")),
) -> None:
    mapping = _get_or_404(
        db, ProgramOutcomeProblemAttributeMapping, mapping_id, "PO/PI-CEP mapping"
    )
    write_audit_log(
        db,
        user_id=current_user.id,
        action="po_problem_attribute_mapping.deleted",
        entity_type="ProgramOutcomeProblemAttributeMapping",
        entity_id=mapping.id,
        previous_value={"problem_attribute_id": str(mapping.problem_attribute_id)},
        **get_request_context(request),
    )
    db.delete(mapping)


# --- PO/PI <-> Engineering Activity (CEA) mapping (spec §16/§17/§19) ---
@router.post(
    "/po-engineering-activity-mappings",
    response_model=ProgramOutcomeEngineeringActivityMappingRead,
    status_code=status.HTTP_201_CREATED,
)
def create_po_engineering_activity_mapping(
    payload: ProgramOutcomeEngineeringActivityMappingCreate,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission(_MANAGE, scope_type="program")),
) -> ProgramOutcomeEngineeringActivityMapping:
    _require_exactly_one_target(payload.program_outcome_id, payload.performance_indicator_id)
    if payload.program_outcome_id is not None:
        _get_or_404(db, ProgramOutcome, payload.program_outcome_id, "Program outcome")
    if payload.performance_indicator_id is not None:
        _get_or_404(
            db, PerformanceIndicator, payload.performance_indicator_id, "Performance indicator"
        )
    mapping = ProgramOutcomeEngineeringActivityMapping(**payload.model_dump())
    db.add(mapping)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="po_engineering_activity_mapping.created",
        entity_type="ProgramOutcomeEngineeringActivityMapping",
        entity_id=mapping.id,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return mapping


@router.get(
    "/po-engineering-activity-mappings",
    response_model=list[ProgramOutcomeEngineeringActivityMappingRead],
)
def list_po_engineering_activity_mappings(
    program_outcome_id: uuid.UUID | None = None,
    performance_indicator_id: uuid.UUID | None = None,
    db: Session = Depends(get_program_scoped_db),
    _current_user: User = Depends(require_permission("curriculum.view", scope_type="program")),
) -> list[ProgramOutcomeEngineeringActivityMapping]:
    query = db.query(ProgramOutcomeEngineeringActivityMapping)
    if program_outcome_id is not None:
        query = query.filter(
            ProgramOutcomeEngineeringActivityMapping.program_outcome_id == program_outcome_id
        )
    if performance_indicator_id is not None:
        query = query.filter(
            ProgramOutcomeEngineeringActivityMapping.performance_indicator_id
            == performance_indicator_id
        )
    return query.all()


@router.delete(
    "/po-engineering-activity-mappings/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_po_engineering_activity_mapping(
    mapping_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission(_MANAGE, scope_type="program")),
) -> None:
    mapping = _get_or_404(
        db, ProgramOutcomeEngineeringActivityMapping, mapping_id, "PO/PI-CEA mapping"
    )
    write_audit_log(
        db,
        user_id=current_user.id,
        action="po_engineering_activity_mapping.deleted",
        entity_type="ProgramOutcomeEngineeringActivityMapping",
        entity_id=mapping.id,
        previous_value={"engineering_activity_id": str(mapping.engineering_activity_id)},
        **get_request_context(request),
    )
    db.delete(mapping)


# --- Program Coordinator feedback (spec §25-26) ---
# No new "administrator notified" mechanism: `app/api/v1/endpoints/
# notifications.py` deliberately computes its pending-approvals summary live
# from each category's own table rather than writing real `notifications`
# rows (nothing in this codebase does that yet) — see that file's module
# docstring. `get_pending_approvals` there is extended to add an "open
# curriculum feedback" count for `program_outcome_framework.manage` holders,
# matching that same pattern instead of introducing a new one.
@router.post(
    "/curriculum-feedback",
    response_model=CurriculumFeedbackRead,
    status_code=status.HTTP_201_CREATED,
)
def create_curriculum_feedback(
    payload: CurriculumFeedbackCreate,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(
        require_permission("curriculum_feedback.create", scope_type="program")
    ),
) -> CurriculumFeedback:
    if payload.entity_type not in ENTITY_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"entity_type must be one of {sorted(ENTITY_TYPES)}",
        )
    feedback = CurriculumFeedback(
        entity_type=payload.entity_type,
        entity_id=payload.entity_id,
        comment=payload.comment,
        status="open",
        submitted_by=current_user.id,
    )
    db.add(feedback)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="curriculum_feedback.submitted",
        entity_type="CurriculumFeedback",
        entity_id=feedback.id,
        new_value=payload.model_dump(mode="json"),
        **get_request_context(request),
    )
    return feedback


@router.get("/curriculum-feedback", response_model=list[CurriculumFeedbackRead])
def list_curriculum_feedback(
    entity_type: str | None = None,
    entity_id: uuid.UUID | None = None,
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_program_scoped_db),
    _current_user: User = Depends(require_permission("curriculum.view", scope_type="program")),
) -> list[CurriculumFeedback]:
    query = db.query(CurriculumFeedback)
    if entity_type is not None:
        query = query.filter(CurriculumFeedback.entity_type == entity_type)
    if entity_id is not None:
        query = query.filter(CurriculumFeedback.entity_id == entity_id)
    if status_filter is not None:
        query = query.filter(CurriculumFeedback.status == status_filter)
    return query.order_by(CurriculumFeedback.created_at.desc()).all()


@router.post("/curriculum-feedback/{feedback_id}/review", response_model=CurriculumFeedbackRead)
def review_curriculum_feedback(
    feedback_id: uuid.UUID,
    payload: CurriculumFeedbackReview,
    request: Request,
    db: Session = Depends(get_program_scoped_db),
    current_user: User = Depends(require_permission(_MANAGE, scope_type="program")),
) -> CurriculumFeedback:
    feedback = _get_or_404(db, CurriculumFeedback, feedback_id, "Curriculum feedback")
    if payload.status not in STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"status must be one of {STATUSES}"
        )
    previous_value = {"status": feedback.status}
    feedback.status = payload.status
    feedback.review_note = payload.review_note
    feedback.reviewed_by = current_user.id
    feedback.reviewed_at = datetime.now(UTC)
    db.add(feedback)
    db.flush()
    write_audit_log(
        db,
        user_id=current_user.id,
        action="curriculum_feedback.reviewed",
        entity_type="CurriculumFeedback",
        entity_id=feedback.id,
        previous_value=previous_value,
        new_value={"status": payload.status, "review_note": payload.review_note},
        **get_request_context(request),
    )
    return feedback
