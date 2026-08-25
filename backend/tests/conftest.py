"""Shared pytest fixtures.

DB-backed tests need a reachable PostgreSQL instance at `DATABASE_URL`
(schema-per-tenant relies on real Postgres schemas — there is no sqlite
fallback, since UUID/JSON column types and `CREATE SCHEMA` are Postgres-
specific). This dev sandbox does not ship one, so `require_database` (and
everything that depends on it) calls `pytest.skip()` with a clear message
rather than hanging or erroring.
"""

from __future__ import annotations

import sys
import uuid
from collections.abc import Generator
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session

_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.core.config import settings  # noqa: E402


def _database_reachable() -> bool:
    from sqlalchemy import create_engine

    try:
        probe_engine = create_engine(settings.database_url, connect_args={"connect_timeout": 2})
        with probe_engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        probe_engine.dispose()
        return True
    except Exception:  # noqa: BLE001 - any connection failure means "unavailable"
        return False


@pytest.fixture(scope="session")
def database_available() -> bool:
    return _database_reachable()


@pytest.fixture(scope="session")
def require_database(database_available: bool) -> None:
    if not database_available:
        pytest.skip(
            "PostgreSQL not reachable at DATABASE_URL "
            f"({settings.database_url!r}) — skipping DB-dependent test. "
            "Run `docker compose up -d postgres` and re-run to exercise it."
        )


@pytest.fixture(scope="session")
def db_engine(require_database: None):
    from app.db.session import get_engine

    return get_engine()


@pytest.fixture(scope="session")
def public_schema_ready(db_engine, require_database: None) -> None:
    """Ensure `public.institutions` / `public.platform_admins` exist.

    Uses `PublicBase.metadata.create_all` rather than running the Alembic
    chain — the migration *files* are exercised separately (they're
    hand-written to match these same models); this fixture only needs the
    resulting schema to exist so tests can exercise application code.
    """
    import app.models.public  # noqa: F401 - registers tables on PublicBase.metadata
    from app.db.base import PublicBase

    with db_engine.begin() as connection:
        connection.execute(text("CREATE SCHEMA IF NOT EXISTS public"))
    PublicBase.metadata.create_all(db_engine)


@pytest.fixture
def public_db(db_engine, public_schema_ready: None) -> Generator[Session]:
    from app.db.session import get_sessionmaker

    SessionLocal = get_sessionmaker()
    session = SessionLocal()
    try:
        yield session
        session.rollback()
    finally:
        session.close()


@pytest.fixture
def provisioned_tenant(public_db: Session, db_engine):
    """Provisions a throwaway tenant for one test, then drops its schema and
    institutions row on teardown."""
    from app.services.tenancy import provision_tenant

    slug = f"test-{uuid.uuid4().hex[:8]}"
    institution = provision_tenant(
        public_db,
        name=f"Test Institution {slug}",
        code=slug.upper(),
        slug=slug,
        contact_email=f"admin@{slug}.example.org",
    )
    yield institution

    with db_engine.begin() as connection:
        connection.execute(text(f'DROP SCHEMA IF EXISTS "{institution.schema_name}" CASCADE'))
    public_db.query(type(institution)).filter(type(institution).id == institution.id).delete()
    public_db.commit()
