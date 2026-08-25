"""No database needed — pure permission-resolution logic
(`app.services.rbac.grants_satisfy_permission`)."""

from __future__ import annotations

import uuid

from app.services.rbac import grants_satisfy_permission


def test_no_grants_means_no_permission() -> None:
    assert grants_satisfy_permission([], "curriculum.view") is False


def test_unscoped_grant_satisfies_any_scope() -> None:
    grants = [("curriculum.view", None, None)]
    assert grants_satisfy_permission(grants, "curriculum.view") is True
    assert grants_satisfy_permission(
        grants, "curriculum.view", scope_type="department", scope_id=uuid.uuid4()
    ) is True


def test_scoped_grant_only_satisfies_matching_scope() -> None:
    department_id = uuid.uuid4()
    other_department_id = uuid.uuid4()
    grants = [("outcome.create", "department", department_id)]

    assert (
        grants_satisfy_permission(
            grants, "outcome.create", scope_type="department", scope_id=department_id
        )
        is True
    )
    assert (
        grants_satisfy_permission(
            grants, "outcome.create", scope_type="department", scope_id=other_department_id
        )
        is False
    )
    assert grants_satisfy_permission(grants, "outcome.create") is False  # no scope requested at all


def test_wrong_permission_code_never_matches() -> None:
    grants = [("marks.enter", None, None)]
    assert grants_satisfy_permission(grants, "assessment.approve") is False


def test_multiple_grants_any_match_wins() -> None:
    department_id = uuid.uuid4()
    grants = [
        ("outcome.create", "department", uuid.uuid4()),  # different department
        ("outcome.create", "department", department_id),  # matching department
    ]
    assert (
        grants_satisfy_permission(
            grants, "outcome.create", scope_type="department", scope_id=department_id
        )
        is True
    )
