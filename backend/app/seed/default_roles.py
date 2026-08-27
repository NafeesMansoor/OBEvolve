"""Default roles seeded into every newly-provisioned tenant (spec §5).

Institution admins may add custom roles afterwards (ARCHITECTURE.md §3) —
these are the starting set, not a closed list. Permission sets are a
judgment call informed by each role's real-world responsibilities; codes for
modules not yet implemented (assessment.*, attainment.*, survey.*,
accreditation.*, ...) are included where the role will need them once those
phases ship, since the permission catalogue itself is already fixed
(app/core/permissions.py) even though nothing enforces those codes yet.

Seven roles are seeded `is_active=False` — disabled for ease of use per an
explicit request, not removed (existing grants, if any, keep working; they
just don't show up in the assignable-roles list). Institution admins can
re-enable any of them the same way they'd enable a custom role.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from sqlalchemy.orm import Session

from app.core.permissions import PERMISSION_CODES
from app.models.tenant.identity import Permission, Role, RolePermission

_ALL = "ALL"


@dataclass(frozen=True)
class RoleDef:
    name: str
    description: str
    permission_codes: tuple[str, ...] | Literal["ALL"]
    is_active: bool = field(default=True)


DEFAULT_ROLES: list[RoleDef] = [
    RoleDef(
        "Super Administrator",
        "Full control within the institution's tenant (distinct from the "
        "cross-institution platform_admins in the public schema). Includes "
        "raw_data.manage_all via the ALL sentinel: the raw-data console can "
        "reach every institution's every table.",
        _ALL,
    ),
    RoleDef(
        "Institution Administrator",
        "Manages organizational structure, programs, curriculum, course "
        "delivery, and users for the institution — the day-to-day "
        "administrator a Super Administrator delegates setup to. Raw-data "
        "console access is scoped to this institution only.",
        (
            "institution.view",
            "org.manage",
            "org.view",
            "program.manage",
            "program.view",
            "program.approve",
            "academic_calendar.manage",
            "academic_calendar.view",
            "user.manage",
            "user.view",
            "role.manage",
            "role.view",
            "audit.view",
            "curriculum.view",
            "outcome.create",
            "outcome.approve",
            "mapping.create",
            "section.manage",
            "section.view",
            "student.manage",
            "student.view",
            "grading.manage",
            "grading.view",
            "assessment.create",
            "assessment.approve",
            "assessment.view",
            "marks.enter",
            "report.generate",
            "raw_data.manage_institution",
        ),
    ),
    RoleDef(
        "Accreditation Administrator",
        "Owns accreditation submissions and evidence across the institution.",
        (
            "org.view",
            "program.view",
            "curriculum.view",
            "accreditation.manage",
            "evidence.upload",
            "report.generate",
            "audit.view",
        ),
        is_active=False,
    ),
    RoleDef(
        "Dean",
        "School-level oversight of curriculum and program approvals "
        "(typically scoped to one school).",
        (
            "org.view",
            "program.view",
            "program.approve",
            "curriculum.view",
            "outcome.approve",
            "user.view",
            "report.generate",
        ),
        is_active=False,
    ),
    RoleDef(
        "Head of Department",
        "Department-level curriculum and assessment oversight "
        "(typically scoped to one department).",
        (
            "org.view",
            "program.view",
            "curriculum.view",
            "outcome.create",
            "mapping.create",
            "section.manage",
            "section.view",
            "student.view",
            "grading.view",
            "assessment.approve",
            "user.view",
        ),
        is_active=False,
    ),
    RoleDef(
        "Program Administrator",
        "Full administrative control over one program's data (typically "
        "scoped to one program via UserRole.scope_type='program') — the "
        "raw-data-console peer of Institution Administrator, but scoped to "
        "a single program instead of the whole institution. Approves "
        "Program Coordinators' pending course-level raw-data changes.",
        (
            "program.view",
            "curriculum.view",
            "outcome.create",
            "outcome.approve",
            "mapping.create",
            "section.manage",
            "section.view",
            "student.manage",
            "student.view",
            "grading.manage",
            "grading.view",
            "assessment.create",
            "assessment.approve",
            "assessment.view",
            "marks.enter",
            "report.generate",
            "raw_data.manage_scoped",
            "raw_data.approve",
        ),
    ),
    RoleDef(
        "Program Coordinator",
        "Coordinates one program's curriculum and outcome definitions "
        "(typically scoped to one program). Cannot change program-level "
        "data (PEOs, POs, PO-PEO mappings) — that's Program Administrator "
        "territory. Raw-data-console writes to course-level tables are "
        "proposals, not immediate changes: a Program Administrator must "
        "approve one before it takes effect or becomes visible to others.",
        (
            "program.view",
            "curriculum.view",
            "outcome.create",
            "mapping.create",
            "section.view",
            "student.view",
            "grading.view",
            "assessment.create",
            "report.generate",
            "raw_data.propose_scoped",
        ),
    ),
    RoleDef(
        "Course Administrator",
        "Full administrative control over one course's data (typically "
        "scoped to one course via UserRole.scope_type='course') — the "
        "raw-data-console peer of Program Administrator, but scoped to a "
        "single course.",
        (
            "curriculum.view",
            "outcome.create",
            "outcome.approve",
            "mapping.create",
            "section.manage",
            "section.view",
            "student.view",
            "grading.view",
            "assessment.create",
            "assessment.approve",
            "assessment.view",
            "marks.enter",
            "raw_data.manage_scoped",
        ),
    ),
    RoleDef(
        "Faculty",
        "Delivers courses: creates assessments and enters marks for sections they teach.",
        (
            "curriculum.view",
            "mapping.create",
            "section.view",
            "student.view",
            "grading.view",
            "assessment.create",
            "assessment.view",
            "marks.enter",
        ),
    ),
    RoleDef(
        "Course Coordinator",
        "Owns one course's assessment plan and approves marks entry for its sections.",
        (
            "curriculum.view",
            "mapping.create",
            "section.view",
            "student.view",
            "grading.view",
            "assessment.create",
            "assessment.approve",
            "assessment.view",
            "marks.enter",
        ),
    ),
    RoleDef(
        "Examination/Assessment Administrator",
        "Institution-wide assessment scheduling and approval.",
        (
            "section.view",
            "grading.view",
            "assessment.create",
            "assessment.approve",
            "assessment.view",
            "marks.enter",
            "report.generate",
        ),
        is_active=False,
    ),
    RoleDef(
        "Quality Assurance Officer",
        "Monitors attainment results and survey cycles for institutional QA.",
        (
            "curriculum.view",
            "attainment.calculate",
            "attainment.approve",
            "survey.manage",
            "report.generate",
            "audit.view",
        ),
        is_active=False,
    ),
    RoleDef(
        "Accreditation Reviewer",
        "Reviews submitted evidence against accreditation criteria (typically external/part-time).",
        (
            "curriculum.view",
            "evidence.upload",
            "report.generate",
        ),
        is_active=False,
    ),
    RoleDef(
        "Student",
        "Views their own program curriculum and (from Phase 7) responds to surveys.",
        ("curriculum.view",),
    ),
    RoleDef(
        "External Stakeholder",
        "Employers/alumni/advisory-board members — survey participation only (Phase 7+); "
        "no Phase 1 permissions.",
        (),
        is_active=False,
    ),
]


def seed_default_roles(
    db: Session, permission_map: dict[str, Permission]
) -> dict[str, Role]:
    """Create default roles + their role_permissions grants. Idempotent.

    Also re-syncs `is_active`/`description` on already-seeded roles against
    the current `DEFAULT_ROLES` definition, so changing a role's default
    active state here and re-running this against an existing tenant takes
    effect (this is how the seven roles get retroactively disabled in
    already-provisioned tenants, not just new ones).

    `permission_map` is the `code -> Permission` map returned by
    `seed_default_permissions` (called first so every code here resolves).
    """
    existing_roles = {role.name: role for role in db.query(Role).all()}
    existing_grants: set[tuple] = {
        (rp.role_id, rp.permission_id) for rp in db.query(RolePermission).all()
    }

    for role_def in DEFAULT_ROLES:
        role = existing_roles.get(role_def.name)
        if role is None:
            role = Role(
                name=role_def.name,
                description=role_def.description,
                is_system_role=True,
                is_active=role_def.is_active,
            )
            db.add(role)
            db.flush()
            existing_roles[role_def.name] = role
        elif role.is_system_role:
            role.description = role_def.description
            role.is_active = role_def.is_active
            db.add(role)

        codes = PERMISSION_CODES if role_def.permission_codes == _ALL else role_def.permission_codes
        for code in codes:
            permission = permission_map.get(code)
            if permission is None:
                continue  # defensive: unknown code, skip rather than fail provisioning
            grant_key = (role.id, permission.id)
            if grant_key in existing_grants:
                continue
            db.add(RolePermission(role_id=role.id, permission_id=permission.id))
            existing_grants.add(grant_key)

    db.flush()
    return existing_roles
