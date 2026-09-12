"""programs.session_names — per-program academic-session naming
(Fall/Spring/Summer, Semester 1/2, Trimester 1/2/3, ...).

Institute Settings feedback: a program's yearly session count/names weren't
decidable anywhere, and `AcademicTerm.term_type` (institution-wide calendar,
`0022_academic_term_calendar.py`) is free text with no link back to any one
program — one program could run semesters while another runs trimesters,
and nothing recorded which names applied to which program. This column is
the per-program half of that: an ordered JSON list of session-name strings,
surfaced by a new "Sessions" panel under the Programs tab. Deliberately not
a new table (no per-session behavior beyond a name/order exists yet) and
deliberately not wired into `AcademicTerm` itself — the institution-wide
calendar is a separate, larger piece of scheduling machinery than this
migration's scope; `term_type` still accepts free text, this just gives the
program-level admin something concrete to align it against by convention.

Revision ID: 0029
Revises: 0028
Create Date: 2026-09-12 00:00:00

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0029"
down_revision: str | None = "0028"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _target_schema() -> str | None:
    """`op.add_column`/`op.drop_column` don't reliably honor
    `schema_translate_map` — see 0003_user_bio.py's identical helper."""
    bind = op.get_bind()
    return bind.get_execution_options().get("schema_translate_map", {}).get(None)


def upgrade() -> None:
    schema = _target_schema()
    op.add_column(
        "programs",
        sa.Column(
            "session_names",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
        schema=schema,
    )


def downgrade() -> None:
    schema = _target_schema()
    op.drop_column("programs", "session_names", schema=schema)
