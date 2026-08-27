"""Unit tests for the raw-data console's access-tier resolution
(app/services/raw_data.py) — pure logic, no database needed. This is the
highest-risk-of-a-subtle-bug part of the whole feature (row-level scope
filtering itself is exercised live against real data instead, see the
verification notes in the commit that introduced this module — a pure-SQL
mock would just duplicate the FK-chain logic under test)."""

from __future__ import annotations

import uuid

import app.models.public  # noqa: F401 - registers Institution/PlatformAdmin on the shared metadata
import app.models.tenant  # noqa: F401 - registers every tenant table on the shared metadata
from app.services.raw_data import (
    COURSE_LEVEL_TABLES,
    PROGRAM_LEVEL_TABLES,
    ScopedGrant,
    accessible_table_names,
    has_cross_institution_access,
    raw_data_grants,
    resolve_write_mode,
)


def test_raw_data_grants_filters_to_raw_data_codes() -> None:
    all_grants = [
        ("curriculum.view", None, None),
        ("raw_data.manage_institution", None, None),
        ("assessment.create", None, None),
    ]
    result = raw_data_grants(all_grants)
    assert [g.permission_code for g in result] == ["raw_data.manage_institution"]


def test_manage_all_sees_every_table_including_public() -> None:
    grants = [ScopedGrant("raw_data.manage_all", None, None)]
    names = accessible_table_names(grants)
    assert "institutions" in names
    assert "platform_admins" in names
    assert "peos" in names
    assert "courses" in names
    assert has_cross_institution_access(grants) is True


def test_manage_institution_sees_tenant_tables_not_public() -> None:
    grants = [ScopedGrant("raw_data.manage_institution", None, None)]
    names = accessible_table_names(grants)
    assert "institutions" not in names
    assert "users" in names  # institution-only table
    assert "peos" in names
    assert has_cross_institution_access(grants) is False


def test_program_admin_scoped_sees_program_and_course_tables_only() -> None:
    program_id = uuid.uuid4()
    grants = [ScopedGrant("raw_data.manage_scoped", "program", program_id)]
    names = accessible_table_names(grants)
    assert names == PROGRAM_LEVEL_TABLES | COURSE_LEVEL_TABLES
    assert "users" not in names
    assert "audit_logs" not in names


def test_course_admin_scoped_sees_course_tables_only() -> None:
    course_id = uuid.uuid4()
    grants = [ScopedGrant("raw_data.manage_scoped", "course", course_id)]
    names = accessible_table_names(grants)
    assert names == COURSE_LEVEL_TABLES
    assert "peos" not in names
    assert "programs" not in names


def test_program_coordinator_proposes_reads_both_groups() -> None:
    program_id = uuid.uuid4()
    grants = [ScopedGrant("raw_data.propose_scoped", "program", program_id)]
    names = accessible_table_names(grants)
    assert names == PROGRAM_LEVEL_TABLES | COURSE_LEVEL_TABLES


def test_write_mode_program_admin_is_immediate_on_both_groups() -> None:
    program_id = uuid.uuid4()
    grants = [ScopedGrant("raw_data.manage_scoped", "program", program_id)]
    assert resolve_write_mode(grants, "peos") == "immediate"
    assert resolve_write_mode(grants, "courses") == "immediate"


def test_write_mode_course_admin_denied_on_program_level() -> None:
    course_id = uuid.uuid4()
    grants = [ScopedGrant("raw_data.manage_scoped", "course", course_id)]
    assert resolve_write_mode(grants, "peos") == "denied"
    assert resolve_write_mode(grants, "courses") == "immediate"


def test_write_mode_program_coordinator_denied_on_program_propose_on_course() -> None:
    program_id = uuid.uuid4()
    grants = [ScopedGrant("raw_data.propose_scoped", "program", program_id)]
    assert resolve_write_mode(grants, "peos") == "denied"
    assert resolve_write_mode(grants, "programs") == "denied"
    assert resolve_write_mode(grants, "course_outcomes") == "propose"


def test_write_mode_manage_all_short_circuits_to_immediate() -> None:
    grants = [
        ScopedGrant("raw_data.propose_scoped", "program", uuid.uuid4()),
        ScopedGrant("raw_data.manage_all", None, None),
    ]
    assert resolve_write_mode(grants, "peos") == "immediate"


def test_write_mode_takes_the_best_across_multiple_grants() -> None:
    """A user holding both Program Coordinator (propose) and Course
    Administrator (immediate, for a different scope) grants should get
    immediate write on course-level tables — the union is the more
    permissive of the two, not whichever grant happens to be checked
    first."""
    grants = [
        ScopedGrant("raw_data.propose_scoped", "program", uuid.uuid4()),
        ScopedGrant("raw_data.manage_scoped", "course", uuid.uuid4()),
    ]
    assert resolve_write_mode(grants, "course_outcomes") == "immediate"


def test_no_grants_means_no_access() -> None:
    assert accessible_table_names([]) == set()
    assert resolve_write_mode([], "peos") == "denied"
