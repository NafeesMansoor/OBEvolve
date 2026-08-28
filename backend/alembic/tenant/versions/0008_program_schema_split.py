"""drop tables moved to the per-program schema (docs/adr/0003-schema-per-program.md)

Applied once per tenant schema via schema_translate_map, same as every other
migration in this chain. By the time this runs against a given tenant, its
data for these 11 tables must already have been copied into that tenant's
program schema(s) and verified — this migration only drops the now-empty
source tables (and two FK constraints on tables that stay in this schema but
used to point at one of the moved tables). It does NOT move any data itself;
see the one-off migration script used for `demo`/`ulab-cse` (not part of this
repo's migration chain — a manual, verified, backed-up data move is not
something that should silently re-run against a fresh tenant that never had
this data in the shared schema to begin with).

`grading_policies.program_version_id` and `student_profiles.program_version_id`
lose their FK constraint entirely (not re-pointed at the program schema): a
single FK constraint can only target one fixed schema, but an institution can
have more than one program, so a real constraint from an institution-shared
table to a per-program table is architecturally unsound the moment a second
program exists. See the docstrings on `GradingPolicy`/`StudentProfile` in
app/models/tenant — referential integrity for these two columns is enforced
at the application layer from here on.

Revision ID: 0008
Revises: 0007
Create Date: 2026-08-28 00:00:00

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Order matters for both: dropped children-before-parents so no FK from a
# not-yet-dropped table in this list ever points at an already-dropped one.
_TABLES_IN_DROP_ORDER: tuple[str, ...] = (
    "assessment_questions",
    "assessments",
    "program_outcome_peo_mappings",
    "course_outcome_po_mappings",
    "student_enrollments",
    "faculty_assignments",
    "course_sections",
    "course_offerings",
    "program_outcomes",
    "peos",
    "program_versions",
)


def _target_schema() -> str | None:
    """`op.drop_constraint`/`op.drop_table` (like `op.add_column`/
    `op.drop_column` in 0003) can fall through to the default schema instead
    of the tenant schema — resolve it explicitly from the bind's execution
    options rather than relying on schema_translate_map alone."""
    bind = op.get_bind()
    return bind.get_execution_options().get("schema_translate_map", {}).get(None)


def upgrade() -> None:
    schema = _target_schema()

    op.drop_constraint(
        "grading_policies_program_version_id_fkey",
        "grading_policies",
        schema=schema,
        type_="foreignkey",
    )
    op.drop_constraint(
        "student_profiles_program_version_id_fkey",
        "student_profiles",
        schema=schema,
        type_="foreignkey",
    )

    for table in _TABLES_IN_DROP_ORDER:
        op.drop_table(table, schema=schema)


def downgrade() -> None:
    raise NotImplementedError(
        "0008 is not reversible via alembic downgrade: the tables it drops "
        "held real data that was moved to a per-program schema by a manual, "
        "verified, backed-up migration script run before this migration was "
        "applied (see backups/obevolve_pre_program_schema_*.dump). Restore "
        "from that backup instead of downgrading."
    )
