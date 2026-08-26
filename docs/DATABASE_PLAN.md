# OBEvolve — Database Plan

PostgreSQL 16. UUID primary keys everywhere. `schema-per-tenant` multi-tenancy —
see [ARCHITECTURE.md](ARCHITECTURE.md) §2 for the mechanism. All tables below live
in each institution's **tenant schema** unless explicitly marked `[public schema]`.

Tables marked **(Phase 1)** are implemented now with real Alembic migrations.
Everything else is the planned schema for later phases — documented up front so
the model doesn't need disruptive rewrites, but not yet migrated.

Conventions used throughout:
- `id UUID PK default gen_random_uuid()`
- `created_at timestamptz default now()`, `updated_at timestamptz` (auto-touched)
- Workflow status columns use one shared enum:
  `draft | submitted | reviewed | approved | published | archived`
- Mapping/weight scores use a configurable scale (see `mapping_scales`), default
  `0=None,1=Low,2=Medium,3=High`
- Soft-delete (`is_active boolean`) only on org/catalog entities that can be
  deactivated; assessment/academic records that feed accreditation are never
  deleted, only superseded by new versions.

---

## 0. Control plane `[public schema]` (Phase 1)

### `institutions`
Tenant registry — the only table every request needs before tenant resolution.

| column | type | notes |
|---|---|---|
| id | uuid PK | |
| name | text | |
| code | text unique | institutional short code |
| slug | text unique | used for subdomain / `X-Institution-Slug` |
| schema_name | text unique | `tenant_<slug>` |
| status | text | `active \| suspended \| trial` |
| subscription_plan | text | |
| contact_email | text | |
| logo_url | text nullable | |
| timezone | text | default `UTC` |
| created_at / updated_at | timestamptz | |

### `platform_admins`
Super Administrator accounts — the only role that spans institutions.

| column | type | notes |
|---|---|---|
| id | uuid PK | |
| email | text unique | |
| password_hash | text | |
| full_name | text | |
| mfa_secret | text nullable | MFA-ready, not enforced yet |
| is_active | boolean | |
| created_at | timestamptz | |

---

## A. Organizational structure (Phase 1)

`institutions → campuses → schools → departments → programs → program_versions`,
plus the academic calendar (`academic_years → academic_terms`).

### `campuses`
`id, institution_id[FK public.institutions], name, code, address, is_active, created_at, updated_at`
*(institution_id is the one cross-schema FK — tenant schema → public schema.)*

### `schools`
`id, campus_id[FK], name, code, is_active, created_at, updated_at`

### `departments`
`id, school_id[FK], name, code, is_active, created_at, updated_at`

### `programs`
`id, department_id[FK], name, code, degree_level, is_active, created_at, updated_at`

### `program_versions`
`id, program_id[FK], version_label, effective_academic_year_id[FK], status(workflow), created_by[FK users], approved_by[FK users], created_at, updated_at`

Historical program versions are never edited after `published`; a new curriculum
change creates a new `program_version` row (spec §6, §10).

### `academic_years`
`id, label, start_date, end_date, is_active`

### `academic_terms`
`id, academic_year_id[FK], name, term_type, start_date, end_date, is_active`

---

## B. Identity & RBAC (Phase 1)

### `users`
`id, email unique, password_hash, full_name, is_active, mfa_enabled, last_login_at, created_at, updated_at`

### `roles`
`id, name, description, is_system_role`  — seeded with the spec §5 defaults, but
institution admins may add custom roles.

### `permissions`
`id, code unique` (e.g. `curriculum.view`, `assessment.approve`, `marks.enter`),
`description, module`

### `role_permissions`
`role_id[FK], permission_id[FK]` — composite PK.

### `user_roles`
`id, user_id[FK], role_id[FK], scope_type` (`institution|campus|school|department|program`),
`scope_id nullable` — lets "HOD" be scoped to one department, "Dean" to one school.

### `faculty_profiles`
`user_id[FK PK], employee_code, designation, department_id[FK]`

### `student_profiles`
`user_id[FK PK], student_code, program_id[FK], program_version_id[FK], batch_year, status`

---

## C. Courses (Phase 2/4 — catalog, delivery, and grading policy implemented)

Course *catalog* (`courses`/`course_versions`) was implemented first so the
ULAB CSE course list could be seeded. Course *delivery/scheduling* —
offerings, sections, faculty assignments, enrollments — and grading policy
are implemented in this pass (Phase 4); `course_prerequisites` alone stays
planned — no source data for it yet.

### `courses` (Phase 2/3 — implemented)
`id, department_id[FK], code, title, description nullable, credits(numeric, keeps
source formatting like "1" or "3.0"), contact_hours nullable, course_type nullable
(category label as published, e.g. "Major Core Courses" — not yet a constrained
enum, since the source uses institution-specific category names), is_active`

### `course_versions` (Phase 2/3 — implemented)
`id, course_id[FK], version_label (e.g. "2022"), effective_academic_year_id[FK
nullable — curriculum year may predate the academic_years seeded for a fresh
tenant], status(workflow), created_by[FK nullable], approved_by[FK nullable]`

### `course_prerequisites` (still planned)
Unchanged from the original proposal — no source data for it yet.

### `course_offerings` / `course_sections` / `faculty_assignments` /
### `student_enrollments` (Phase 4 — implemented)
Course delivery/scheduling, per-term operational data (distinct from the
curriculum-level catalog above):

`course_offerings(id, course_version_id[FK], academic_term_id[FK org.AcademicTerm],
program_version_id[FK org.ProgramVersion, nullable — the same offering can
serve multiple programs' students])`

`course_sections(id, course_offering_id[FK], section_code, max_students nullable)`

`faculty_assignments(id, course_section_id[FK], faculty_user_id[FK identity.User],
role — "coordinator"|"instructor", free string, not an enum table)`

`student_enrollments(id, student_user_id[FK identity.User], course_section_id[FK],
enrollment_status(default "enrolled"), enrolled_at)`

### Grading policy (Phase 4 — implemented)
Letter-grade bands used to convert a percentage into a grade + grade point.
Not part of the original proposal — added alongside course delivery since a
policy is scoped the same way an offering is (institution-wide default, or
program-version-specific):

`grading_policies(id, name, program_version_id[FK org.ProgramVersion, nullable
— an institution-wide default policy has this null], is_default, description nullable)`

`grading_bands(id, grading_policy_id[FK], letter_grade (e.g. "A", "A-", "B+"),
min_percentage, max_percentage, grade_point nullable, sequence)`

---

## D. OBE outcome hierarchy (Phase 3 — implemented, framework-aware)

Extends the original proposal with an explicit accreditation-framework layer,
per `docs/adr/0002-framework-aware-outcomes.md`: an outcome's *framework*
definition (BAETE's official PO wording) and a program's *adopted* definition
(what a specific program actually publishes, which may use older/different
wording) are separate rows, optionally linked — never merged or overwritten.

### `bloom_levels`
`id, name, sequence_order, is_active` — configurable per institution, seeded with
the 6 default levels (Remember → Create). Unchanged from the original proposal.

### `accreditation_bodies` (implemented)
`id, name (e.g. "Board of Accreditation for Engineering and Technical
Education"), code (e.g. "BAETE"), description nullable, is_active`

### `accreditation_frameworks` (implemented)
This is the same table Group K's original sketch referenced; defined here
since a framework's PO/WK/WP/EA catalogue is needed starting Phase 3, well
before Phase 8's criteria/evidence workflow.
`id, accreditation_body_id[FK], name (e.g. "BAETE Accreditation Manual"),
version (e.g. "v3.0"), effective_date, expiry_date nullable, description
nullable, is_active`

### `framework_pos` (implemented)
The framework's own official PO catalogue — e.g. BAETE v3.0's PO1–PO12, verbatim.
`id, framework_id[FK], code, statement, sequence, is_active`

### `knowledge_profiles` (WK) / `problem_attributes` (WP) / `engineering_activities` (EA) (implemented)
Same shape for all three: `id, framework_id[FK], code, title nullable
(short label, e.g. WP's "Depth of knowledge required"), description, sequence,
is_active`. Seeded from BAETE v3.0 Tables 6.1/6.2/6.3 (WK1–9, WP1–7, EA1–5).

### `peos` (implemented)
`id, program_version_id[FK], code, statement, description nullable, sequence,
is_active, status(workflow), effective_from nullable, effective_to nullable,
created_by[FK nullable], approved_by[FK nullable]`

### `program_outcomes` (implemented — supersedes the earlier generic `pos` sketch)
The program's *adopted* POs — what the program actually publishes and assesses
against, which may differ in wording from the framework.
`id, program_version_id[FK], framework_po_id[FK framework_pos, NULLABLE], code,
title nullable (short label, e.g. "Engineering Knowledge"), statement, sequence,
is_active, status(workflow), effective_from nullable, effective_to nullable`

`framework_po_id` is set when a program PO is explicitly derived from a
framework PO (by outcome "slot," not by text match — e.g. ULAB's PO1 links to
BAETE v3.0's PO1 despite different wording); it stays `NULL` when a program PO
has no framework counterpart. This is the concrete mechanism for spec §27 /
ADR 0002: never assume framework wording and program wording are the same
string, but keep them traceable to each other.

### `psos` (still planned — not used by the ULAB CSE seed, kept for programs that need them)

### `course_outcomes` (implemented — supersedes the earlier generic `cos` sketch)
`id, course_version_id[FK], code (source convention: "CLO1".."CLO5"), statement,
sequence, bloom_target_level_id[FK bloom_levels, nullable], is_active,
status(workflow)`

### `tlos` / `competencies` / `performance_indicators` (still planned)
Unchanged — spec §16 explicitly defers PO indicators; no TLO/competency source
data exists yet either.

---

## E. Mappings (Phase 3 — junction tables implemented, left EMPTY)

All normalized junction tables — **never** comma-separated strings or JSON blobs
(spec §7). The tables below are migrated in this pass so the mapping UI has
somewhere to write to, but **no mapping rows are seeded** — CO–PO and PEO–PO
mapping data was deliberately excluded from curriculum-document extraction (the
source document's mapping tables are not authoritative for OBEvolve; mappings
must be entered/approved through the application itself).

| table | columns | status |
|---|---|---|
| `course_outcome_po_mappings` | course_outcome_id[FK], program_outcome_id[FK], mapping_scale_level_id[FK], remarks nullable | implemented, empty |
| `program_outcome_peo_mappings` | program_outcome_id[FK], peo_id[FK], mapping_scale_level_id[FK], remarks nullable | implemented, empty |
| `po_pso_mappings` | po_id[FK], pso_id[FK], level(int) | still planned |
| `tlo_co_mappings` | tlo_id[FK], co_id[FK], level(int) | still planned |
| `competency_pi_mappings` | competency_id[FK], performance_indicator_id[FK], level(int) | still planned |

### `mapping_scales` / `mapping_scale_levels` (implemented — supersedes the single-table sketch)
Correlation scales are institution-configurable in both how many levels exist
and what they're called (spec §14: binary Yes/No, ternary None/Low/High,
four-level None/Low/Medium/High, etc.), so they're two tables, not one fixed set
of rows:
`mapping_scales(id, name, description nullable, is_default)`
`mapping_scale_levels(id, mapping_scale_id[FK], value(int), label, sequence)`

Seeded default: a four-level scale (`0=None,1=Low,2=Medium,3=High`), matching
the correlation levels used in `course_outcome_po_mappings` /
`program_outcome_peo_mappings` above.

---

## F. Assessment definition (Phase 4 — implemented; `lesson_plans` and marks entry/gradebook stay planned)

Scope stops at *defining* assessment types/rubrics/questions/assessments —
recording student scores is a separate, later feature (marks entry/gradebook,
see §G's `student_performance`), not built here.

### `assessment_types` (implemented)
`id, name, is_custom` — seeded with 13 defaults (`app.seed.assessment_defaults`,
`is_custom=False`): Quiz, Class Test, Assignment, Lab, Project, Presentation,
Midterm, Final Exam, Viva, Seminar, Practical, Complex Engineering Problem,
Class Participation. Institutions may add their own (`is_custom=True`).

### `rubrics` / `rubric_criteria` / `rubric_levels` (implemented)
`rubrics(id, name, description nullable, is_reusable)`
`rubric_criteria(id, rubric_id[FK], criterion, weight)`
`rubric_levels(id, rubric_criterion_id[FK], label, score, description nullable)`

### `questions` (implemented)
`id, course_version_id[FK], text, question_type, difficulty nullable, marks, topic nullable, status(workflow), author_id[FK users, nullable], reviewer_id[FK users, nullable], created_at`

### `question_co_mappings` / `question_bloom_mappings` (implemented)
Junction tables: `question_id[FK]` + `course_outcome_id[FK]` /
`bloom_level_id[FK]` — no scale needed, a question either targets a CO/Bloom
level or not. `question_pi_mappings` stays planned — `performance_indicators`
(§D) doesn't exist yet either.

### `assessments` (implemented)
`id, course_section_id[FK], academic_term_id[FK], assessment_type_id[FK], title, max_marks, weight nullable, date nullable, duration_minutes nullable, rubric_id[FK nullable], status(workflow)`

### `assessment_questions` (implemented)
`id, assessment_id[FK], question_id[FK], marks_allocated, sequence`

### `lesson_plans` (still planned)
`id, course_offering_id[FK], week, date, topic, subtopic, tlo_id[FK nullable], co_id[FK nullable], bloom_level_id[FK nullable], teaching_method, learning_activity, resource, planned_duration, actual_duration, delivery_status`

---

## G. Student performance (Phase 5 — planned)

### `student_performance`
Raw marks — **immutable**, never overwritten by attainment calculation.

`id, student_user_id[FK users], assessment_id[FK], question_id[FK nullable],
raw_marks, max_marks, rubric_score nullable, attempt_number, evaluation_status,
entered_by[FK users], entered_at`

Corrections insert a new row (higher `attempt_number`) rather than updating —
history stays intact for audit and accreditation evidence.

---

## H. Attainment engine (Phase 6 — planned)

### `attainment_methodologies`
`id, name, description, version, direct_method, indirect_method, direct_weight,
indirect_weight, thresholds_json, rounding_rule, applicable_program_id[FK
nullable], effective_academic_year_id[FK], is_active`

Institution-configurable — the engine never hard-codes one formula (spec §17–18).

### `attainment_runs`
Immutable calculation record.

`id, methodology_id[FK], methodology_version, program_version_id[FK nullable],
course_version_id[FK nullable], academic_term_id[FK], scope(co|po|pso|peo),
parameters_json, input_dataset_ref, executed_by[FK users], executed_at, status,
calculation_version`

### Result tables (each FK's back to the `attainment_runs` row that produced it)
`co_attainment_results(id, attainment_run_id[FK], co_id[FK], course_section_id[FK], direct_value, indirect_value, final_value, student_count)`
`po_attainment_results`, `pso_attainment_results`, `peo_attainment_results` — analogous, at program scope.
`student_co_attainment(id, attainment_run_id[FK], student_user_id[FK], co_id[FK], value)` — enables the student-level drill-down required by spec §20.

### `threshold_definitions`
`id, scope_type, target, minimum, warning, critical, applicable_program_id[FK nullable]`

---

## I. Continuous improvement (Phase 7 — planned)

### `findings`
`id, related_outcome_type, related_outcome_id, description, root_cause, identified_by[FK users], identified_at, status`

### `action_plans`
`id, finding_id[FK], proposed_action, responsible_user_id[FK users], deadline,
expected_improvement, actual_improvement, evidence_ref nullable,
status(finding|action_plan|implementation|measurement|review|closure)`

---

## J. Surveys (Phase 7 — planned)

`survey_templates(id, name, stakeholder_type, is_anonymous)`
`survey_questions(id, survey_template_id[FK], text, question_type(rating|likert|mcq|text|matrix), options_json, sequence)`
`survey_instances(id, survey_template_id[FK], academic_term_id[FK], program_version_id[FK nullable], opens_at, closes_at, status)`
`survey_responses(id, survey_instance_id[FK], respondent_user_id[FK nullable — anonymous], submitted_at)`
`survey_answers(id, survey_response_id[FK], survey_question_id[FK], answer_value)`

Survey results feed the indirect-attainment side of the attainment engine
(spec §17, §23).

---

## K. Accreditation (Phase 8 — planned)

`accreditation_bodies` and `accreditation_frameworks` are already implemented —
see Group D above (needed earlier for the PO/WK/WP/EA catalogue). The
criteria/evidence workflow below is still Phase 8.

`accreditation_criteria(id, framework_id[FK], parent_criterion_id[FK nullable, self-referencing], code, title, description)`
`evidence_requirements(id, criterion_id[FK], description)`
`evidence_items(id, evidence_requirement_id[FK], description, file_ref nullable, url nullable, owner_user_id[FK users], academic_year_id[FK], program_version_id[FK nullable], upload_date, verification_status, reviewer_comments, version)`
`accreditation_submissions(id, framework_id[FK], program_version_id[FK], academic_year_id[FK], status)`

Frameworks are data, not code — NBA/ABET/internal-QA/custom all fit the same
tables (spec §24).

---

## L. Reporting / Analytics (Phase 9 — planned)

Mostly computed from the tables above at read time; the one persisted table:

`report_generation_log(id, report_type, parameters_json, generated_by[FK users], generated_at, file_ref, format)`

---

## M. Audit & operations (Phase 1)

### `audit_logs`
`id, user_id[FK users], action, entity_type, entity_id, previous_value_json,
new_value_json, timestamp, ip_address, user_agent`

Written by the service layer on every significant mutation (outcome changed,
mapping changed, marks changed, assessment approved, attainment calculated,
report generated, evidence uploaded, accreditation criterion approved — spec §29).

### `import_jobs` (Phase 5+ — planned)
`id, import_type, file_ref, status, validation_report_json, rows_total,
rows_success, rows_failed, imported_by[FK users], created_at, completed_at`

### `notifications` (Phase 1 table, Phase 7+ triggers)
`id, user_id[FK users], type, title, body, is_read, created_at`

---

## Core relationship diagram

```mermaid
erDiagram
  INSTITUTIONS ||--o{ CAMPUSES : has
  CAMPUSES ||--o{ SCHOOLS : has
  SCHOOLS ||--o{ DEPARTMENTS : has
  DEPARTMENTS ||--o{ PROGRAMS : has
  PROGRAMS ||--o{ PROGRAM_VERSIONS : has
  PROGRAM_VERSIONS ||--o{ PEOS : defines
  PROGRAM_VERSIONS ||--o{ POS : defines
  PROGRAM_VERSIONS ||--o{ PSOS : defines
  DEPARTMENTS ||--o{ COURSES : offers
  COURSES ||--o{ COURSE_VERSIONS : has
  COURSE_VERSIONS ||--o{ COS : defines
  COS }o--o{ POS : co_po_mappings
  COURSE_VERSIONS ||--o{ COURSE_OFFERINGS : scheduled_as
  COURSE_OFFERINGS ||--o{ COURSE_SECTIONS : has
  COURSE_SECTIONS ||--o{ ASSESSMENTS : has
  ASSESSMENTS ||--o{ QUESTIONS : contains
  QUESTIONS }o--o{ COS : question_co_mappings
  ASSESSMENTS ||--o{ STUDENT_PERFORMANCE : produces
  STUDENT_PERFORMANCE }o--|| ATTAINMENT_RUNS : "feeds (via calc)"
  ATTAINMENT_RUNS ||--o{ CO_ATTAINMENT_RESULTS : produces
  CO_ATTAINMENT_RESULTS }o--o{ PO_ATTAINMENT_RESULTS : "rolls up to"
  USERS ||--o{ USER_ROLES : has
  ROLES ||--o{ ROLE_PERMISSIONS : has
  USERS ||--o{ STUDENT_PERFORMANCE : "entered_by"
```

## RBAC diagram

```mermaid
erDiagram
  USERS ||--o{ USER_ROLES : has
  ROLES ||--o{ USER_ROLES : "granted via"
  ROLES ||--o{ ROLE_PERMISSIONS : has
  PERMISSIONS ||--o{ ROLE_PERMISSIONS : "granted via"
```
`user_roles.scope_type/scope_id` (not shown as an FK — polymorphic) ties a role
grant to one campus/school/department/program instead of the whole institution.

---

## Cross-cutting rules

- **UUID PKs** everywhere; `gen_random_uuid()` default (requires `pgcrypto` or
  Postgres 16's built-in `gen_random_uuid()`).
- **Cross-schema FK**: tenant tables referencing `institution_id` point at
  `public.institutions.id` — valid in Postgres within one database, but the one
  place `schema_translate_map` needs an explicit `schema="public"` in the
  SQLAlchemy model.
- **CHECK constraints** on every attainment/percentage column
  (`0 <= value <= 100`, or against the configured target scale).
- **Indexes** on every FK named in spec §32: `institution_id`, `program_id`,
  `course_id`, `academic_year_id`, `term_id`, `student_id`, `assessment_id`,
  `outcome_id` (and their equivalents: `co_id`, `po_id`, etc.).
- **Soft delete** (`is_active`) only on org/catalog entities that can be
  deactivated (courses, programs, users). Academic/assessment records that feed
  accreditation are never physically deleted — only superseded by a new version.
- **Transactions** wrap: assessment imports, marks updates, attainment runs,
  curriculum publication, accreditation submissions (spec §32).
- **Audit logging** happens in the service layer (not scattered across
  endpoints) so every mutating service function that touches the tables above
  also writes an `audit_logs` row.

## Migration strategy

Two independent Alembic chains (see `ARCHITECTURE.md` §2):
- `backend/alembic/public` → `public` schema (`institutions`, `platform_admins`).
- `backend/alembic/tenant` → applied once per `tenant_<slug>` schema via
  `scripts/migrate_all_tenants.py`, using SQLAlchemy `schema_translate_map` so
  the same migration scripts apply unmodified to every tenant.

Phase 1 ships the first migration in each chain (control-plane tables; org
structure + identity/RBAC + audit_logs/notifications). Every later phase adds
new tenant-chain migrations for its table group — never edits Phase 1's
migrations in place.
