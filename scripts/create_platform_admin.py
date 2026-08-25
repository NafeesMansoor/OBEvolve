"""CLI: create or update a `public.platform_admins` Super Administrator account.

    python -m scripts.create_platform_admin --email admin@example.com \\
        --full-name "Super Administrator"

Idempotent "set" semantics: if the email already exists, its password and
full name are updated in place rather than erroring — this is the account
bootstrap tool, not a general user-management API, so there's exactly one
sane way to invoke it whether the account exists yet or not.

The password is never accepted as a positional/plaintext-echoing argument.
Pass it via the `PLATFORM_ADMIN_PASSWORD` environment variable (for
one-off/non-interactive use) or omit it to be prompted with hidden input.
Never put a real password in a committed file or in `.env.example`.
"""

from __future__ import annotations

import argparse
import getpass
import logging
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_BACKEND_ROOT = _REPO_ROOT / "backend"
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.core.security import hash_password  # noqa: E402
from app.db.session import session_scope  # noqa: E402
from app.models.public.platform_admin import PlatformAdmin  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create or update an OBEvolve platform (super admin) account."
    )
    parser.add_argument("--email", required=True, help="Login email, e.g. admin@example.com")
    parser.add_argument("--full-name", default="Super Administrator")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)-8s %(message)s")

    password = os.environ.get("PLATFORM_ADMIN_PASSWORD")
    if not password:
        password = getpass.getpass("Password: ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("Passwords did not match.", file=sys.stderr)
            raise SystemExit(1)
    if len(password) < 8:
        print("Password must be at least 8 characters.", file=sys.stderr)
        raise SystemExit(1)

    password_hash = hash_password(password)

    with session_scope() as db:
        admin = db.query(PlatformAdmin).filter(PlatformAdmin.email == args.email).one_or_none()
        created = admin is None
        if admin is None:
            admin = PlatformAdmin(email=args.email, full_name=args.full_name, is_active=True)
            db.add(admin)
        else:
            admin.full_name = args.full_name
            admin.is_active = True
        admin.password_hash = password_hash

    print(
        f"{'Created' if created else 'Updated'} platform admin {args.email!r}. "
        "Sign in at POST /api/v1/platform-auth/login."
    )


if __name__ == "__main__":
    main()
