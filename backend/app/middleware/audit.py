"""Request-context helper for audit logging.

This is deliberately **not** a blanket HTTP middleware — audit rows are
written explicitly by the service layer on significant mutations (see
`app.services.audit.write_audit_log`), not for every request indiscriminately.
This module only extracts the request metadata (`ip_address`, `user_agent`)
that a service needs to pass into that call.
"""

from __future__ import annotations

from starlette.requests import Request


def get_request_context(request: Request) -> dict[str, str | None]:
    """Extract the client IP and user agent from a request for audit logging.

    Honors `X-Forwarded-For` (first hop) when present, since the app is
    expected to run behind a reverse proxy in production.
    """
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        ip_address = forwarded_for.split(",")[0].strip()
    elif request.client:
        ip_address = request.client.host
    else:
        ip_address = None

    return {
        "ip_address": ip_address,
        "user_agent": request.headers.get("user-agent"),
    }
