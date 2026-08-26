"""FastAPI application factory."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.middleware.tenancy import TenancyMiddleware

logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s %(levelname)-8s %(name)s %(message)s",
)


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.project_name,
        debug=settings.debug,
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Tenant resolution runs on every request except the tenant-agnostic
    # paths listed in app.middleware.tenancy.TENANT_EXEMPT_PREFIXES.
    # Audit logging is NOT a blanket middleware — it's written explicitly by
    # the service layer on mutations (see app.services.audit), per
    # ARCHITECTURE.md §4 / the ADR: only the code that knows what changed can
    # produce a meaningful before/after audit row.
    #
    # Added BEFORE CORSMiddleware deliberately: Starlette's add_middleware()
    # makes the most-recently-added middleware the outermost layer, so
    # CORSMiddleware must be added last to end up outermost. Otherwise a
    # short-circuited TenancyMiddleware response (400/403/404, e.g. unknown
    # institution) never passes through CORSMiddleware at all, arrives at the
    # browser with no Access-Control-Allow-Origin header, and gets silently
    # blocked — surfacing to the frontend as an opaque "Network Error"
    # instead of the actual error body.
    app.add_middleware(TenancyMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.backend_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    @app.get("/health", tags=["infra"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
