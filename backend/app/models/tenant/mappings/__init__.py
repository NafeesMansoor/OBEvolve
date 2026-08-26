"""Mapping scales + CO-PO / PO-PEO junction tables (DATABASE_PLAN.md §E).

Implemented, left EMPTY — see `app/seed/ulab_cse.py` and
docs/adr/0002-framework-aware-outcomes.md for why no mapping rows are seeded.
"""

from app.models.tenant.mappings.scales import (
    CourseOutcomePOMapping,
    MappingScale,
    MappingScaleLevel,
    ProgramOutcomePEOMapping,
)

__all__ = [
    "CourseOutcomePOMapping",
    "MappingScale",
    "MappingScaleLevel",
    "ProgramOutcomePEOMapping",
]
