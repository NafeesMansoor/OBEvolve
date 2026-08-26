# ADR 0002: Framework POs and program POs are separate, optionally-linked rows

## Status
Accepted

## Context
OBEvolve's first real tenant is ULAB CSE, accredited under BAETE (Bangladesh).
While sourcing seed data, we confirmed directly against the official BAETE v3.0
manual (baetebangladesh.org) that ULAB's currently-published Program Outcomes
use noticeably different wording from BAETE v3.0's official PO text — e.g.
ULAB's PO1 mentions "manufacturing engineering," a term that does not appear
anywhere in BAETE v3.0's PO1. ULAB's wording matches an older BAETE
formulation. This is a real, expected situation, not a data error: programs
update their published outcomes on their own cycle, independent of when the
accrediting body revises its framework.

The database must represent both without ever merging or silently overwriting
one with the other, since program-outcome wording is itself accreditation
evidence (it's what the program actually assessed students against for a given
curriculum year).

## Decision
Two separate tables:
- `framework_pos` — the accrediting body's own official PO catalogue, versioned
  per framework (`accreditation_frameworks`). Immutable reference data, seeded
  verbatim from the official manual.
- `program_outcomes` — what a specific program version actually publishes and
  assesses against. Has an optional `framework_po_id` FK, set only when a
  program PO is explicitly understood to be "the same outcome slot" as a
  framework PO (matched by position/intent, e.g. both are "PO1: engineering
  knowledge"), left `NULL` when there's no clean correspondence.

The same pattern applies to `peos` (program-owned, no framework equivalent
exists) and will apply to any future framework-vs-program distinction
elsewhere in the OBE hierarchy.

## Rationale
- Preserves accreditation traceability: an auditor can see both "what BAETE
  v3.0 requires" and "what ULAB actually published," and how they relate,
  without either one being lossy.
- Matches the explicit instruction from the ULAB CSE requirements doc
  (`docs/obevolve_ulab_cse_setup.md` §27): "Do not overwrite one with the
  other... this distinction is important for accreditation traceability."
- Generalizes past BAETE: any institution using any framework (ABET, NBA,
  internal QA) gets the same framework-catalogue/program-adoption split for
  free, with no framework-specific code.

## Trade-offs accepted
- Seeding a new program's POs requires deciding, per PO, whether a
  `framework_po_id` link applies — this is a one-time curation step per
  program/framework pair, not something the application can infer
  automatically (wording similarity is not a reliable enough signal on its
  own, and a wrong auto-link would be worse than no link).
- Reports that want "the current official framework wording" and "what this
  program actually says" side by side need an explicit join through
  `framework_po_id`, rather than reading one column.
