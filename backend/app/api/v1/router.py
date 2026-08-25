"""Aggregates all v1 endpoint routers under `settings.api_v1_prefix`."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import auth, institutions, org, platform_auth, users

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(platform_auth.router, prefix="/platform-auth", tags=["platform-auth"])
api_router.include_router(institutions.router, prefix="/institutions", tags=["institutions"])
api_router.include_router(org.router, prefix="/org", tags=["organization"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
