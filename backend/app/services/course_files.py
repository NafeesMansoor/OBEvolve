"""Course Files (Faculty Module spec §5-9): resolving which documents apply
to a given section and which requirement rule (if any) governs each one.

`CourseFileRequirement` supports three targeting scopes at once
(`program_version_id`, `course_type`, `course_version_id`) — "most specific
wins" when more than one rule could apply to the same file type in the same
term: a `course_version_id` match beats a `course_type` match beats a
`program_version_id` (holistic) match. This is what lets an administrator
set one common rule for "all courses" and then override it for a specific
course, per spec §8.1.
"""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.tenant.course_files import (
    CourseFileRequirement,
    CourseFileSubmission,
    CourseFileType,
)
from app.models.tenant.courses.catalog import Course, CourseVersion
from app.models.tenant.courses.delivery import CourseOffering, CourseSection
from app.schemas.course_files import CourseFileChecklistItem


def _section_context(
    db: Session, course_section_id: uuid.UUID
) -> tuple[uuid.UUID, uuid.UUID, uuid.UUID | None, str]:
    """Returns (academic_term_id, course_version_id, program_version_id,
    delivery_format) for a section."""
    section = db.get(CourseSection, course_section_id)
    if section is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Course section not found")
    offering = db.get(CourseOffering, section.course_offering_id)
    if offering is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Course offering not found")
    course_version = db.get(CourseVersion, offering.course_version_id)
    course = db.get(Course, course_version.course_id) if course_version else None
    delivery_format = course.delivery_format if course else "theory"
    return offering.academic_term_id, offering.course_version_id, offering.program_version_id, (
        delivery_format
    )


def resolve_requirements(
    db: Session, course_section_id: uuid.UUID
) -> list[CourseFileChecklistItem]:
    academic_term_id, course_version_id, program_version_id, delivery_format = _section_context(
        db, course_section_id
    )

    file_types = (
        db.query(CourseFileType)
        .filter(CourseFileType.applicable_course_type.in_([delivery_format, "both"]))
        .order_by(CourseFileType.category, CourseFileType.name)
        .all()
    )

    requirements = (
        db.query(CourseFileRequirement)
        .filter(CourseFileRequirement.academic_term_id == academic_term_id)
        .all()
    )
    by_course_version: dict[uuid.UUID, CourseFileRequirement] = {}
    by_course_type: dict[str, CourseFileRequirement] = {}
    by_program: dict[uuid.UUID, CourseFileRequirement] = {}
    for req in requirements:
        if req.course_version_id is not None:
            by_course_version.setdefault((req.course_version_id, req.course_file_type_id), req)
        elif req.course_type is not None:
            by_course_type.setdefault((req.course_type, req.course_file_type_id), req)
        elif req.program_version_id is not None:
            by_program.setdefault((req.program_version_id, req.course_file_type_id), req)

    submissions_by_type = {
        s.course_file_type_id: s
        for s in db.query(CourseFileSubmission).filter(
            CourseFileSubmission.course_section_id == course_section_id
        )
    }

    items: list[CourseFileChecklistItem] = []
    for file_type in file_types:
        requirement = (
            by_course_version.get((course_version_id, file_type.id))
            or by_course_type.get((delivery_format, file_type.id))
            or (
                by_program.get((program_version_id, file_type.id))
                if program_version_id is not None
                else None
            )
        )
        items.append(
            CourseFileChecklistItem(
                file_type=file_type,
                requirement=requirement,
                submission=submissions_by_type.get(file_type.id),
            )
        )
    return items


def import_requirements(
    db: Session, from_academic_term_id: uuid.UUID, to_academic_term_id: uuid.UUID
) -> list[CourseFileRequirement]:
    """Copies every requirement rule from one term to another (spec §9),
    leaving the source term's rows untouched. Skips (course_file_type_id +
    scope) combinations that already exist in the target term, so this is
    safe to re-run without duplicating rows."""
    source_rows = (
        db.query(CourseFileRequirement)
        .filter(CourseFileRequirement.academic_term_id == from_academic_term_id)
        .all()
    )
    existing_keys = {
        (r.course_file_type_id, r.program_version_id, r.course_type, r.course_version_id)
        for r in db.query(CourseFileRequirement).filter(
            CourseFileRequirement.academic_term_id == to_academic_term_id
        )
    }
    created: list[CourseFileRequirement] = []
    for row in source_rows:
        key = (
            row.course_file_type_id,
            row.program_version_id,
            row.course_type,
            row.course_version_id,
        )
        if key in existing_keys:
            continue
        new_row = CourseFileRequirement(
            academic_term_id=to_academic_term_id,
            course_file_type_id=row.course_file_type_id,
            program_version_id=row.program_version_id,
            course_type=row.course_type,
            course_version_id=row.course_version_id,
            is_required=row.is_required,
            deadline=None,  # a copied deadline from a past term is never meaningful
            soft_copy_required=row.soft_copy_required,
            hard_copy_required=row.hard_copy_required,
        )
        db.add(new_row)
        created.append(new_row)
    db.flush()
    return created
