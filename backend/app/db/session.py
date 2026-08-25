"""Engine + sessionmaker factories.

One process-wide engine is used for both the `public` schema and every
tenant schema; per-request tenant binding happens via
`execution_options(schema_translate_map=...)` applied to a *copy* of the
connection, not by creating a new engine per tenant (see app/db/tenancy.py).
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
    return _engine


def get_sessionmaker() -> sessionmaker[Session]:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            bind=get_engine(), autoflush=False, autocommit=False, expire_on_commit=False
        )
    return _SessionLocal


@contextmanager
def session_scope(schema_translate_map: dict[str | None, str] | None = None) -> Generator[Session]:
    """Context-manager session for use outside of FastAPI's DI (scripts, workers, tests).

    Commits on clean exit, rolls back and re-raises on error, always closes.
    """
    SessionLocal = get_sessionmaker()
    if schema_translate_map:
        connectable = get_engine().execution_options(schema_translate_map=schema_translate_map)
        session = SessionLocal(bind=connectable)
    else:
        session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
