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
    "Open-Ended Lab Problem",
    "Class Participation",
]

# These types require the exam-office document set (question paper,
# moderation form, compliance form, highest/lowest/median scripts —
# AssessmentDocument) before they're considered complete. A type-level flag
# rather than name-matching at query time, so it survives renames and
# institutions can opt custom types in too.
DOCUMENT_REQUIRED_TYPE_NAMES: set[str] = {"Midterm", "Final Exam"}

# This type requires the CEP-specific document set (problem definition,
# marked-rubric sample, project reports).
CEP_DOCUMENT_REQUIRED_TYPE_NAMES: set[str] = {"Complex Engineering Problem"}

# This type requires Open-Ended Problem validation on advance (CO-mapping
# completeness, no PO/KPA requirement — see requires_oep_validation).
OEP_VALIDATION_TYPE_NAMES: set[str] = {"Open-Ended Lab Problem"}


def seed_default_assessment_types(db: Session) -> dict[str, AssessmentType]:
    """Insert any catalogue assessment types missing from this schema.

    Returns a `name -> AssessmentType` map (including pre-existing rows).
    """
    existing = {at.name: at for at in db.query(AssessmentType).all()}
    for name in DEFAULT_ASSESSMENT_TYPE_NAMES:
        if name in existing:
            continue
        assessment_type = AssessmentType(
            name=name,
            is_custom=False,
            requires_documents=name in DOCUMENT_REQUIRED_TYPE_NAMES,
            requires_cep_documents=name in CEP_DOCUMENT_REQUIRED_TYPE_NAMES,
            requires_oep_validation=name in OEP_VALIDATION_TYPE_NAMES,
        )
        db.add(assessment_type)
        existing[name] = assessment_type
    db.flush()
    return existing
