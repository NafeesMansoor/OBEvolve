"""Loads the fixed default `assessment_types` catalogue into a tenant schema.
Idempotent — safe to call against a schema that already has some or all rows
(check-by-name pattern, mirrors `app.seed.default_permissions`)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.tenant.assessments import AssessmentType

DEFAULT_ASSESSMENT_TYPE_NAMES: list[str] = [
    "Quiz",
    "Class Test",
    "Assignment",
    "Lab",
    "Project",
    "Presentation",
    "Midterm",
    "Final Exam",
    "Viva",
    "Seminar",
    "Practical",
    "Complex Engineering Problem",
    "Class Participation",
]


def seed_default_assessment_types(db: Session) -> dict[str, AssessmentType]:
    """Insert any catalogue assessment types missing from this schema.

    Returns a `name -> AssessmentType` map (including pre-existing rows).
    """
    existing = {at.name: at for at in db.query(AssessmentType).all()}
    for name in DEFAULT_ASSESSMENT_TYPE_NAMES:
        if name in existing:
            continue
        assessment_type = AssessmentType(name=name, is_custom=False)
        db.add(assessment_type)
        existing[name] = assessment_type
    db.flush()
    return existing
