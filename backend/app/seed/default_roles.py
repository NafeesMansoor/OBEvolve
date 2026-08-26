"""Default roles seeded into every newly-provisioned tenant (spec §5).

Institution admins may add custom roles afterwards (ARCHITECTURE.md §3) —
these are the starting set, not a closed list. Permission sets are a
judgment call informed by each role's real-world responsibilities; codes for
modules not yet implemented (assessment.*, attainment.*, survey.*,
accreditation.*, ...) are included where the role will need them once those
phases ship, since the permission catalogue itself is already fixed
(app/core/permissions.py) even though nothing enforces those codes yet.
"""

from __future__ import annotations

from dataclasses import dataclass
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


DEFAULT_ROLES: list[RoleDef] = [
    RoleDef(
        "Super Administrator",
        "Full control within the institution's tenant (distinct from the "
        "cross-institution platform_admins in the public schema).",
        _ALL,
    ),
    RoleDef(
        "Institution Administrator",
        "Manages organizational structure, programs, curriculum, course "
        "delivery, and users for the institution — the day-to-day "
        "administrator a Super Administrator delegates setup to.",
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
    ),
    RoleDef(
        "Program Coordinator",
        "Coordinates one program's curriculum and outcome definitions "
        "(typically scoped to one program).",
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
    ),
    RoleDef(
        "Accreditation Reviewer",
        "Reviews submitted evidence against accreditation criteria (typically external/part-time).",
        (
            "curriculum.view",
            "evidence.upload",
            "report.generate",
        ),
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
    ),
]


def seed_default_roles(
    db: Session, permission_map: dict[str, Permission]
) -> dict[str, Role]:
    """Create default roles + their role_permissions grants. Idempotent.

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
            role = Role(name=role_def.name, description=role_def.description, is_system_role=True)
            db.add(role)
            db.flush()
            existing_roles[role_def.name] = role

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
