"""Loads the fixed default `bloom_levels` catalogue (Remember -> Create) into
a tenant schema. Idempotent — safe to call against a schema that already has
some or all rows (check-by-name pattern, mirrors
`app.seed.assessment_defaults`)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.tenant.obe import BloomLevel

DEFAULT_BLOOM_LEVEL_NAMES: list[str] = [
    "Remember",
    "Understand",
    "Apply",
    "Analyze",
    "Evaluate",
    "Create",
]


def seed_default_bloom_levels(db: Session) -> dict[str, BloomLevel]:
    """Insert any catalogue Bloom levels missing from this schema.

    Returns a `name -> BloomLevel` map (including pre-existing rows).
    """
    existing = {level.name: level for level in db.query(BloomLevel).all()}
    for order, name in enumerate(DEFAULT_BLOOM_LEVEL_NAMES, start=1):
        if name in existing:
            continue
        level = BloomLevel(name=name, sequence_order=order, is_active=True)
        db.add(level)
        existing[name] = level
    db.flush()
    return existing
