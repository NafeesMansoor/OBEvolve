"""Forgot-password / reset-password flow, end-to-end against a real
provisioned tenant. Requires a reachable PostgreSQL (`require_database`
skips cleanly otherwise) — see tests/integration/test_auth.py for the same
pattern this file follows.
"""

from __future__ import annotations

import hashlib

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.security import hash_password, verify_password
from app.db.session import session_scope
from app.main import app
from app.models.tenant.identity import PasswordResetToken, User

pytestmark = pytest.mark.usefixtures("require_database")

_OLD_PASSWORD = "OldSecret123!"  # noqa: S105 - test-only credential
_NEW_PASSWORD = "NewSecret456!"  # noqa: S105 - test-only credential


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def _tenant_headers(slug: str) -> dict[str, str]:
    return {settings.dev_tenant_header: slug}


def _create_user(schema_name: str, email: str) -> None:
    with session_scope(schema_translate_map={None: schema_name}) as db:
        user = User(email=email, password_hash=hash_password(_OLD_PASSWORD), full_name="Reset User")
        db.add(user)


def test_forgot_password_is_generic_for_unknown_email(
    client: TestClient, provisioned_tenant
) -> None:
    resp = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "nobody-here@example.org"},
        headers=_tenant_headers(provisioned_tenant.slug),
    )
    assert resp.status_code == 200
    assert "reset link has been sent" in resp.json()["detail"]


def test_forgot_password_then_reset_flow(client: TestClient, provisioned_tenant) -> None:
    slug = provisioned_tenant.slug
    email = "forgot-pw-user@example.org"
    _create_user(provisioned_tenant.schema_name, email)

    forgot_resp = client.post(
        "/api/v1/auth/forgot-password",
        json={"email": email},
        headers=_tenant_headers(slug),
    )
    assert forgot_resp.status_code == 200
    assert "reset link has been sent" in forgot_resp.json()["detail"]

    with session_scope(schema_translate_map={None: provisioned_tenant.schema_name}) as db:
        token_row = db.query(PasswordResetToken).one()
        assert token_row.used_at is None

    # Recover a raw token that hashes to the stored value isn't possible
    # (that's the point) — instead, mint one ourselves the same way the
    # endpoint does and overwrite the stored hash, so we can drive
    # reset-password without depending on log scraping in a unit test.
    raw_token = "test-raw-token-for-reset-flow"
    with session_scope(schema_translate_map={None: provisioned_tenant.schema_name}) as db:
        token_row = db.query(PasswordResetToken).one()
        token_row.token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    reset_resp = client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": _NEW_PASSWORD},
        headers=_tenant_headers(slug),
    )
    assert reset_resp.status_code == 204, reset_resp.text

    with session_scope(schema_translate_map={None: provisioned_tenant.schema_name}) as db:
        user = db.query(User).filter(User.email == email).one()
        assert verify_password(_NEW_PASSWORD, user.password_hash)
        assert not verify_password(_OLD_PASSWORD, user.password_hash)

        token_row = db.query(PasswordResetToken).one()
        assert token_row.used_at is not None

    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": _NEW_PASSWORD},
        headers=_tenant_headers(slug),
    )
    assert login_resp.status_code == 200, login_resp.text

    old_login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": _OLD_PASSWORD},
        headers=_tenant_headers(slug),
    )
    assert old_login_resp.status_code == 401

    reuse_resp = client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "AnotherOne789!"},
        headers=_tenant_headers(slug),
    )
    assert reuse_resp.status_code == 400


def test_reset_password_rejects_unknown_token(client: TestClient, provisioned_tenant) -> None:
    resp = client.post(
        "/api/v1/auth/reset-password",
        json={"token": "not-a-real-token", "new_password": _NEW_PASSWORD},
        headers=_tenant_headers(provisioned_tenant.slug),
    )
    assert resp.status_code == 400
