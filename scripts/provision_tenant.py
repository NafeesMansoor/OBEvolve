"""CLI: `python -m scripts.provision_tenant --slug demo --name "University Demo" [--seed-demo]`

Thin wrapper around `app.services.tenancy.provision_tenant` — the same
function `POST /api/v1/institutions` calls, so provisioning via CLI and via
API stay in sync by construction (ARCHITECTURE.md §2).
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
from app.seed.demo_institution import DEMO_ADMIN_EMAIL, DEMO_ADMIN_PASSWORD  # noqa: E402
from app.services.tenancy import (  # noqa: E402
    TenantAlreadyExistsError,
    TenantProvisioningError,
    provision_tenant,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Provision a new OBEvolve institution tenant.")
    parser.add_argument("--slug", required=True, help="URL/subdomain-safe slug, e.g. 'demo'")
    parser.add_argument("--name", required=True, help="Institution display name")
    parser.add_argument(
        "--code", default=None, help="Institution short code (defaults to the slug, uppercased)"
    )
    parser.add_argument(
        "--contact-email",
        default=None,
        help="Institution contact email (defaults to admin@<slug>.obevolve.dev)",
    )
    parser.add_argument("--subscription-plan", default=None)
    parser.add_argument("--timezone", default="UTC")
    parser.add_argument(
        "--seed-demo",
        action="store_true",
        help="Also seed a demo admin user and a small sample org structure",
    )
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")

    code = args.code or args.slug.upper()
    contact_email = args.contact_email or f"admin@{args.slug}.obevolve.dev"

    try:
        with session_scope() as db:
            institution = provision_tenant(
                db,
                name=args.name,
                code=code,
                slug=args.slug,
                contact_email=contact_email,
                subscription_plan=args.subscription_plan,
                timezone=args.timezone,
                seed_demo=args.seed_demo,
            )
            # Read attributes now, while the session (and its identity map)
            # is still open.
            slug, schema_name, institution_id = (
                institution.slug,
                institution.schema_name,
                institution.id,
            )
    except (TenantAlreadyExistsError, TenantProvisioningError) as exc:
        print(f"Provisioning failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    print(f"Provisioned institution {slug!r} -> schema {schema_name!r} (id={institution_id})")
    if args.seed_demo:
        print(
            f"Seeded demo admin: {DEMO_ADMIN_EMAIL} / {DEMO_ADMIN_PASSWORD}  (rotate immediately)"
        )


if __name__ == "__main__":
    main()
