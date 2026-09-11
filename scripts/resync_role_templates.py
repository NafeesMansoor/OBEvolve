"""CLI: `python -m scripts.resync_role_templates`

Loops every row in `public.institutions` and re-applies the live
`public.role_templates` catalogue to that tenant's `roles` table
(`app.services.tenancy.resync_role_templates`). A platform admin editing a
role template (`PATCH /role-templates/{id}`) only takes effect for
*newly*-provisioned institutions until this is run — mirrors
`migrate_all_tenants.py`'s all-institutions loop, but for role templates
instead of the Alembic chain. Sequential by design, same reasoning as that
script.
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
from app.services.tenancy import resync_role_templates  # noqa: E402

logger = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")

    with session_scope() as db:
        institutions = db.query(Institution).order_by(Institution.slug).all()
        targets = [(inst.slug, inst.schema_name) for inst in institutions]

    if not targets:
        print("No institutions found in public.institutions — nothing to resync.")
        return

    failures: list[str] = []
    for slug, schema_name in targets:
        print(f"Resyncing role templates to {slug!r} ({schema_name}) ...")
        try:
            resync_role_templates(schema_name)
        except Exception:
            logger.exception("Role template resync failed for institution %r", slug)
            failures.append(slug)
            continue
        print("  OK")

    if failures:
        print(f"Failed to resync: {', '.join(failures)}", file=sys.stderr)
        raise SystemExit(1)

    print(f"Resynced role templates to {len(targets)} tenant schema(s).")


if __name__ == "__main__":
    main()
