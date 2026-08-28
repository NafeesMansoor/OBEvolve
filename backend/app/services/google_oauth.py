"""Google Sign-In: verify a Google Identity Services ID token server-side.

An ID token is a signed JWT Google issues after the *user* authenticates
with Google in the browser — it proves "Google says this person controls
this email address," nothing more. This module's only job is verifying that
claim cryptographically (signature, issuer, audience, expiry — all handled
by `google.oauth2.id_token.verify_oauth2_token`, which also fetches and
caches Google's public keys) and handing back the verified email. Whether
that email corresponds to an actual user account in this tenant, and
whether that account may log in, is decided by the caller
(app.api.v1.endpoints.auth.google_login) — this module has no notion of
tenants or user accounts.
"""

from __future__ import annotations

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

from app.core.config import settings

_google_request = google_requests.Request()


class GoogleTokenError(Exception):
    """Raised when an ID token fails verification or the settings needed to
    verify one (GOOGLE_CLIENT_ID) aren't configured."""


def verify_google_id_token(raw_id_token: str) -> str:
    """Verify a Google ID token and return the verified email address.

    Raises `GoogleTokenError` for anything that means "don't trust this
    token" — bad signature, wrong audience, expired, or (deliberately
    treated as a failure, not just a warning) an email Google itself hasn't
    verified, e.g. some federated/SSO-backed Google accounts.
    """
    if not settings.google_client_id:
        raise GoogleTokenError("Google Sign-In is not configured on this server.")

    try:
        claims = google_id_token.verify_oauth2_token(
            raw_id_token, _google_request, settings.google_client_id
        )
    except ValueError as exc:
        raise GoogleTokenError(f"Invalid Google ID token: {exc}") from exc

    if not claims.get("email_verified"):
        raise GoogleTokenError("Google has not verified this account's email address.")

    email = claims.get("email")
    if not email:
        raise GoogleTokenError("Google ID token did not include an email claim.")

    return email
