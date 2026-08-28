"""One-off bootstrap: creates the first `public.platform_admins` row.

There is deliberately no API endpoint for this (a platform admin is the one
role that can create/manage institutions across the whole deployment, so
exposing its creation over HTTP would need its own bootstrap-auth problem
solved) — run this directly against the deployed database instead, once,
after the public-schema migration has run. Idempotent: re-running with the
same email updates the password/name rather than erroring.

Usage:
    python scripts/create_platform_admin.py \
        --email you@example.com --password 'x' --name "Your Name"

Reads DATABASE_URL from the environment the same way the app does (see
app/core/config.py) — run this in the same environment as the deployed
backend (e.g. a Render one-off Shell/Job against the production database),
not against a local dev database unless that's genuinely the target.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.security import hash_password  # noqa: E402
from app.db.session import session_scope  # noqa: E402
from app.models.public.platform_admin import PlatformAdmin  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--name", default="Platform Administrator")
    args = parser.parse_args()

    email = args.email.strip().lower()

    with session_scope() as db:
        admin = db.query(PlatformAdmin).filter(PlatformAdmin.email == email).one_or_none()
        if admin is None:
            admin = PlatformAdmin(
                email=email,
                password_hash=hash_password(args.password),
                full_name=args.name,
                is_active=True,
            )
            db.add(admin)
            print(f"Created platform admin {email!r}.")
        else:
            admin.password_hash = hash_password(args.password)
            admin.full_name = args.name
            admin.is_active = True
            db.add(admin)
            print(f"Updated existing platform admin {email!r}.")


if __name__ == "__main__":
    main()
