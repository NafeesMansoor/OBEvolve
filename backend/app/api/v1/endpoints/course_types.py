"""Course Types and their per-program section configuration
(docs/course_level_settings_and_approval_workflow.md §1-§3).

`CourseType` itself is tenant-shared (queried via plain `get_db`); its
per-section enablement is program-scoped (`get_program_scoped_db`) — see
`app.models.tenant.course_type_config.CourseTypeSectionConfig`'s docstring
for why. Every endpoint here still requires an `X-Program-Code` header
(via `require_permission(..., scope_type="program")` / `get_program_scoped_db`,
both of which depend on `get_program_context`) since course types are, in
practice, administered from within one program's Course-Level Settings
screen even though the catalog rows themselves are institution-wide.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.tenancy import get_db
from app.models.tenant.course_type_config import SECTION_KEYS, CourseTypeSectionConfig
from app.models.tenant.courses.catalog import CourseType
from app.models.tenant.identity import User
from app.schemas.course_types import (
    CourseTypeCreate,
    CourseTypeRead,
    SectionConfigRead,
    SectionConfigUpdate,
)
from app.services.course_type_config import resolve_section_config
from app.services.rbac import get_program_scoped_db, require_permission

router = APIRouter()


def _get_or_404(db: Session, course_type_id: uuid.UUID) -> CourseType:
    obj = db.get(CourseType, course_type_id)
    if obj is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Course type not found")
    return obj


@router.get("", response_model=list[CourseTypeRead])
def list_course_types(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("curriculum.view", scope_type="program")),
) -> list[CourseType]:
    query = db.query(CourseType)
    if not include_inactive:
        query = query.filter(CourseType.is_active.is_(True))
    return query.order_by(CourseType.name).all()


@router.post("", response_model=CourseTypeRead, status_code=status.HTTP_201_CREATED)
def create_course_type(
    payload: CourseTypeCreate,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("course_type.manage", scope_type="program")),
) -> CourseType:
    course_type = CourseType(**payload.model_dump())
    db.add(course_type)
    db.flush()
    return course_type


@router.post("/{course_type_id}/deactivate", response_model=CourseTypeRead)
def deactivate_course_type(
    course_type_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("course_type.manage", scope_type="program")),
) -> CourseType:
    """Never a hard delete (spec §1: don't destroy historical course data
    tied to a retired type) — courses classified under this type keep their
    `course_type_id` reference; it just stops appearing in the active list
    and its section config no longer grants any teacher edit access."""
    course_type = _get_or_404(db, course_type_id)
    course_type.is_active = False
    db.add(course_type)
    db.flush()
    return course_type


@router.post("/{course_type_id}/reactivate", response_model=CourseTypeRead)
def reactivate_course_type(
    course_type_id: uuid.UUID,
    db: Session = Depends(get_db),
    _current_user: User = Depends(require_permission("course_type.manage", scope_type="program")),
) -> CourseType:
    course_type = _get_or_404(db, course_type_id)
    course_type.is_active = True
    db.add(course_type)
    db.flush()
    return course_type


@router.get("/{course_type_id}/section-config", response_model=list[SectionConfigRead])
def get_section_config(
    course_type_id: uuid.UUID,
    db: Session = Depends(get_program_scoped_db),
    _current_user: User = Depends(require_permission("curriculum.view", scope_type="program")),
) -> list[SectionConfigRead]:
    existing = {
        row.section_key: row.is_enabled
        for row in db.query(CourseTypeSectionConfig)
        .filter(CourseTypeSectionConfig.course_type_id == course_type_id)
        .all()
    }
    return [
        SectionConfigRead(section_key=key, is_enabled=existing.get(key, False))
        for key in SECTION_KEYS
    ]


@router.put("/{course_type_id}/section-config/{section_key}", response_model=SectionConfigRead)
def update_section_config(
    course_type_id: uuid.UUID,
    section_key: str,
    payload: SectionConfigUpdate,
    db: Session = Depends(get_program_scoped_db),
    _current_user: User = Depends(require_permission("course_type.manage", scope_type="program")),
) -> CourseTypeSectionConfig:
    if section_key not in SECTION_KEYS:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=f"Unknown section: {section_key}")
    row = (
        db.query(CourseTypeSectionConfig)
        .filter(
            CourseTypeSectionConfig.course_type_id == course_type_id,
            CourseTypeSectionConfig.section_key == section_key,
        )
        .one_or_none()
    )
    if row is None:
        row = CourseTypeSectionConfig(course_type_id=course_type_id, section_key=section_key)
    row.is_enabled = payload.is_enabled
    db.add(row)
    db.flush()
    return row


@router.get("/resolve/{course_section_id}", response_model=dict[str, bool])
def resolve_section_config_for_section(
    course_section_id: uuid.UUID,
    db: Session = Depends(get_program_scoped_db),
    _current_user: User = Depends(require_permission("section.view", scope_type="program")),
) -> dict[str, bool]:
    """`{section_key: is_enabled}` for the course this section belongs to —
    what `CourseManagementPage` calls to decide which Edit buttons to show
    (spec §3)."""
    return resolve_section_config(db, course_section_id)
