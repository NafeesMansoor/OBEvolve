"""Outbound email — currently a stub, wired for real later.

There is no SMTP/transactional-email integration configured anywhere in
this codebase yet (no credentials in `app.core.config.Settings`, no email
library dependency). Rather than block features that need to "send" mail
(password reset today, likely notifications later) on that integration
existing, this module gives them one call site — `send_email()` — to depend
on now.

Wiring real delivery later is a one-function change: replace the body of
`send_email()` with an `smtplib` call (or a transactional API client, e.g.
SES/SendGrid/Postmark), reading credentials off `Settings`. Nothing in the
calling code (password reset, future notification code, ...) needs to
change — the function signature is the contract.
"""

from __future__ import annotations

import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, body: str) -> None:
    """"Send" an email. For now, logs that it would have been sent.

    Only logs the full `body` (which, for password reset, contains the raw
    reset link/token) when `settings.debug` is true — that is a deliberate
    local-dev convenience so a developer can pull the reset link out of the
    server log without a real mail transport. In non-debug (production-like)
    environments the body is withheld from the log entirely: it routinely
    carries sensitive, single-use secrets, and logs are a much wider-access,
    longer-retention surface than an actual mailbox.
    """
    logger.info(
        "email.would_send to=%s subject=%r", to, subject, extra={"to": to, "subject": subject}
    )
    if settings.debug:
        # Deliberately part of the log *message* (not just `extra`), since
        # the default logging.basicConfig formatter (see app/main.py) does
        # not render `extra` fields — only the message text.
        logger.info(
            "email.would_send.body to=%s subject=%r body=%s",
            to,
            subject,
            body,
            extra={"to": to, "subject": subject, "body": body},
        )
