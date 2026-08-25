"""`get_db` FastAPI dependency: yields a tenant-scoped SQLAlchemy session.

Reads the schema name resolved by `app.middleware.tenancy.TenancyMiddleware`
off `request.state.schema_name` and binds the session to that schema via
`execution_options(schema_translate_map={None: schema_name})`, per
ARCHITECTURE.md §2. Every ORM model is written with no hardcoded schema, so
the same model classes transparently read/write whichever tenant schema this
request was bound to.
"""

from __future__ import annotations

from collections.abc import Generator

from fastapi import Request
from sqlalchemy.orm import Session

from app.db.session import get_engine, get_sessionmaker


def get_db(request: Request) -> Generator[Session]:
    """Per-request tenant-scoped session. Requires TenancyMiddleware to have
    already set `request.state.schema_name` (404s happen in the middleware
    before this dependency is ever reached)."""
    schema_name: str = request.state.schema_name
    SessionLocal = get_sessionmaker()
    connectable = get_engine().execution_options(schema_translate_map={None: schema_name})
    session = SessionLocal(bind=connectable)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_public_db() -> Generator[Session]:
    """Session bound to the `public` schema only (no tenant translation) —
    used by platform-admin-only endpoints (e.g. institution provisioning)."""
    SessionLocal = get_sessionmaker()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
