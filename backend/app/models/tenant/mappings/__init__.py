"""Mapping scales + CO-PO / PO-PEO / CO-PI / PO(PI)-K/CEP/CEA junction tables
(DATABASE_PLAN.md §E).

Implemented, left EMPTY — see `app/seed/ulab_cse.py` and
docs/adr/0002-framework-aware-outcomes.md for why no mapping rows are seeded.
"""

from app.models.tenant.mappings.framework_mappings import (
    ProgramOutcomeEngineeringActivityMapping,
    ProgramOutcomeKnowledgeProfileMapping,
    ProgramOutcomeProblemAttributeMapping,
)
from app.models.tenant.mappings.scales import (
    CourseOutcomePIMapping,
    CourseOutcomePOMapping,
    MappingScale,
    MappingScaleLevel,
    ProgramOutcomePEOMapping,
)

__all__ = [
    "CourseOutcomePIMapping",
    "CourseOutcomePOMapping",
    "MappingScale",
    "MappingScaleLevel",
    "ProgramOutcomeEngineeringActivityMapping",
    "ProgramOutcomeKnowledgeProfileMapping",
    "ProgramOutcomePEOMapping",
    "ProgramOutcomeProblemAttributeMapping",
]
