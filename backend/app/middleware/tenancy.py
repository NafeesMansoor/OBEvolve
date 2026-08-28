"""Tenant resolution middleware (ARCHITECTURE.md §2).

Resolves the institution slug from the subdomain (production) or the
`X-Institution-Slug` header (local dev, per `settings.dev_tenant_header`),
looks it up in `public.institutions`, and stashes `schema_name` /
`institution_id` / `institution_slug` on `request.state` for
`app.db.tenancy.get_db` to bind the session with. Returns 404 for an unknown
or non-active tenant rather than letting the request fall through to a
handler with no tenant context.

A short list of paths are tenant-agnostic (health check, docs, platform-admin
institution provisioning) and skip resolution entirely.
"""

from __future__ import annotations

import logging

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings
from app.db.session import session_scope
from app.models.public.institution import Institution

logger = logging.getLogger(__name__)

# Paths that must work with no tenant resolved yet (platform-admin surface,
# infra endpoints). Matched by prefix.
TENANT_EXEMPT_PREFIXES: tuple[str, ...] = (
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    f"{settings.api_v1_prefix}/institutions",
    f"{settings.api_v1_prefix}/platform-auth",
    f"{settings.api_v1_prefix}/platform-raw-data",
)


def _extract_slug(request: Request) -> str | None:
    header_slug = request.headers.get(settings.dev_tenant_header)
    if header_slug:
        return header_slug.strip().lower()

    # Production: subdomain of the Host header, e.g. `acme.obevolve.io` -> `acme`.
    host = request.headers.get("host", "")
    host_without_port = host.split(":")[0]
    parts = host_without_port.split(".")
    if len(parts) >= 3:  # subdomain present
        return parts[0].lower()
    return None


class TenancyMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        path = request.url.path
        if any(path.startswith(prefix) for prefix in TENANT_EXEMPT_PREFIXES):
            return await call_next(request)

        slug = _extract_slug(request)
        if not slug:
            return JSONResponse(
                status_code=400,
                content={"detail": "Institution could not be determined from the request."},
            )

        institution = _lookup_institution(slug)
        if institution is None:
            logger.info("tenancy.unknown_slug", extra={"slug": slug})
            return JSONResponse(status_code=404, content={"detail": "Unknown institution."})
        if institution["status"] not in ("active", "trial"):
            logger.info("tenancy.inactive_institution", extra={"slug": slug})
            return JSONResponse(status_code=403, content={"detail": "Institution is not active."})

        request.state.schema_name = institution["schema_name"]
        request.state.institution_id = institution["id"]
        request.state.institution_slug = institution["slug"]

        return await call_next(request)


def _lookup_institution(slug: str) -> dict | None:
    with session_scope() as session:
        institution = session.query(Institution).filter(Institution.slug == slug).one_or_none()
        if institution is None:
            return None
        return {
            "id": institution.id,
            "slug": institution.slug,
            "schema_name": institution.schema_name,
            "status": institution.status,
        }
