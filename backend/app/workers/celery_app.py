"""Celery app wired to Redis. No tasks are registered in Phase 1.

Phase 6 (Attainment Engine) adds attainment-run tasks, Phase 9 (Analytics)
adds report-generation tasks, and notification delivery lands alongside
Phase 7 (Surveys & Continuous Improvement) — see ARCHITECTURE.md §5. Import
their task modules here (`celery_app.autodiscover_tasks([...])` or explicit
imports) once those phases exist; deliberately not stubbed out further now
since an empty `tasks.py` with no real task would be exactly the kind of
placeholder logic this codebase avoids.
"""

from __future__ import annotations

from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "obevolve",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
