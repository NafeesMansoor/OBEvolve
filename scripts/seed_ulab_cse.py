"""CLI: `python -m scripts.seed_ulab_cse --tenant-slug ulab-cse`

Looks up the institution by slug in `public.institutions`, then seeds the
BAETE v3.0 accreditation framework catalogue followed by the full ULAB CSE
program (org structure, PEOs/POs, course catalog) into that tenant's schema.

Both seed functions are idempotent — safe to re-run against an
already-seeded tenant.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_BACKEND_ROOT = _REPO_ROOT / "backend"
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.db.session import session_scope  # noqa: E402
from app.models.public.institution import Institution  # noqa: E402
from app.seed.baete_v3 import seed_baete_v3_framework  # noqa: E402
from app.seed.ulab_cse import seed_ulab_cse_program  # noqa: E402

logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed the ULAB CSE program into a tenant schema.")
    parser.add_argument(
        "--tenant-slug", required=True, help="Institution slug to seed, e.g. 'ulab-cse'"
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")

    with session_scope() as db:
        institution = db.query(Institution).filter(Institution.slug == args.tenant_slug).one_or_none()
        if institution is None:
            print(f"No institution found with slug {args.tenant_slug!r}.", file=sys.stderr)
            raise SystemExit(1)
        institution_id, schema_name = institution.id, institution.schema_name

    print(f"Seeding {args.tenant_slug!r} -> schema {schema_name!r} ...")

    try:
        with session_scope(schema_translate_map={None: schema_name}) as tenant_db:
            framework = seed_baete_v3_framework(tenant_db)
            program = seed_ulab_cse_program(
                tenant_db, institution_id=institution_id, framework=framework
            )
            program_name, program_code = program.name, program.code
    except Exception as exc:
        logger.exception("seed_ulab_cse.failed", extra={"tenant_slug": args.tenant_slug})
        print(f"Seeding failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    print(f"Seeded program {program_name!r} (code={program_code}) into {schema_name!r}.")


if __name__ == "__main__":
    main()
