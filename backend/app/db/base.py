"""Declarative bases and shared column/mixin helpers.

Two separate `DeclarativeBase` subclasses is what lets Alembic run two
independent migration chains (see ARCHITECTURE.md §2 and
docs/adr/0001-schema-per-tenant.md): every model that belongs in the
`public` schema derives from `PublicBase`; every model that belongs in a
tenant's `tenant_<slug>` schema derives from `TenantBase`. Neither base sets
a hardcoded `schema` — tenant schema resolution happens per-request via
`schema_translate_map` (see app/db/tenancy.py), not at model-definition time.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, MetaData, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Tenant-schema tables declare cross-schema foreign keys back to
# `public.institutions` (see docs/adr/0001-schema-per-tenant.md — "the one
# cross-schema FK"). SQLAlchemy's ORM resolves a string ForeignKey target by
# looking it up in the *same* MetaData the referencing table belongs to, so
# PublicBase and TenantBase must share one MetaData instance even though they
# stay separate DeclarativeBase classes (which is what lets Alembic run two
# independent migration chains — see ARCHITECTURE.md §2). Each alembic env.py
# filters target_metadata via include_object so this sharing doesn't leak
# into autogenerate.
_shared_metadata = MetaData()


class PublicBase(DeclarativeBase):
    """Base for tables that live in the `public` schema (cross-tenant)."""

    metadata = _shared_metadata


class TenantBase(DeclarativeBase):
    """Base for tables that live in each institution's `tenant_<slug>` schema."""

    metadata = _shared_metadata


class WorkflowStatus(StrEnum):
    """Shared status enum for every approval-driven entity (spec §4, ARCHITECTURE.md §4).

    Only `program_versions` uses this in Phase 1; later phases (outcomes,
    courses, questions, evidence, ...) reuse the same shape, so it is defined
    once here rather than per-model.
    """

    DRAFT = "draft"
    SUBMITTED = "submitted"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class UUIDPKMixin:
    """UUID primary key, default `uuid.uuid4()` (generated app-side, not DB-side,
    so it is portable across the public/tenant schema split and needs no
    Postgres extension)."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )


class TimestampMixin:
    """`created_at` / `updated_at` timestamptz columns, `updated_at` auto-touched."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
