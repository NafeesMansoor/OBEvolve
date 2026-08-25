"""No database needed — pure password hashing and JWT logic."""

from __future__ import annotations

import time
import uuid
from datetime import timedelta

import pytest

from app.core.security import (
    InvalidTokenError,
    TokenType,
    _create_token,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_hash_password_produces_a_verifiable_but_different_hash() -> None:
    plain = "correct horse battery staple"
    hashed = hash_password(plain)

    assert hashed != plain
    assert verify_password(plain, hashed)
    assert not verify_password("wrong password", hashed)


def test_hash_password_is_salted_differently_each_time() -> None:
    plain = "same-password"
    assert hash_password(plain) != hash_password(plain)


def test_access_token_roundtrip_carries_subject_and_institution() -> None:
    user_id = str(uuid.uuid4())
    token = create_access_token(user_id, institution_slug="acme")

    payload = decode_token(token)

    assert payload.sub == user_id
    assert payload.type == TokenType.ACCESS
    assert payload.institution_slug == "acme"
    assert payload.is_platform_admin is False


def test_refresh_token_has_refresh_type() -> None:
    token = create_refresh_token(str(uuid.uuid4()), institution_slug="acme")
    payload = decode_token(token)
    assert payload.type == TokenType.REFRESH


def test_decode_token_rejects_garbage() -> None:
    with pytest.raises(InvalidTokenError):
        decode_token("not.a.jwt")


def test_decode_token_rejects_expired_token() -> None:
    expired = _create_token(
        str(uuid.uuid4()), TokenType.ACCESS, timedelta(seconds=-1), institution_slug="acme"
    )
    with pytest.raises(InvalidTokenError):
        decode_token(expired)


def test_each_token_has_a_unique_jti() -> None:
    user_id = str(uuid.uuid4())
    token_a = create_access_token(user_id)
    time.sleep(0.01)
    token_b = create_access_token(user_id)

    assert decode_token(token_a).jti != decode_token(token_b).jti
