"""Aggregates all v1 endpoint routers under `settings.api_v1_prefix`."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints import (
    academic_ops,
    assessment,
    auth,
    curriculum,
    grading,
    institutions,
    org,
    platform_auth,
    raw_data,
    users,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(platform_auth.router, prefix="/platform-auth", tags=["platform-auth"])
api_router.include_router(institutions.router, prefix="/institutions", tags=["institutions"])
api_router.include_router(org.router, prefix="/org", tags=["organization"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(curriculum.router, prefix="/curriculum", tags=["curriculum"])
api_router.include_router(academic_ops.router, prefix="/academic", tags=["academic"])
api_router.include_router(grading.router, prefix="/grading", tags=["grading"])
api_router.include_router(assessment.router, prefix="/assessment", tags=["assessment"])
api_router.include_router(raw_data.router, prefix="/raw-data", tags=["raw-data"])
