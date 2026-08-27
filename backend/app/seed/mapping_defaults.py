"""Seeds the tenant-wide default mapping scale, used by CO-PO and PEO-PO
mapping cells (DATABASE_PLAN.md §E) when no institution-specific scale has
been configured yet.

Binary (Yes/No) per explicit request — institutions that want a graded scale
(None/Low/Medium/High, or anything else) can still define one of their own
through the mapping-scales UI; this is only the seeded starting point, not a
hard-coded limit (spec §14: the scale itself must stay configurable).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.tenant.mappings import MappingScale, MappingScaleLevel

DEFAULT_SCALE_NAME = "Yes/No"
DEFAULT_SCALE_LEVELS = [(0, "No"), (1, "Yes")]


def seed_default_mapping_scale(db: Session) -> MappingScale:
    """Idempotent: returns the existing default scale if one is already
    marked `is_default=True`, otherwise creates the binary one."""
    existing = db.query(MappingScale).filter(MappingScale.is_default.is_(True)).one_or_none()
    if existing is not None:
        return existing

    scale = MappingScale(
        name=DEFAULT_SCALE_NAME,
        description="Default correlation scale (DATABASE_PLAN.md §E) — binary mapped/not-mapped.",
        is_default=True,
    )
    db.add(scale)
    db.flush()
    for i, (value, label) in enumerate(DEFAULT_SCALE_LEVELS, start=1):
        db.add(MappingScaleLevel(mapping_scale_id=scale.id, value=value, label=label, sequence=i))
    db.flush()
    return scale
