"""Course-Level Settings gating + auto-apply
(docs/course_level_settings_and_approval_workflow.md).

Two independent jobs live here:

1. `ensure_section_enabled` — the write-side gate. A Course Teacher may only
   submit a change for `section_key` if the section's `Course.course_type_id`
   has that section enabled in the *current program's*
   `CourseTypeSectionConfig` (an unclassified course, or one with no config
   row at all, is treated as fully locked — a safe default, not an
   oversight). Mirrors `app.services.faculty_scope.ensure_assigned_to_section`
   in shape/placement: called once the target section id is known, before
   any write.

2. `SECTION_APPROVAL_TIERS` + `apply_change_request` — once a
   `CourseChangeRequest` reaches its terminal "approved" status, this is
   what actually writes the change into the real data (spec §5: "Once
   accepted, the changes become the current course data"). One handler per
   `section_key`/`target_field` combination, registered in
   `_APPLIERS`, keeps each write shape-aware instead of a blind JSON patch —
   see `app.models.tenant.change_requests`' module docstring for why that
   matters. A handler that can't safely apply a given `target_field`
   (`grading_policy` — a course has no owning FK to rewrite, see that
   branch below) records `apply_status="skipped"` rather than guessing at
   new schema/semantics; the existing manual admin-UI edit remains the
   fallback for that one case, unchanged from before this feature.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.tenant.assessments.assessment import Assessment
from app.models.tenant.change_requests import CourseChangeRequest
from app.models.tenant.course_type_config import SECTION_KEYS, CourseTypeSectionConfig
from app.models.tenant.courses.catalog import Course, CourseVersion
from app.models.tenant.courses.delivery import CourseOffering, CourseSection, StudentEnrollment
from app.models.tenant.obe.outcomes import CourseOutcome

# overview/students: Course Teacher -> Course Administrator -> final.
# settings/assessments: Course Teacher -> Course Administrator -> Program
# Coordinator -> final. Fixed by the spec (§5), not admin-configurable.
SECTION_APPROVAL_TIERS: dict[str, int] = {
    "overview": 1,
    "students": 1,
    "settings": 2,
    "assessments": 2,
}


def _resolve_course(db: Session, course_section_id: uuid.UUID) -> Course | None:
    row = _resolve_course_and_version(db, course_section_id)
    return row[0] if row else None


def _resolve_course_and_version(
    db: Session, course_section_id: uuid.UUID
) -> tuple[Course, CourseVersion] | None:
    """The specific `CourseVersion` this section was actually offered
    under (via its `CourseOffering.course_version_id`) — not an arbitrary
    pick off `Course.versions`, which may hold multiple/historical
    versions in no guaranteed order."""
    row = (
        db.query(Course, CourseVersion)
        .join(CourseVersion, CourseVersion.course_id == Course.id)
        .join(CourseOffering, CourseOffering.course_version_id == CourseVersion.id)
        .join(CourseSection, CourseSection.course_offering_id == CourseOffering.id)
        .filter(CourseSection.id == course_section_id)
        .one_or_none()
    )
    return (row[0], row[1]) if row is not None else None


def resolve_section_config(db: Session, course_section_id: uuid.UUID) -> dict[str, bool]:
    """`{section_key: is_enabled}` for every `SECTION_KEYS` entry, for the
    course this section belongs to — the read-side counterpart of
    `ensure_section_enabled`, for the frontend to decide which Edit buttons
    to show (spec §3) without a 403 round-trip per section. An unclassified
    course (or one with no config rows yet) resolves to all-disabled."""
    result = dict.fromkeys(SECTION_KEYS, False)
    course = _resolve_course(db, course_section_id)
    if course is None or course.course_type_id is None:
        return result
    rows = (
        db.query(CourseTypeSectionConfig.section_key, CourseTypeSectionConfig.is_enabled)
        .filter(CourseTypeSectionConfig.course_type_id == course.course_type_id)
        .all()
    )
    result.update({key: enabled for key, enabled in rows})  # noqa: C416 - dict(rows) fails mypy on Row[]
    return result


def ensure_section_enabled(db: Session, course_section_id: uuid.UUID, section_key: str) -> None:
    """403s unless `section_key` is enabled for this section's course type
    in the caller's current program schema. Call before creating a
    `CourseChangeRequest` (or, for `students`, before any enrollment write)."""
    course = _resolve_course(db, course_section_id)
    if course is None or course.course_type_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"'{section_key}' is not enabled for this course (no course type assigned)",
        )
    is_enabled = (
        db.query(CourseTypeSectionConfig.is_enabled)
        .filter(
            CourseTypeSectionConfig.course_type_id == course.course_type_id,
            CourseTypeSectionConfig.section_key == section_key,
        )
        .scalar()
    )
    if not is_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"'{section_key}' is not enabled for this course's course type",
        )


def ensure_direct_enrollment_write_allowed(is_section_authority: bool) -> None:
    """Enrollment writes (spec §2/§4/§11) move from direct-write to
    submit-for-approval for a personally-assigned Course Teacher once
    "Students" is a gated section — only a section authority (Program
    Coordinator, Program/Course Administrator, via
    `app.services.faculty_scope.is_section_authority`) may still write the
    roster directly, mirroring how Course Overview/Settings already work:
    the admin/coordinator tier finalizes directly, the teacher tier
    proposes. Call from every enrollment create/update/delete endpoint
    *instead of* letting a `student.manage` grant write straight through."""
    if is_section_authority:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=(
            "Enrollment changes for an assigned section must be submitted as a "
            "course change request (section_key='students') for approval."
        ),
    )


# --- Apply-on-final-approval ---

_SCALAR_TARGETS: dict[str, tuple[type, str]] = {
    "description": (Course, "description"),
    "objectives": (CourseVersion, "objectives"),
    "tla_mapping": (CourseVersion, "tla_items"),
    "learning_materials": (CourseVersion, "learning_materials"),
    "weights": (CourseVersion, "target_assessment_weights"),
}

#: Every target_field `compute_import_preview` knows how to diff — the
#: "settings"-section scalar fields plus "outcomes" (relational), matching
#: `_SCALAR_TARGETS`/`_apply_outcomes` exactly so a confirmed preview can be
#: submitted through the normal `POST /course-change-requests` path
#: unchanged (spec §10: import is "propose, then approve," not a direct
#: write — see `apply_change_request` below for what eventually applies it).
IMPORTABLE_TARGET_FIELDS: tuple[str, ...] = (*_SCALAR_TARGETS, "outcomes")


def compute_import_preview(
    db: Session, course_section_id: uuid.UUID, source_course_version_id: uuid.UUID
) -> dict[str, dict[str, object]]:
    """`{target_field: {"current_value": ..., "proposed_value": ...}}` for
    every field in `IMPORTABLE_TARGET_FIELDS` — the read-only "review what
    will be imported before confirming" step spec §10 asks for. Never
    writes anything; the caller reviews this, then submits whichever fields
    they want via the normal change-request create endpoint using this
    dict's `proposed_value` verbatim as `proposed_value_json`.
    """
    resolved = _resolve_course_and_version(db, course_section_id)
    if resolved is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Course section not found")
    target_course, target_version = resolved

    source_version = db.get(CourseVersion, source_course_version_id)
    if source_version is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Source course version not found")
    source_course = db.get(Course, source_version.course_id)
    assert source_course is not None  # FK guarantees this

    preview: dict[str, dict[str, object]] = {}
    for target_field, (model, attr) in _SCALAR_TARGETS.items():
        source_obj = source_course if model is Course else source_version
        current_obj = target_course if model is Course else target_version
        preview[target_field] = {
            "current_value": {"value": getattr(current_obj, attr)},
            "proposed_value": {"value": getattr(source_obj, attr)},
        }

    def _outcome_rows(course_version_id: uuid.UUID) -> list[dict[str, object]]:
        rows = (
            db.query(CourseOutcome)
            .filter(
                CourseOutcome.course_version_id == course_version_id,
                CourseOutcome.is_active.is_(True),
            )
            .order_by(CourseOutcome.sequence)
            .all()
        )
        return [
            {
                "code": co.code,
                "statement": co.statement,
                "sequence": co.sequence,
                "delivery_methods": co.delivery_methods,
                "assessment_tools": co.assessment_tools,
            }
            for co in rows
        ]

    preview["outcomes"] = {
        "current_value": {"outcomes": _outcome_rows(target_version.id)},
        "proposed_value": {"outcomes": _outcome_rows(source_version.id)},
    }
    return preview


def _apply_scalar(db: Session, change: CourseChangeRequest, value: dict) -> None:
    model, attr = _SCALAR_TARGETS[change.target_field]
    resolved = _resolve_course_and_version(db, change.course_section_id)
    if resolved is None:
        raise ValueError("course section no longer resolves to a course")
    course, course_version = resolved
    target = course if model is Course else course_version
    setattr(target, attr, value.get("value"))
    db.add(target)


def _apply_outcomes(db: Session, change: CourseChangeRequest, value: dict) -> None:
    outcomes = value.get("outcomes")
    if not isinstance(outcomes, list) or not outcomes:
        # A free-text proposal (e.g. CourseSettingsTab's "Course outcomes"
        # Edit button sends {"value": "<free text>"}, no "outcomes" key at
        # all) can't be safely turned into CourseOutcome rows — silently
        # upserting an empty list here would look like it applied
        # successfully while doing nothing. Only a structured proposal
        # (currently: the import-preview flow) auto-applies; a free-text
        # one needs the same manual admin follow-through as grading_policy.
        raise ValueError(
            "This proposal isn't in a structured format course outcomes can be "
            "applied from automatically — apply it manually via Course Outcomes."
        )
    resolved = _resolve_course_and_version(db, change.course_section_id)
    if resolved is None:
        raise ValueError("course section no longer resolves to a course")
    _course, course_version = resolved
    existing = {
        co.code: co
        for co in db.query(CourseOutcome)
        .filter(CourseOutcome.course_version_id == course_version.id)
        .all()
    }
    for row in outcomes:
        co = existing.get(row["code"])
        if co is None:
            co = CourseOutcome(course_version_id=course_version.id, code=row["code"], sequence=0)
        co.statement = row.get("statement", co.statement if co.statement else "")
        co.sequence = row.get("sequence", co.sequence)
        co.delivery_methods = row.get("delivery_methods")
        co.assessment_tools = row.get("assessment_tools")
        db.add(co)


def _apply_enrollment(db: Session, change: CourseChangeRequest, value: dict) -> None:
    action = value.get("action")
    if action == "add":
        db.add(
            StudentEnrollment(
                student_user_id=uuid.UUID(value["student_user_id"]),
                course_section_id=change.course_section_id,
                enrollment_status="enrolled",
            )
        )
    elif action in {"drop", "update_status"}:
        enrollment = db.get(StudentEnrollment, uuid.UUID(value["enrollment_id"]))
        if enrollment is None:
            raise ValueError("enrollment no longer exists")
        enrollment.enrollment_status = value.get(
            "status", "withdrawn" if action == "drop" else enrollment.enrollment_status
        )
        db.add(enrollment)
    else:
        raise ValueError(f"unknown enrollment action {action!r}")


def _apply_assessment_details(db: Session, change: CourseChangeRequest, value: dict) -> None:
    assessment = db.get(Assessment, uuid.UUID(value["assessment_id"]))
    if assessment is None:
        raise ValueError("assessment no longer exists")
    for field in ("title", "max_marks", "weight", "duration_minutes"):
        if field in value:
            setattr(assessment, field, value[field])
    db.add(assessment)


_APPLIERS: dict[str, Callable[[Session, CourseChangeRequest, dict], None]] = {
    "description": _apply_scalar,
    "objectives": _apply_scalar,
    "tla_mapping": _apply_scalar,
    "learning_materials": _apply_scalar,
    "weights": _apply_scalar,
    "outcomes": _apply_outcomes,
    "enrollment_add": _apply_enrollment,
    "enrollment_drop": _apply_enrollment,
    "enrollment_status": _apply_enrollment,
    "assessment_details": _apply_assessment_details,
}


def apply_change_request(db: Session, change: CourseChangeRequest) -> None:
    """Writes `change`'s final value into the real target data and stamps
    `apply_status`/`apply_error` accordingly. Call only once a request has
    just reached its terminal "approved" status. Never raises — a failed
    apply is recorded on the row (visible to the approver/teacher), not
    surfaced as a 500, since the approval itself already succeeded."""
    value = (
        change.edited_value_json
        if change.edited_value_json is not None
        else change.proposed_value_json
    )
    applier = _APPLIERS.get(change.target_field)
    if applier is None:
        change.apply_status = "skipped"
        change.apply_error = f"No automatic apply handler for target_field={change.target_field!r}"
        return
    try:
        applier(db, change, value)
    except Exception as exc:  # noqa: BLE001 - recorded on the row, not raised
        change.apply_status = "failed"
        change.apply_error = str(exc)
        return
    change.apply_status = "applied"
    change.apply_error = None


if set(SECTION_APPROVAL_TIERS) != set(SECTION_KEYS):
    raise RuntimeError("SECTION_APPROVAL_TIERS and SECTION_KEYS have drifted apart")
