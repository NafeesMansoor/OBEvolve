"""Seeds the BAETE v3.0 accreditation body/framework/PO/WK/WP/EA catalogue
into a tenant schema, from `app/seed/data/baete_v3.json` (verified verbatim
against the official BAETE manual — see the JSON file's own `source_url`
fields).

Idempotent — checked by framework name+version, since a framework's own
catalogue is immutable reference data (docs/adr/0002-framework-aware-outcomes.md).
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.tenant.accreditation import (
    AccreditationBody,
    AccreditationFramework,
    EngineeringActivity,
    FrameworkPO,
    KnowledgeProfile,
    ProblemAttribute,
)

_DATA_PATH = Path(__file__).parent / "data" / "baete_v3.json"


def _load_data() -> dict:
    with _DATA_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def seed_baete_v3_framework(db: Session) -> AccreditationFramework:
    """Create (or return the existing) BAETE v3.0 framework + its full
    PO/WK/WP/EA catalogue in this tenant schema.

    Idempotent: if a framework with this name+version already exists, it is
    returned as-is (its catalogue rows are not re-checked/re-created row by
    row — the framework as a whole is the idempotency unit, since it is
    immutable reference data seeded once).
    """
    data = _load_data()
    framework_data = data["framework"]

    existing = (
        db.query(AccreditationFramework)
        .filter(
            AccreditationFramework.name == framework_data["name"],
            AccreditationFramework.version == framework_data["version"],
        )
        .one_or_none()
    )
    if existing is not None:
        return existing

    body_data = data["accreditation_body"]
    body = (
        db.query(AccreditationBody)
        .filter(AccreditationBody.code == body_data["code"])
        .one_or_none()
    )
    if body is None:
        body = AccreditationBody(
            name=body_data["name"],
            code=body_data["code"],
            description=body_data.get("description"),
            is_active=True,
        )
        db.add(body)
        db.flush()

    framework = AccreditationFramework(
        accreditation_body_id=body.id,
        name=framework_data["name"],
        version=framework_data["version"],
        effective_date=date.fromisoformat(framework_data["effective_date"]),
        expiry_date=None,
        description=framework_data.get("description"),
        is_active=True,
    )
    db.add(framework)
    db.flush()

    for i, po in enumerate(data["framework_pos"], start=1):
        db.add(
            FrameworkPO(
                framework_id=framework.id,
                code=po["code"],
                statement=po["statement"],
                sequence=i,
                is_active=True,
            )
        )

    for i, wk in enumerate(data["knowledge_profiles"], start=1):
        db.add(
            KnowledgeProfile(
                framework_id=framework.id,
                code=wk["code"],
                title=wk.get("title"),
                description=wk["description"],
                sequence=i,
                is_active=True,
            )
        )

    for i, wp in enumerate(data["problem_attributes"], start=1):
        db.add(
            ProblemAttribute(
                framework_id=framework.id,
                code=wp["code"],
                title=wp.get("title"),
                description=wp["description"],
                sequence=i,
                is_active=True,
            )
        )

    for i, ea in enumerate(data["engineering_activities"], start=1):
        db.add(
            EngineeringActivity(
                framework_id=framework.id,
                code=ea["code"],
                title=ea.get("title"),
                description=ea["description"],
                sequence=i,
                is_active=True,
            )
        )

    db.flush()
    return framework
