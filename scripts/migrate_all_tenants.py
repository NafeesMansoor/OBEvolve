"""CLI: `python -m scripts.migrate_all_tenants`

Loops every row in `public.institutions` and runs the tenant Alembic chain
against that schema (ARCHITECTURE.md §2). Sequential by design — the ADR
(docs/adr/0001-schema-per-tenant.md) flags that this will need to become
parallel/queued once the platform grows past pilot scale, not solved here.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_BACKEND_ROOT = _REPO_ROOT / "backend"
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.db.session import session_scope  # noqa: E402
from app.models.public.institution import Institution  # noqa: E402
from app.services.tenancy import run_tenant_migrations  # noqa: E402

logger = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")

    with session_scope() as db:
        institutions = db.query(Institution).order_by(Institution.slug).all()
        targets = [(inst.slug, inst.schema_name) for inst in institutions]

    if not targets:
        print("No institutions found in public.institutions — nothing to migrate.")
        return

    failures: list[str] = []
    for slug, schema_name in targets:
        print(f"Migrating {slug!r} ({schema_name}) ...")
        try:
            run_tenant_migrations(schema_name)
        except Exception:
            logger.exception("Migration failed for institution %r", slug)
            failures.append(slug)
            continue
        print("  OK")

    if failures:
        print(f"Failed to migrate: {', '.join(failures)}", file=sys.stderr)
        raise SystemExit(1)

    print(f"Migrated {len(targets)} tenant schema(s).")


if __name__ == "__main__":
    main()
