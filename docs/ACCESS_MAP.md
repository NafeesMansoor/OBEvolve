# OBEvolve Access Map

Every role, every menu item, every tab — and whether that role can just look, or actually change something. Generated from the live permission catalogue (`backend/app/core/permissions.py`), default role grants (`backend/app/seed/default_roles.py`), and the frontend’s actual navigation/tab gating — not a hand-maintained description of it. If the code changes, this doc goes stale; regenerate rather than hand-edit.

> **2026-09-12 full regeneration:** every role's section below was recomputed from scratch — the exact nav-item and tab-level permission gates (read directly from `frontend/src/app/layout.tsx` and every page/tab component under `frontend/src/features/`), cross-referenced against each role's exact granted codes in `backend/app/seed/default_roles.py`. No generator script exists (confirmed); this was a careful hand pass driven by a small Python model built from that ground truth, not free-hand transcription. A prior partial pass the same day (nav reorder + a few spot-corrections) undercounted the actual drift — several roles were missing nav items they should see (e.g. Head of Department legitimately has an **Assessment** entry via `assessment.approve`, limited to its Attainment/Pending documents tabs; Student and several disabled roles gained an **Outcome Mapping** entry via `curriculum.view`) or listed ones they shouldn't (e.g. several roles were shown "Grading" despite lacking `grading.manage`, which gates that nav item's *visibility*, not just its `grading.manage`/`grading.view` read-write split). This pass supersedes all of that. It also documents the institution-level custom-role-creation capability and the new platform-level Role Templates page (both 2026-09-12). Two things it deliberately does **not** do: model the exact conditional visibility of the Program & Curriculum page's "Performance Indicators" tab (only shown for curricula using the Indicator-Based PO method — noted inline, not modeled per-role) or fully verify the backend enforces every one of these frontend gates identically (frontend nav/tab visibility was the ground truth used throughout).

Interactive version: [Access Map](https://claude.ai/code/artifact/f984e975-d442-4367-8a1e-df55b14d53b8) (role picker + the same data, browsable) — **stale relative to this 2026-09-12 regeneration**, not yet republished.

**Legend** — **Read**: can view. **Read + Write**: can create / edit / approve. Sections not listed for a role aren’t in that role’s sidebar at all — visibility is nav-gated (`frontend/src/app/layout.tsx`'s `anyOfPermissions`), which is sometimes *stricter* than what the page itself would allow if reached directly by URL (e.g. Grading's nav entry needs `grading.manage`, though the page itself only requires `grading.view`) — deliberately, so a role never sees a sidebar link to a page it can only half-use.

## Contents

**Active by default**
- [Institution Administrator](#institution-administrator)
- [Program Administrator](#program-administrator)
- [Program Coordinator](#program-coordinator)
- [Section Coordinator](#section-coordinator)
- [Faculty](#faculty)
- [Student](#student)

**Seeded, disabled by default**
- [Legacy Tenant Administrator](#legacy-tenant-administrator)
- [Accreditation Administrator](#accreditation-administrator)
- [Dean](#dean)
- [Head of Department](#head-of-department)
- [Examination/Assessment Administrator](#examinationassessment-administrator)
- [Quality Assurance Officer](#quality-assurance-officer)
- [Accreditation Reviewer](#accreditation-reviewer)
- [External Stakeholder](#external-stakeholder)

**Separate system**
- [Platform Administrator](#platform-administrator)

---

## Active by default

### Institution Administrator

*Scope: Whole tenant* &nbsp;·&nbsp; `active`

Manages org structure, programs, curriculum, delivery, and users — created by the platform Super Administrator at provisioning time, and the top of the tenant's own role hierarchy. Raw-data console scoped to this institution. Notably does **not** hold `program_role.manage`/`term_commit.manage`, so — despite sitting at the top of the tenant's role hierarchy — it does not see **Program Administration** in its own nav; that page is Program Administrator's/Coordinator's.

**13** menu sections visible · **9** with write access · **30** permission codes granted

**Dashboard** (`/`)
  Content adapts by role rather than by a permission gate: the Student role sees a read-only “My Attainment” panel in place of the usual overview. Anyone holding section.view (teaches courses) sees a personalized Faculty Courses panel instead of the generic overview. Anyone holding academic_calendar.view additionally sees a Current Term card (added 2026-09-12) surfacing the active academic term, or a prompt to set one up if none is active. Anyone holding assessment.approve additionally sees a “documents awaiting review” card — itself just a link, not a write surface.

**Program & Curriculum** (`/program-settings`)
  - Curriculum — **Read + Write** _Creating/editing a program version needs program.manage; advancing its status needs program.approve._
  - Mission & Vision — **Read + Write** _Institutional/program mission and numbered visions, plus the Institutional Vision ↔ Program Vision mapping; program_outcome_framework.manage to write._
  - PEOs — **Read + Write** _program_outcome_framework.manage to write and to advance status; curriculum_feedback.create shows a Provide Feedback action instead of Advance._
  - Program Outcomes — **Read + Write** _program_outcome_framework.manage to write and to advance status; curriculum_feedback.create shows a Provide Feedback action instead of Advance._
  - Performance Indicators — **Read + Write** _Only shown when the curriculum uses the Indicator-Based PO method; program_outcome_framework.manage to write, same code to advance status._
  - Feedback — **Read + Write** _Everyone who can see this tab can submit feedback (curriculum_feedback.create) or just read it; reviewing/resolving a submission needs program_outcome_framework.manage._

**Outcome Mapping** (`/outcome-mapping`)
  - PEO-PO Mapping — **Read + Write**
  - Course Outcome Mapping — **Read + Write** _Editing also requires one specific course selected, not the institution-wide aggregate view._
  - K/CEP/CEA Mapping — **Read + Write** _Knowledge Profile / Complex Engineering Problem / Complex Engineering Activity mappings, one write permission for all three._
  - Accreditation Framework — **Read** _Read-only for every role — the accreditation body’s own catalogue, not tenant-editable data. — Program Outcomes (POs); Knowledge Profiles (WK); Problem Attributes (WP); Engineering Activities (EA)_

**Course Level Settings** (`/course-settings`)
  - Courses — **Read + Write** _All courses / by category — a client-side filter, not permission-gated. No workflow/approve step exists for a course itself._
  - Course versions — **Read + Write** _Creating/editing a version needs outcome.create; advancing its workflow status (draft→submitted→…→published) additionally needs outcome.approve._
  - Course Outcomes — **Read + Write** _Same split as Course versions: outcome.create to write, outcome.approve to advance status._

**Trimester Management** (`/academic`)
  - Academic calendar — **Read + Write** _Trimester/semester definition (dates, add/drop, midterm/final-exam windows, result dates) — leads this page since a term must be defined before anything below can reference one._
  - Course offerings — **Read + Write**
  - Sections — **Read + Write**
  - Faculty assignments — **Read + Write**
  - Enrollments — **Read + Write**
  - Students — **Read + Write**
  - Student cohorts — **Read + Write** _Viewing a cohort's roster is open to anyone who can see this tab; there is no edit or delete action for a cohort at all, only creation._

**Courses** (`/courses`)
  Read-only personal roster — current/previous sections taught, students, and a nudge for anything needing attention. No write actions exist on this page.

**Question Bank** (`/question-bank`)
  Read — own + globally-shared questions across courses. The one write control (“Shared globally” toggle) isn't permission-gated — it's available on a question only to its own author, regardless of role.

**Grading** (`/grading`)
  - Grading policies — **Read + Write** — Grade bands — nested inside each policy, same permission

**Assessment** (`/assessment`)
  - Assessment types — **Read + Write**
  - Rubrics — **Read + Write**
  - Question bank — **Read + Write** _assessment.create to write/create a question; advancing its status needs assessment.approve. Every question opens a Mappings panel (Bloom’s level + CO mapping) under the same assessment.create gate._
  - Assessments — **Read + Write** _assessment.create to write/attach questions; advancing status needs assessment.approve. The Documents panel (question paper, moderation/compliance forms, scripts, CEP docs) is upload = assessment.create, review/approve/extend-deadline = assessment.approve._
  - Marks entry — **Read + Write**
  - Attainment — **Read + Write** _Recalculating/locking attainment or editing its thresholds needs attainment.calculate or assessment.approve; otherwise read-only._
  - Pending documents — **Read + Write** _The whole tab is a review queue — reaching it at all already requires assessment.approve._

**Analytics** (`/analytics`)
  - PO Attainment — **Read + Write** _Read-only analysis for most viewers; recalculating/configuring thresholds needs attainment.calculate or program.manage._
  - Program Analytics — **Read** _Read-only roll-up — no write action exists on this tab for any role._
  - Course Attainment — **Read + Write** _Same component as Assessment → Attainment, reused here at the course level; excluded for a Faculty-only viewer (see My Courses)._

**Institute Settings** (`/organization`)
  - Institution — **Read** _Campuses are managed inline on this same tab, not a separate one — org.manage to write them. — Campuses — embedded card, write needs org.manage_
  - Schools — **Read + Write**
  - Departments — **Read + Write**
  - Programs — **Read + Write**
  - Users & roles — **Read + Write** _user.manage to create/deactivate accounts; role.manage to change what a role grants — and, as of 2026-09-12, to create brand-new custom roles with their own permission set (system-seeded roles keep name/permissions locked; only is_active/description are editable for those)._
  - Role matrix — **Read + Write** _Single gate for both seeing and editing this tab — no separate read-only tier._
  - Audit log — **Read** _Read-only — audit entries aren't editable._

**Raw Data Console** (`/raw-data`)
  Tiered access — Own institution — read/write/delete any tenant table (`raw_data.manage_institution`)

**About** (`/about`)
  Static, informational — the same for everyone.

---

### Program Administrator

*Scope: One program* &nbsp;·&nbsp; `active`

Full control over one program’s data — the program-scoped peer of Institution Administrator. Approves Program Coordinators’ pending raw-data changes.

**14** menu sections visible · **9** with write access · **25** permission codes granted

**Dashboard** (`/`)
  Content adapts by role rather than by a permission gate: the Student role sees a read-only “My Attainment” panel in place of the usual overview. Anyone holding section.view (teaches courses) sees a personalized Faculty Courses panel instead of the generic overview. Anyone holding academic_calendar.view additionally sees a Current Term card (added 2026-09-12) surfacing the active academic term, or a prompt to set one up if none is active. Anyone holding assessment.approve additionally sees a “documents awaiting review” card — itself just a link, not a write surface.

**Program & Curriculum** (`/program-settings`)
  - Curriculum — **Read** _Creating/editing a program version needs program.manage; advancing its status needs program.approve._
  - Mission & Vision — **Read + Write** _Institutional/program mission and numbered visions, plus the Institutional Vision ↔ Program Vision mapping; program_outcome_framework.manage to write._
  - PEOs — **Read + Write** _program_outcome_framework.manage to write and to advance status; curriculum_feedback.create shows a Provide Feedback action instead of Advance._
  - Program Outcomes — **Read + Write** _program_outcome_framework.manage to write and to advance status; curriculum_feedback.create shows a Provide Feedback action instead of Advance._
  - Performance Indicators — **Read + Write** _Only shown when the curriculum uses the Indicator-Based PO method; program_outcome_framework.manage to write, same code to advance status._
  - Feedback — **Read + Write** _Everyone who can see this tab can submit feedback (curriculum_feedback.create) or just read it; reviewing/resolving a submission needs program_outcome_framework.manage._

**Outcome Mapping** (`/outcome-mapping`)
  - PEO-PO Mapping — **Read + Write**
  - Course Outcome Mapping — **Read + Write** _Editing also requires one specific course selected, not the institution-wide aggregate view._
  - K/CEP/CEA Mapping — **Read + Write** _Knowledge Profile / Complex Engineering Problem / Complex Engineering Activity mappings, one write permission for all three._
  - Accreditation Framework — **Read** _Read-only for every role — the accreditation body’s own catalogue, not tenant-editable data. — Program Outcomes (POs); Knowledge Profiles (WK); Problem Attributes (WP); Engineering Activities (EA)_

**Course Level Settings** (`/course-settings`)
  - Courses — **Read + Write** _All courses / by category — a client-side filter, not permission-gated. No workflow/approve step exists for a course itself._
  - Course versions — **Read + Write** _Creating/editing a version needs outcome.create; advancing its workflow status (draft→submitted→…→published) additionally needs outcome.approve._
  - Course Outcomes — **Read + Write** _Same split as Course versions: outcome.create to write, outcome.approve to advance status._

**Program Administration** (`/program-administration`)
  - Faculty roles — **Read + Write** _Grant/revoke Faculty and Section Coordinator roles within one's own program, and create brand-new faculty accounts._
  - Final Commit — **Read + Write** _Enable early commit and permanently commit a term, locking further assessment/marks/attainment writes for it in this program._

**Trimester Management** (`/academic`)
  - Course offerings — **Read + Write**
  - Sections — **Read + Write**
  - Faculty assignments — **Read + Write**
  - Enrollments — **Read + Write**
  - Students — **Read + Write**
  - Student cohorts — **Read + Write** _Viewing a cohort's roster is open to anyone who can see this tab; there is no edit or delete action for a cohort at all, only creation._

**Courses** (`/courses`)
  Read-only personal roster — current/previous sections taught, students, and a nudge for anything needing attention. No write actions exist on this page.

**Question Bank** (`/question-bank`)
  Read — own + globally-shared questions across courses. The one write control (“Shared globally” toggle) isn't permission-gated — it's available on a question only to its own author, regardless of role.

**Grading** (`/grading`)
  - Grading policies — **Read + Write** — Grade bands — nested inside each policy, same permission

**Assessment** (`/assessment`)
  - Assessment types — **Read + Write**
  - Rubrics — **Read + Write**
  - Question bank — **Read + Write** _assessment.create to write/create a question; advancing its status needs assessment.approve. Every question opens a Mappings panel (Bloom’s level + CO mapping) under the same assessment.create gate._
  - Assessments — **Read + Write** _assessment.create to write/attach questions; advancing status needs assessment.approve. The Documents panel (question paper, moderation/compliance forms, scripts, CEP docs) is upload = assessment.create, review/approve/extend-deadline = assessment.approve._
  - Marks entry — **Read + Write**
  - Attainment — **Read + Write** _Recalculating/locking attainment or editing its thresholds needs attainment.calculate or assessment.approve; otherwise read-only._
  - Pending documents — **Read + Write** _The whole tab is a review queue — reaching it at all already requires assessment.approve._

**Analytics** (`/analytics`)
  - PO Attainment — **Read** _Read-only analysis for most viewers; recalculating/configuring thresholds needs attainment.calculate or program.manage._
  - Program Analytics — **Read** _Read-only roll-up — no write action exists on this tab for any role._
  - Course Attainment — **Read + Write** _Same component as Assessment → Attainment, reused here at the course level; excluded for a Faculty-only viewer (see My Courses)._

**Institute Settings** (`/organization`)
  - Programs — **Read**

**Raw Data Console** (`/raw-data`)
  Tiered access — Own program/course — read/write directly (`raw_data.manage_scoped`), plus approves others’ pending proposals (`raw_data.approve`)

**About** (`/about`)
  Static, informational — the same for everyone.

---

### Program Coordinator

*Scope: One program* &nbsp;·&nbsp; `active`

Manages semester-level course offerings and curriculum for one program. Cannot touch program-level data (PEOs/POs); raw-data writes go through Program Administrator approval.

**11** menu sections visible · **5** with write access · **19** permission codes granted

**Dashboard** (`/`)
  Content adapts by role rather than by a permission gate: the Student role sees a read-only “My Attainment” panel in place of the usual overview. Anyone holding section.view (teaches courses) sees a personalized Faculty Courses panel instead of the generic overview. Anyone holding academic_calendar.view additionally sees a Current Term card (added 2026-09-12) surfacing the active academic term, or a prompt to set one up if none is active. Anyone holding assessment.approve additionally sees a “documents awaiting review” card — itself just a link, not a write surface.

**Program & Curriculum** (`/program-settings`)
  - Curriculum — **Read** _Creating/editing a program version needs program.manage; advancing its status needs program.approve._
  - Mission & Vision — **Read** _Institutional/program mission and numbered visions, plus the Institutional Vision ↔ Program Vision mapping; program_outcome_framework.manage to write._
  - PEOs — **Read** _program_outcome_framework.manage to write and to advance status; curriculum_feedback.create shows a Provide Feedback action instead of Advance._
  - Program Outcomes — **Read** _program_outcome_framework.manage to write and to advance status; curriculum_feedback.create shows a Provide Feedback action instead of Advance._
  - Performance Indicators — **Read** _Only shown when the curriculum uses the Indicator-Based PO method; program_outcome_framework.manage to write, same code to advance status._
  - Feedback — **Read** _Everyone who can see this tab can submit feedback (curriculum_feedback.create) or just read it; reviewing/resolving a submission needs program_outcome_framework.manage._

**Outcome Mapping** (`/outcome-mapping`)
  - PEO-PO Mapping — **Read**
  - Course Outcome Mapping — **Read + Write** _Editing also requires one specific course selected, not the institution-wide aggregate view._
  - K/CEP/CEA Mapping — **Read** _Knowledge Profile / Complex Engineering Problem / Complex Engineering Activity mappings, one write permission for all three._
  - Accreditation Framework — **Read** _Read-only for every role — the accreditation body’s own catalogue, not tenant-editable data. — Program Outcomes (POs); Knowledge Profiles (WK); Problem Attributes (WP); Engineering Activities (EA)_

**Course Level Settings** (`/course-settings`)
  - Courses — **Read + Write** _All courses / by category — a client-side filter, not permission-gated. No workflow/approve step exists for a course itself._
  - Course versions — **Read + Write** _Creating/editing a version needs outcome.create; advancing its workflow status (draft→submitted→…→published) additionally needs outcome.approve._
  - Course Outcomes — **Read + Write** _Same split as Course versions: outcome.create to write, outcome.approve to advance status._
  - Course Types — **Read + Write** _A separate gate from the rest of this page — holding outcome.create/outcome.approve does not by itself grant this tab; only Program Coordinator and Section Coordinator currently hold course_type.manage among active roles._

**Program Administration** (`/program-administration`)
  - Faculty roles — **Read + Write** _Grant/revoke Faculty and Section Coordinator roles within one's own program, and create brand-new faculty accounts._

**Trimester Management** (`/academic`)
  - Course offerings — **Read + Write**
  - Sections — **Read + Write**
  - Faculty assignments — **Read + Write**
  - Enrollments — **Read**
  - Students — **Read**
  - Student cohorts — **Read + Write** _Viewing a cohort's roster is open to anyone who can see this tab; there is no edit or delete action for a cohort at all, only creation._

**Courses** (`/courses`)
  Read-only personal roster — current/previous sections taught, students, and a nudge for anything needing attention. No write actions exist on this page.

**Analytics** (`/analytics`)
  - PO Attainment — **Read** _Read-only analysis for most viewers; recalculating/configuring thresholds needs attainment.calculate or program.manage._
  - Program Analytics — **Read** _Read-only roll-up — no write action exists on this tab for any role._

**Institute Settings** (`/organization`)
  - Programs — **Read**

**Raw Data Console** (`/raw-data`)
  Tiered access — Own program: program-level tables read-only; course-level tables read + propose (a Program Administrator must approve before it takes effect) (`raw_data.propose_scoped`)

**About** (`/about`)
  Static, informational — the same for everyone.

> **No Question Bank, Grading, or Assessment nav item for this role** — despite holding `assessment.create`, this role lacks `assessment.view`/`assessment.approve` (Question Bank/Assessment's nav gates) and `grading.manage` (Grading's nav gate, stricter than the `grading.view` this role does hold). Assessment creation for this role's own courses happens elsewhere in the app (its own Course Management pages when also acting as faculty on a section), not through these institution-wide consoles.

---

### Section Coordinator

*Scope: One course* &nbsp;·&nbsp; `active`

Full administrative control over one course's data — the course-scoped peer of Program
Administrator — and owner of that course's assessment plan, approving marks entry for its
sections. Merges what were previously two separate roles ("Course Administrator" and "Section
Coordinator") whose responsibilities had grown to overlap; granting it no longer requires the
holder to already have a FacultyAssignment on a section of the course. Notably lacks `program.view`, so — despite holding `curriculum.view` and seeing most of Program & Curriculum — it doesn't see that page's "Curriculum" tab specifically; and it lacks all five of Institute Settings' gate codes, so doesn't see that nav item at all.

**11** menu sections visible · **6** with write access · **22** permission codes granted

**Dashboard** (`/`)
  Content adapts by role rather than by a permission gate: the Student role sees a read-only “My Attainment” panel in place of the usual overview. Anyone holding section.view (teaches courses) sees a personalized Faculty Courses panel instead of the generic overview. Anyone holding academic_calendar.view additionally sees a Current Term card (added 2026-09-12) surfacing the active academic term, or a prompt to set one up if none is active. Anyone holding assessment.approve additionally sees a “documents awaiting review” card — itself just a link, not a write surface.

**Program & Curriculum** (`/program-settings`)
  - Mission & Vision — **Read** _Institutional/program mission and numbered visions, plus the Institutional Vision ↔ Program Vision mapping; program_outcome_framework.manage to write._
  - PEOs — **Read** _program_outcome_framework.manage to write and to advance status; curriculum_feedback.create shows a Provide Feedback action instead of Advance._
  - Program Outcomes — **Read** _program_outcome_framework.manage to write and to advance status; curriculum_feedback.create shows a Provide Feedback action instead of Advance._
  - Performance Indicators — **Read** _Only shown when the curriculum uses the Indicator-Based PO method; program_outcome_framework.manage to write, same code to advance status._
  - Feedback — **Read** _Everyone who can see this tab can submit feedback (curriculum_feedback.create) or just read it; reviewing/resolving a submission needs program_outcome_framework.manage._

**Outcome Mapping** (`/outcome-mapping`)
  - PEO-PO Mapping — **Read**
  - Course Outcome Mapping — **Read + Write** _Editing also requires one specific course selected, not the institution-wide aggregate view._
  - K/CEP/CEA Mapping — **Read** _Knowledge Profile / Complex Engineering Problem / Complex Engineering Activity mappings, one write permission for all three._
  - Accreditation Framework — **Read** _Read-only for every role — the accreditation body’s own catalogue, not tenant-editable data. — Program Outcomes (POs); Knowledge Profiles (WK); Problem Attributes (WP); Engineering Activities (EA)_

**Course Level Settings** (`/course-settings`)
  - Courses — **Read + Write** _All courses / by category — a client-side filter, not permission-gated. No workflow/approve step exists for a course itself._
  - Course versions — **Read + Write** _Creating/editing a version needs outcome.create; advancing its workflow status (draft→submitted→…→published) additionally needs outcome.approve._
  - Course Outcomes — **Read + Write** _Same split as Course versions: outcome.create to write, outcome.approve to advance status._
  - Course Types — **Read + Write** _A separate gate from the rest of this page — holding outcome.create/outcome.approve does not by itself grant this tab; only Program Coordinator and Section Coordinator currently hold course_type.manage among active roles._

**Trimester Management** (`/academic`)
  - Course offerings — **Read + Write**
  - Sections — **Read + Write**
  - Faculty assignments — **Read + Write**
  - Enrollments — **Read + Write**
  - Students — **Read + Write**
  - Student cohorts — **Read + Write** _Viewing a cohort's roster is open to anyone who can see this tab; there is no edit or delete action for a cohort at all, only creation._

**Courses** (`/courses`)
  Read-only personal roster — current/previous sections taught, students, and a nudge for anything needing attention. No write actions exist on this page.

**Question Bank** (`/question-bank`)
  Read — own + globally-shared questions across courses. The one write control (“Shared globally” toggle) isn't permission-gated — it's available on a question only to its own author, regardless of role.

**Assessment** (`/assessment`)
  - Assessment types — **Read + Write**
  - Rubrics — **Read + Write**
  - Question bank — **Read + Write** _assessment.create to write/create a question; advancing its status needs assessment.approve. Every question opens a Mappings panel (Bloom’s level + CO mapping) under the same assessment.create gate._
  - Assessments — **Read + Write** _assessment.create to write/attach questions; advancing status needs assessment.approve. The Documents panel (question paper, moderation/compliance forms, scripts, CEP docs) is upload = assessment.create, review/approve/extend-deadline = assessment.approve._
  - Marks entry — **Read + Write**
  - Attainment — **Read + Write** _Recalculating/locking attainment or editing its thresholds needs attainment.calculate or assessment.approve; otherwise read-only._
  - Pending documents — **Read + Write** _The whole tab is a review queue — reaching it at all already requires assessment.approve._

**Analytics** (`/analytics`)
  - Course Attainment — **Read + Write** _Same component as Assessment → Attainment, reused here at the course level; excluded for a Faculty-only viewer (see My Courses)._

**Raw Data Console** (`/raw-data`)
  Tiered access — Own program/course — read/write directly (`raw_data.manage_scoped`)

**About** (`/about`)
  Static, informational — the same for everyone.

---

### Faculty

*Scope: Assigned sections* &nbsp;·&nbsp; `active`

Delivers courses: creates assessments and enters marks for sections they teach. Lacks `outcome.create`/`outcome.approve` (no Course Level Settings), `section.manage`/`academic_calendar.view` (no Trimester Management), `grading.manage` (no Grading), and `assessment.approve` (no institution-wide Assessment console) — Faculty's real day-to-day surface is Courses (their own sections) and Question Bank.

**7** menu sections visible · **1** with write access · **12** permission codes granted

**Dashboard** (`/`)
  Content adapts by role rather than by a permission gate: the Student role sees a read-only “My Attainment” panel in place of the usual overview. Anyone holding section.view (teaches courses) sees a personalized Faculty Courses panel instead of the generic overview. Anyone holding academic_calendar.view additionally sees a Current Term card (added 2026-09-12) surfacing the active academic term, or a prompt to set one up if none is active. Anyone holding assessment.approve additionally sees a “documents awaiting review” card — itself just a link, not a write surface.

**Program & Curriculum** (`/program-settings`)
  - Mission & Vision — **Read** _Institutional/program mission and numbered visions, plus the Institutional Vision ↔ Program Vision mapping; program_outcome_framework.manage to write._
  - PEOs — **Read** _program_outcome_framework.manage to write and to advance status; curriculum_feedback.create shows a Provide Feedback action instead of Advance._
  - Program Outcomes — **Read** _program_outcome_framework.manage to write and to advance status; curriculum_feedback.create shows a Provide Feedback action instead of Advance._
  - Performance Indicators — **Read** _Only shown when the curriculum uses the Indicator-Based PO method; program_outcome_framework.manage to write, same code to advance status._
  - Feedback — **Read** _Everyone who can see this tab can submit feedback (curriculum_feedback.create) or just read it; reviewing/resolving a submission needs program_outcome_framework.manage._

**Outcome Mapping** (`/outcome-mapping`)
  - PEO-PO Mapping — **Read**
  - Course Outcome Mapping — **Read + Write** _Editing also requires one specific course selected, not the institution-wide aggregate view._
  - K/CEP/CEA Mapping — **Read** _Knowledge Profile / Complex Engineering Problem / Complex Engineering Activity mappings, one write permission for all three._
  - Accreditation Framework — **Read** _Read-only for every role — the accreditation body’s own catalogue, not tenant-editable data. — Program Outcomes (POs); Knowledge Profiles (WK); Problem Attributes (WP); Engineering Activities (EA)_

**Courses** (`/courses`)
  Read-only personal roster — current/previous sections taught, students, and a nudge for anything needing attention. No write actions exist on this page.

**Question Bank** (`/question-bank`)
  Read — own + globally-shared questions across courses. The one write control (“Shared globally” toggle) isn't permission-gated — it's available on a question only to its own author, regardless of role.

**Analytics** (`/analytics`)
  - My Courses — **Read** _Shown instead of the tabs below to a caller holding only assessment.view (no program.view, no assessment.approve) — an aggregate read-only rollup across their own current+previous sections._

**About** (`/about`)
  Static, informational — the same for everyone.

---

### Student

*Scope: Own record* &nbsp;·&nbsp; `active`

Views their own program curriculum. The Dashboard replaces the usual overview with a read-only “My Attainment” panel for this role specifically. Holds only `curriculum.view` — which is enough to see (read-only) most of Program & Curriculum and all of Outcome Mapping, since neither page's overall visibility gate requires anything stronger.

**4** menu sections visible · **0** with write access · **1** permission codes granted

**Dashboard** (`/`)
  Content adapts by role rather than by a permission gate: the Student role sees a read-only “My Attainment” panel in place of the usual overview. Anyone holding section.view (teaches courses) sees a personalized Faculty Courses panel instead of the generic overview. Anyone holding academic_calendar.view additionally sees a Current Term card (added 2026-09-12) surfacing the active academic term, or a prompt to set one up if none is active. Anyone holding assessment.approve additionally sees a “documents awaiting review” card — itself just a link, not a write surface.

**Program & Curriculum** (`/program-settings`)
  - Mission & Vision — **Read** _Institutional/program mission and numbered visions, plus the Institutional Vision ↔ Program Vision mapping; program_outcome_framework.manage to write._
  - PEOs — **Read** _program_outcome_framework.manage to write and to advance status; curriculum_feedback.create shows a Provide Feedback action instead of Advance._
  - Program Outcomes — **Read** _program_outcome_framework.manage to write and to advance status; curriculum_feedback.create shows a Provide Feedback action instead of Advance._
  - Performance Indicators — **Read** _Only shown when the curriculum uses the Indicator-Based PO method; program_outcome_framework.manage to write, same code to advance status._
  - Feedback — **Read** _Everyone who can see this tab can submit feedback (curriculum_feedback.create) or just read it; reviewing/resolving a submission needs program_outcome_framework.manage._

**Outcome Mapping** (`/outcome-mapping`)
  - PEO-PO Mapping — **Read**
  - Course Outcome Mapping — **Read** _Editing also requires one specific course selected, not the institution-wide aggregate view._
  - K/CEP/CEA Mapping — **Read** _Knowledge Profile / Complex Engineering Problem / Complex Engineering Activity mappings, one write permission for all three._
  - Accreditation Framework — **Read** _Read-only for every role — the accreditation body’s own catalogue, not tenant-editable data. — Program Outcomes (POs); Knowledge Profiles (WK); Problem Attributes (WP); Engineering Activities (EA)_

**About** (`/about`)
  Static, informational — the same for everyone.

---

## Seeded, disabled by default

### Legacy Tenant Administrator

*Scope: Whole tenant* &nbsp;·&nbsp; `disabled by default`

Full control within the institution’s tenant, including raw-data access to every institution via the ALL sentinel. Renamed from “Super Administrator” — that name now belongs exclusively to the cross-institution platform_admins account (Dr. Geek, the developer/maintainer of OBEvolve), never a tenant-scoped role.

> Seeded inactive — the role hierarchy now starts at Institution Administrator, created by the platform Super Administrator at provisioning time. Existing holders keep their grant unchanged; no new grants should be made.

**14** menu sections visible · **10** with write access · **54** permission codes granted (every code in the fixed catalogue — the ALL sentinel)

**Dashboard** (`/`)
  Content adapts by role rather than by a permission gate: the Student role sees a read-only “My Attainment” panel in place of the usual overview. Anyone holding section.view (teaches courses) sees a personalized Faculty Courses panel instead of the generic overview. Anyone holding academic_calendar.view additionally sees a Current Term card (added 2026-09-12) surfacing the active academic term, or a prompt to set one up if none is active. Anyone holding assessment.approve additionally sees a “documents awaiting review” card — itself just a link, not a write surface.

**Program & Curriculum** (`/program-settings`)
  - Curriculum — **Read + Write** _Creating/editing a program version needs program.manage; advancing its status needs program.approve._
  - Mission & Vision — **Read + Write** _Institutional/program mission and numbered visions, plus the Institutional Vision ↔ Program Vision mapping; program_outcome_framework.manage to write._
  - PEOs — **Read + Write** _program_outcome_framework.manage to write and to advance status; curriculum_feedback.create shows a Provide Feedback action instead of Advance._
  - Program Outcomes — **Read + Write** _program_outcome_framework.manage to write and to advance status; curriculum_feedback.create shows a Provide Feedback action instead of Advance._
  - Performance Indicators — **Read + Write** _Only shown when the curriculum uses the Indicator-Based PO method; program_outcome_framework.manage to write, same code to advance status._
  - Feedback — **Read + Write** _Everyone who can see this tab can submit feedback (curriculum_feedback.create) or just read it; reviewing/resolving a submission needs program_outcome_framework.manage._

**Outcome Mapping** (`/outcome-mapping`)
  - PEO-PO Mapping — **Read + Write**
  - Course Outcome Mapping — **Read + Write** _Editing also requires one specific course selected, not the institution-wide aggregate view._
  - K/CEP/CEA Mapping — **Read + Write** _Knowledge Profile / Complex Engineering Problem / Complex Engineering Activity mappings, one write permission for all three._
  - Accreditation Framework — **Read** _Read-only for every role — the accreditation body’s own catalogue, not tenant-editable data. — Program Outcomes (POs); Knowledge Profiles (WK); Problem Attributes (WP); Engineering Activities (EA)_

**Course Level Settings** (`/course-settings`)
  - Courses — **Read + Write** _All courses / by category — a client-side filter, not permission-gated. No workflow/approve step exists for a course itself._
  - Course versions — **Read + Write** _Creating/editing a version needs outcome.create; advancing its workflow status (draft→submitted→…→published) additionally needs outcome.approve._
  - Course Outcomes — **Read + Write** _Same split as Course versions: outcome.create to write, outcome.approve to advance status._
  - Course Types — **Read + Write** _A separate gate from the rest of this page — holding outcome.create/outcome.approve does not by itself grant this tab; only Program Coordinator and Section Coordinator currently hold course_type.manage among active roles (the ALL sentinel grants it here too)._

**Program Administration** (`/program-administration`)
  - Faculty roles — **Read + Write** _Grant/revoke Faculty and Section Coordinator roles within one's own program, and create brand-new faculty accounts._
  - Final Commit — **Read + Write** _Enable early commit and permanently commit a term, locking further assessment/marks/attainment writes for it in this program._

**Trimester Management** (`/academic`)
  - Academic calendar — **Read + Write** _Trimester/semester definition (dates, add/drop, midterm/final-exam windows, result dates) — leads this page since a term must be defined before anything below can reference one._
  - Course offerings — **Read + Write**
  - Sections — **Read + Write**
  - Faculty assignments — **Read + Write**
  - Enrollments — **Read + Write**
  - Students — **Read + Write**
  - Student cohorts — **Read + Write** _Viewing a cohort's roster is open to anyone who can see this tab; there is no edit or delete action for a cohort at all, only creation._

**Courses** (`/courses`)
  Read-only personal roster — current/previous sections taught, students, and a nudge for anything needing attention. No write actions exist on this page.

**Question Bank** (`/question-bank`)
  Read — own + globally-shared questions across courses. The one write control (“Shared globally” toggle) isn't permission-gated — it's available on a question only to its own author, regardless of role.

**Grading** (`/grading`)
  - Grading policies — **Read + Write** — Grade bands — nested inside each policy, same permission

**Assessment** (`/assessment`)
  - Assessment types — **Read + Write**
  - Rubrics — **Read + Write**
  - Question bank — **Read + Write** _assessment.create to write/create a question; advancing its status needs assessment.approve. Every question opens a Mappings panel (Bloom’s level + CO mapping) under the same assessment.create gate._
  - Assessments — **Read + Write** _assessment.create to write/attach questions; advancing status needs assessment.approve. The Documents panel (question paper, moderation/compliance forms, scripts, CEP docs) is upload = assessment.create, review/approve/extend-deadline = assessment.approve._
  - Marks entry — **Read + Write**
  - Attainment — **Read + Write** _Recalculating/locking attainment or editing its thresholds needs attainment.calculate or assessment.approve; otherwise read-only._
  - Pending documents — **Read + Write** _The whole tab is a review queue — reaching it at all already requires assessment.approve._

**Analytics** (`/analytics`)
  - PO Attainment — **Read + Write** _Read-only analysis for most viewers; recalculating/configuring thresholds needs attainment.calculate or program.manage._
  - Program Analytics — **Read** _Read-only roll-up — no write action exists on this tab for any role._
  - Course Attainment — **Read + Write** _Same component as Assessment → Attainment, reused here at the course level; excluded for a Faculty-only viewer (see My Courses)._

**Institute Settings** (`/organization`)
  - Institution — **Read + Write** _Campuses are managed inline on this same tab, not a separate one — org.manage to write them. — Campuses — embedded card, write needs org.manage_
  - Schools — **Read + Write**
  - Departments — **Read + Write**
  - Programs — **Read + Write**
  - Users & roles — **Read + Write** _user.manage to create/deactivate accounts; role.manage to change what a role grants — and, as of 2026-09-12, to create brand-new custom roles with their own permission set (system-seeded roles keep name/permissions locked; only is_active/description are editable for those)._
  - Role matrix — **Read + Write** _Single gate for both seeing and editing this tab — no separate read-only tier._
  - Audit log — **Read** _Read-only — audit entries aren't editable._

**Raw Data Console** (`/raw-data`)
  Tiered access — Every institution — read/write/delete any table (`raw_data.manage_all`), plus approves others’ pending proposals (`raw_data.approve`)

**About** (`/about`)
  Static, informational — the same for everyone.

---

### Accreditation Administrator

*Scope: Whole tenant* &nbsp;·&nbsp; `disabled by default`

Owns accreditation submissions and evidence across the institution.

> Seeded inactive — an Institution Administrator must enable this role before it can be assigned.

**6** menu sections visible · **0** with write access · **7** permission codes granted

**Dashboard** (`/`)
  Content adapts by role rather than by a permission gate: the Student role sees a read-only “My Attainment” panel in place of the usual overview. Anyone holding section.view (teaches courses) sees a personalized Faculty Courses panel instead of the generic overview. Anyone holding academic_calendar.view additionally sees a Current Term card (added 2026-09-12) surfacing the active academic term, or a prompt to set one up if none is active. Anyone holding assessment.approve additionally sees a “documents awaiting review” card — itself just a link, not a write surface.

**Program & Curriculum** (`/program-settings`)
  - Curriculum — **Read** _Creating/editing a program version needs program.manage; advancing its status needs program.approve._
  - Mission & Vision — **Read** _Institutional/program mission and numbered visions, plus the Institutional Vision ↔ Program Vision mapping; program_outcome_framework.manage to write._
  - PEOs — **Read** _program_outcome_framework.manage to write and to advance status; curriculum_feedback.create shows a Provide Feedback action instead of Advance._
  - Program Outcomes — **Read** _program_outcome_framework.manage to write and to advance status; curriculum_feedback.create shows a Provide Feedback action instead of Advance._
  - Performance Indicators — **Read** _Only shown when the curriculum uses the Indicator-Based PO method; program_outcome_framework.manage to write, same code to advance status._
  - Feedback — **Read** _Everyone who can see this tab can submit feedback (curriculum_feedback.create) or just read it; reviewing/resolving a submission needs program_outcome_framework.manage._

**Outcome Mapping** (`/outcome-mapping`)
  - PEO-PO Mapping — **Read**
  - Course Outcome Mapping — **Read** _Editing also requires one specific course selected, not the institution-wide aggregate view._
  - K/CEP/CEA Mapping — **Read** _Knowledge Profile / Complex Engineering Problem / Complex Engineering Activity mappings, one write permission for all three._
  - Accreditation Framework — **Read** _Read-only for every role — the accreditation body’s own catalogue, not tenant-editable data. — Program Outcomes (POs); Knowledge Profiles (WK); Problem Attributes (WP); Engineering Activities (EA)_

**Analytics** (`/analytics`)
  - PO Attainment — **Read** _Read-only analysis for most viewers; recalculating/configuring thresholds needs attainment.calculate or program.manage._
  - Program Analytics — **Read** _Read-only roll-up — no write action exists on this tab for any role._

**Institute Settings** (`/organization`)
  - Institution — **Read** _Campuses are managed inline on this same tab, not a separate one — org.manage to write them. — Campuses — embedded card, write needs org.manage_
  - Schools — **Read**
  - Departments — **Read**
  - Programs — **Read**
  - Audit log — **Read** _Read-only — audit entries aren't editable._

**About** (`/about`)
  Static, informational — the same for everyone.

---

### Dean

*Scope: One school* &nbsp;·&nbsp; `disabled by default`

School-level oversight of curriculum and program approvals.

> Seeded inactive — an Institution Administrator must enable this role before it can be assigned.

**7** menu sections visible · **0** with write access · **7** permission codes granted

**Dashboard** (`/`)
  Content adapts by role rather than by a permission gate: the Student role sees a read-only “My Attainment” panel in place of the usual overview. Anyone holding section.view (teaches courses) sees a personalized Faculty Courses panel instead of the generic overview. Anyone holding academic_calendar.view additionally sees a Current Term card (added 2026-09-12) surfacing the active academic term, or a prompt to set one up if none is active. Anyone holding assessment.approve additionally sees a “documents awaiting review” card — itself just a link, not a write surface.

**Program & Curriculum** (`/program-settings`)
  - Curriculum — **Read** _Creating/editing a program version needs program.manage; advancing its status needs program.approve._
  - Mission & Vision — **Read** _Institutional/program mission and numbered visions, plus the Institutional Vision ↔ Program Vision mapping; program_outcome_framework.manage to write._
  - PEOs — **Read** _program_outcome_framework.manage to write and to advance status; curriculum_feedback.create shows a Provide Feedback action instead of Advance._
  - Program Outcomes — **Read** _program_outcome_framework.manage to write and to advance status; curriculum_feedback.create shows a Provide Feedback action instead of Advance._
  - Performance Indicators — **Read** _Only shown when the curriculum uses the Indicator-Based PO method; program_outcome_framework.manage to write, same code to advance status._
  - Feedback — **Read** _Everyone who can see this tab can submit feedback (curriculum_feedback.create) or just read it; reviewing/resolving a submission needs program_outcome_framework.manage._

**Outcome Mapping** (`/outcome-mapping`)
  - PEO-PO Mapping — **Read**
  - Course Outcome Mapping — **Read** _Editing also requires one specific course selected, not the institution-wide aggregate view._
  - K/CEP/CEA Mapping — **Read** _Knowledge Profile / Complex Engineering Problem / Complex Engineering Activity mappings, one write permission for all three._
  - Accreditation Framework — **Read** _Read-only for every role — the accreditation body’s own catalogue, not tenant-editable data. — Program Outcomes (POs); Knowledge Profiles (WK); Problem Attributes (WP); Engineering Activities (EA)_

**Course Level Settings** (`/course-settings`)
  - Courses — **Read** _All courses / by category — a client-side filter, not permission-gated. No workflow/approve step exists for a course itself._
  - Course versions — **Read** _Creating/editing a version needs outcome.create; advancing its workflow status (draft→submitted→…→published) additionally needs outcome.approve._
  - Course Outcomes — **Read** _Same split as Course versions: outcome.create to write, outcome.approve to advance status._

**Analytics** (`/analytics`)
  - PO Attainment — **Read** _Read-only analysis for most viewers; recalculating/configuring thresholds needs attainment.calculate or program.manage._
  - Program Analytics — **Read** _Read-only roll-up — no write action exists on this tab for any role._

**Institute Settings** (`/organization`)
  - Institution — **Read** _Campuses are managed inline on this same tab, not a separate one — org.manage to write them. — Campuses — embedded card, write needs org.manage_
  - Schools — **Read**
  - Departments — **Read**
  - Programs — **Read**
  - Users & roles — **Read** _user.manage to create/deactivate accounts; role.manage to change what a role grants — and, as of 2026-09-12, to create brand-new custom roles with their own permission set (system-seeded roles keep name/permissions locked; only is_active/description are editable for those)._

**About** (`/about`)
  Static, informational — the same for everyone.

---

### Head of Department

*Scope: One department* &nbsp;·&nbsp; `disabled by default`

Department-level curriculum and assessment oversight. Notably holds `assessment.approve` — so, unlike the pre-2026-09-12 version of this doc, it *does* have an Assessment nav entry, just limited to the Attainment and Pending documents tabs (it lacks `assessment.view`, so the other five tabs stay hidden).

> Seeded inactive — an Institution Administrator must enable this role before it can be assigned.

**10** menu sections visible · **5** with write access · **11** permission codes granted

**Dashboard** (`/`)
  Content adapts by role rather than by a permission gate: the Student role sees a read-only “My Attainment” panel in place of the usual overview. Anyone holding section.view (teaches courses) sees a personalized Faculty Courses panel instead of the generic overview. Anyone holding academic_calendar.view additionally sees a Current Term card (added 2026-09-12) surfacing the active academic term, or a prompt to set one up if none is active. Anyone holding assessment.approve additionally sees a “documents awaiting review” card — itself just a link, not a write surface.

**Program & Curriculum** (`/program-settings`)
  - Curriculum — **Read** _Creating/editing a program version needs program.manage; advancing its status needs program.approve._
  - Mission & Vision — **Read** _Institutional/program mission and numbered visions, plus the Institutional Vision ↔ Program Vision mapping; program_outcome_framework.manage to write._
  - PEOs — **Read** _program_outcome_framework.manage to write and to advance status; curriculum_feedback.create shows a Provide Feedback action instead of Advance._
  - Program Outcomes — **Read** _program_outcome_framework.manage to write and to advance status; curriculum_feedback.create shows a Provide Feedback action instead of Advance._
  - Performance Indicators — **Read** _Only shown when the curriculum uses the Indicator-Based PO method; program_outcome_framework.manage to write, same code to advance status._
  - Feedback — **Read** _Everyone who can see this tab can submit feedback (curriculum_feedback.create) or just read it; reviewing/resolving a submission needs program_outcome_framework.manage._

**Outcome Mapping** (`/outcome-mapping`)
  - PEO-PO Mapping — **Read**
  - Course Outcome Mapping — **Read + Write** _Editing also requires one specific course selected, not the institution-wide aggregate view._
  - K/CEP/CEA Mapping — **Read** _Knowledge Profile / Complex Engineering Problem / Complex Engineering Activity mappings, one write permission for all three._
  - Accreditation Framework — **Read** _Read-only for every role — the accreditation body’s own catalogue, not tenant-editable data. — Program Outcomes (POs); Knowledge Profiles (WK); Problem Attributes (WP); Engineering Activities (EA)_

**Course Level Settings** (`/course-settings`)
  - Courses — **Read + Write** _All courses / by category — a client-side filter, not permission-gated. No workflow/approve step exists for a course itself._
  - Course versions — **Read + Write** _Creating/editing a version needs outcome.create; advancing its workflow status (draft→submitted→…→published) additionally needs outcome.approve._
  - Course Outcomes — **Read + Write** _Same split as Course versions: outcome.create to write, outcome.approve to advance status._

**Trimester Management** (`/academic`)
  - Course offerings — **Read + Write**
  - Sections — **Read + Write**
  - Faculty assignments — **Read + Write**
  - Enrollments — **Read**
  - Students — **Read**
  - Student cohorts — **Read + Write** _Viewing a cohort's roster is open to anyone who can see this tab; there is no edit or delete action for a cohort at all, only creation._

**Courses** (`/courses`)
  Read-only personal roster — current/previous sections taught, students, and a nudge for anything needing attention. No write actions exist on this page.

**Assessment** (`/assessment`)
  - Attainment — **Read + Write** _Recalculating/locking attainment or editing its thresholds needs attainment.calculate or assessment.approve; otherwise read-only._
  - Pending documents — **Read + Write** _The whole tab is a review queue — reaching it at all already requires assessment.approve._

**Analytics** (`/analytics`)
  - PO Attainment — **Read** _Read-only analysis for most viewers; recalculating/configuring thresholds needs attainment.calculate or program.manage._
  - Program Analytics — **Read** _Read-only roll-up — no write action exists on this tab for any role._
  - Course Attainment — **Read + Write** _Same component as Assessment → Attainment, reused here at the course level; excluded for a Faculty-only viewer (see My Courses)._

**Institute Settings** (`/organization`)
  - Institution — **Read** _Campuses are managed inline on this same tab, not a separate one — org.manage to write them. — Campuses — embedded card, write needs org.manage_
  - Schools — **Read**
  - Departments — **Read**
  - Programs — **Read**
  - Users & roles — **Read** _user.manage to create/deactivate accounts; role.manage to change what a role grants — and, as of 2026-09-12, to create brand-new custom roles with their own permission set (system-seeded roles keep name/permissions locked; only is_active/description are editable for those)._

**About** (`/about`)
  Static, informational — the same for everyone.

---

### Examination/Assessment Administrator

*Scope: Whole tenant* &nbsp;·&nbsp; `disabled by default`

Institution-wide assessment scheduling and approval. Holds `section.view` (not `section.manage`) and no `curriculum.view`/`program.view` at all — so Trimester Management, Program & Curriculum, Course Level Settings, and Outcome Mapping are all correctly absent, leaving only Courses/Question Bank/Assessment/Analytics.

> Seeded inactive — an Institution Administrator must enable this role before it can be assigned.

**6** menu sections visible · **2** with write access · **7** permission codes granted

**Dashboard** (`/`)
  Content adapts by role rather than by a permission gate: the Student role sees a read-only “My Attainment” panel in place of the usual overview. Anyone holding section.view (teaches courses) sees a personalized Faculty Courses panel instead of the generic overview. Anyone holding academic_calendar.view additionally sees a Current Term card (added 2026-09-12) surfacing the active academic term, or a prompt to set one up if none is active. Anyone holding assessment.approve additionally sees a “documents awaiting review” card — itself just a link, not a write surface.

**Courses** (`/courses`)
  Read-only personal roster — current/previous sections taught, students, and a nudge for anything needing attention. No write actions exist on this page.

**Question Bank** (`/question-bank`)
  Read — own + globally-shared questions across courses. The one write control (“Shared globally” toggle) isn't permission-gated — it's available on a question only to its own author, regardless of role.

**Assessment** (`/assessment`)
  - Assessment types — **Read + Write**
  - Rubrics — **Read + Write**
  - Question bank — **Read + Write** _assessment.create to write/create a question; advancing its status needs assessment.approve. Every question opens a Mappings panel (Bloom’s level + CO mapping) under the same assessment.create gate._
  - Assessments — **Read + Write** _assessment.create to write/attach questions; advancing status needs assessment.approve. The Documents panel (question paper, moderation/compliance forms, scripts, CEP docs) is upload = assessment.create, review/approve/extend-deadline = assessment.approve._
  - Marks entry — **Read + Write**
  - Attainment — **Read + Write** _Recalculating/locking attainment or editing its thresholds needs attainment.calculate or assessment.approve; otherwise read-only._
  - Pending documents — **Read + Write** _The whole tab is a review queue — reaching it at all already requires assessment.approve._

**Analytics** (`/analytics`)
  - Course Attainment — **Read + Write** _Same component as Assessment → Attainment, reused here at the course level; excluded for a Faculty-only viewer (see My Courses)._

**About** (`/about`)
  Static, informational — the same for everyone.

---

### Quality Assurance Officer

*Scope: Whole tenant* &nbsp;·&nbsp; `disabled by default`

Monitors attainment results and survey cycles for institutional QA. Holds `audit.view`, giving it a narrow Institute Settings entry (Audit log only) not previously documented.

> Seeded inactive — an Institution Administrator must enable this role before it can be assigned.

**6** menu sections visible · **1** with write access · **6** permission codes granted

**Dashboard** (`/`)
  Content adapts by role rather than by a permission gate: the Student role sees a read-only “My Attainment” panel in place of the usual overview. Anyone holding section.view (teaches courses) sees a personalized Faculty Courses panel instead of the generic overview. Anyone holding academic_calendar.view additionally sees a Current Term card (added 2026-09-12) surfacing the active academic term, or a prompt to set one up if none is active. Anyone holding assessment.approve additionally sees a “documents awaiting review” card — itself just a link, not a write surface.

**Program & Curriculum** (`/program-settings`)
  - Mission & Vision — **Read** _Institutional/program mission and numbered visions, plus the Institutional Vision ↔ Program Vision mapping; program_outcome_framework.manage to write._
  - PEOs — **Read** _program_outcome_framework.manage to write and to advance status; curriculum_feedback.create shows a Provide Feedback action instead of Advance._
  - Program Outcomes — **Read** _program_outcome_framework.manage to write and to advance status; curriculum_feedback.create shows a Provide Feedback action instead of Advance._
  - Performance Indicators — **Read** _Only shown when the curriculum uses the Indicator-Based PO method; program_outcome_framework.manage to write, same code to advance status._
  - Feedback — **Read** _Everyone who can see this tab can submit feedback (curriculum_feedback.create) or just read it; reviewing/resolving a submission needs program_outcome_framework.manage._

**Outcome Mapping** (`/outcome-mapping`)
  - PEO-PO Mapping — **Read**
  - Course Outcome Mapping — **Read** _Editing also requires one specific course selected, not the institution-wide aggregate view._
  - K/CEP/CEA Mapping — **Read** _Knowledge Profile / Complex Engineering Problem / Complex Engineering Activity mappings, one write permission for all three._
  - Accreditation Framework — **Read** _Read-only for every role — the accreditation body’s own catalogue, not tenant-editable data. — Program Outcomes (POs); Knowledge Profiles (WK); Problem Attributes (WP); Engineering Activities (EA)_

**Analytics** (`/analytics`)
  - Course Attainment — **Read + Write** _Same component as Assessment → Attainment, reused here at the course level; excluded for a Faculty-only viewer (see My Courses)._

**Institute Settings** (`/organization`)
  - Audit log — **Read** _Read-only — audit entries aren't editable._

**About** (`/about`)
  Static, informational — the same for everyone.

---

### Accreditation Reviewer

*Scope: Assigned criteria* &nbsp;·&nbsp; `disabled by default`

Reviews submitted evidence against accreditation criteria (typically external/part-time).

> Seeded inactive — an Institution Administrator must enable this role before it can be assigned.

**4** menu sections visible · **0** with write access · **3** permission codes granted

**Dashboard** (`/`)
  Content adapts by role rather than by a permission gate: the Student role sees a read-only “My Attainment” panel in place of the usual overview. Anyone holding section.view (teaches courses) sees a personalized Faculty Courses panel instead of the generic overview. Anyone holding academic_calendar.view additionally sees a Current Term card (added 2026-09-12) surfacing the active academic term, or a prompt to set one up if none is active. Anyone holding assessment.approve additionally sees a “documents awaiting review” card — itself just a link, not a write surface.

**Program & Curriculum** (`/program-settings`)
  - Mission & Vision — **Read** _Institutional/program mission and numbered visions, plus the Institutional Vision ↔ Program Vision mapping; program_outcome_framework.manage to write._
  - PEOs — **Read** _program_outcome_framework.manage to write and to advance status; curriculum_feedback.create shows a Provide Feedback action instead of Advance._
  - Program Outcomes — **Read** _program_outcome_framework.manage to write and to advance status; curriculum_feedback.create shows a Provide Feedback action instead of Advance._
  - Performance Indicators — **Read** _Only shown when the curriculum uses the Indicator-Based PO method; program_outcome_framework.manage to write, same code to advance status._
  - Feedback — **Read** _Everyone who can see this tab can submit feedback (curriculum_feedback.create) or just read it; reviewing/resolving a submission needs program_outcome_framework.manage._

**Outcome Mapping** (`/outcome-mapping`)
  - PEO-PO Mapping — **Read**
  - Course Outcome Mapping — **Read** _Editing also requires one specific course selected, not the institution-wide aggregate view._
  - K/CEP/CEA Mapping — **Read** _Knowledge Profile / Complex Engineering Problem / Complex Engineering Activity mappings, one write permission for all three._
  - Accreditation Framework — **Read** _Read-only for every role — the accreditation body’s own catalogue, not tenant-editable data. — Program Outcomes (POs); Knowledge Profiles (WK); Problem Attributes (WP); Engineering Activities (EA)_

**About** (`/about`)
  Static, informational — the same for everyone.

---

### External Stakeholder

*Scope: Survey only* &nbsp;·&nbsp; `disabled by default`

Employers/alumni/advisory-board members — survey participation only once that module ships; no menu access today.

> Seeded inactive — an Institution Administrator must enable this role before it can be assigned.

**2** menu sections visible · **0** with write access · **0** permission codes granted

**Dashboard** (`/`)
  Content adapts by role rather than by a permission gate: the Student role sees a read-only “My Attainment” panel in place of the usual overview. Anyone holding section.view (teaches courses) sees a personalized Faculty Courses panel instead of the generic overview. Anyone holding academic_calendar.view additionally sees a Current Term card (added 2026-09-12) surfacing the active academic term, or a prompt to set one up if none is active. Anyone holding assessment.approve additionally sees a “documents awaiting review” card — itself just a link, not a write surface.

**About** (`/about`)
  Static, informational — the same for everyone.

---

## Separate system

### Platform Administrator

*Scope: Cross-institution* &nbsp;·&nbsp; `separate login`

A completely separate login (/platform-login), outside the tenant permission system entirely. Creates institutions and can browse/edit raw data across every institution.

| Menu section | Access | Notes |
|---|---|---|
| **Platform Dashboard** (`/platform`) | Read + Write | Lists every institution on the deployment. *Create institution* provisions a brand-new tenant schema, seeded roles/permissions/assessment types/Bloom levels, and optionally demo data. As of 2026-09-12, also supports creating/resetting an Institution Administrator account for an already-provisioned institution, and changing an institution's status (trial/active/suspended/archived) — suspending or archiving immediately blocks all tenant requests via `TenancyMiddleware`. |
| **Role Templates** (`/platform/role-templates`) | Read + Write | New 2026-09-12. The platform-editable default "user type" catalogue (`public.role_templates`) every newly-provisioned institution seeds its own `roles` table from — a platform admin can add/edit/deactivate templates here; an institution admin never sees or touches this table, only their own tenant's `roles` (`POST/PATCH /users/roles`). |
| **Platform Raw Data Console** (`/platform/raw-data`) | Read + Write | Cross-institution table browser/editor — not governed by the tenant permission system at all; any platform admin has full access to every institution’s tables. |

---

## Permission code reference

The complete fixed catalogue (`backend/app/core/permissions.py`, 54 codes) — a role's grants (above) are always a subset of these; the tenant `permissions` table is seeded from this list once per tenant and never edited per-institution.

| Code | Module | Unlocks |
|---|---|---|
| `institution.manage` | institution | Create/update/suspend institutions (platform-level; no tenant role holds this) |
| `institution.view` | institution | View institution details |
| `org.manage` | org | Create/update/deactivate campuses/schools/departments |
| `org.view` | org | View organizational structure |
| `program.manage` | org | Create/update programs and program versions |
| `program.view` | org | View programs and program versions |
| `program.approve` | org | Approve/publish a program version |
| `academic_calendar.manage` | org | Manage academic years/terms |
| `academic_calendar.view` | org | View academic years/terms |
| `term_commit.manage` | org | Enable early Final Commit for a term and permanently commit it, locking every assessment/marks/attainment write for that term in one's own program |
| `user.manage` | identity | Create/update/deactivate users within a tenant |
| `user.view` | identity | View users within a tenant |
| `role.manage` | identity | Create/update roles and role-permission grants (includes, as of 2026-09-12, creating brand-new custom roles) |
| `role.view` | identity | View roles and permissions |
| `program_role.manage` | identity | Grant/revoke Faculty and Section Coordinator roles for people within one's own program |
| `curriculum.view` | curriculum | View curriculum (PEOs/POs/PSOs/COs) |
| `outcome.create` | curriculum | Create outcome definitions (course-level) |
| `outcome.approve` | curriculum | Approve outcome definitions (course-level) |
| `mapping.create` | curriculum | Create outcome mappings (course-level, incl. CO↔PO) |
| `program_outcome_framework.manage` | curriculum | Create/edit/publish program-level outcome framework (PEOs, POs, PO↔PEO mappings) — distinct from the course-level codes above |
| `curriculum_feedback.create` | curriculum | Submit feedback on a read-only Program & Curriculum item |
| `section.manage` | delivery | Manage course offerings, sections, and faculty assignments |
| `section.view` | delivery | View course offerings, sections, and faculty assignments |
| `student.manage` | delivery | Create/update students, enrollments, and curriculum alignment |
| `student.view` | delivery | View students, enrollments, and curriculum alignment |
| `grading.manage` | delivery | Manage grading policies (also gates the Grading nav item's visibility) |
| `grading.view` | delivery | View grading policies |
| `assessment.create` | assessment | Create assessments/questions |
| `assessment.approve` | assessment | Approve assessments (also gates the Assessment nav item's visibility) |
| `assessment.view` | assessment | View assessments/questions (also gates the Question Bank nav item's visibility) |
| `marks.enter` | assessment | Enter/record student marks |
| `attainment.calculate` | attainment | Trigger an attainment calculation run |
| `attainment.approve` | attainment | Approve attainment results |
| `survey.manage` | survey | Create/manage survey templates and instances |
| `evidence.upload` | accreditation | Upload accreditation evidence |
| `accreditation.manage` | accreditation | Manage accreditation submissions |
| `report.generate` | reporting | Generate reports |
| `audit.view` | audit | View audit logs |
| `raw_data.manage_all` | raw_data | Raw table read/write/delete across every institution |
| `raw_data.manage_institution` | raw_data | Raw table read/write/delete within one's own institution |
| `raw_data.manage_scoped` | raw_data | Raw table read/write/delete within one's own program or course scope |
| `raw_data.propose_scoped` | raw_data | Raw table read + write-by-proposal (pending approval) within one's own program's course-level tables; program-level tables read-only |
| `raw_data.approve` | raw_data | Approve or reject pending raw-data change proposals |
| `course_file.configure` | course_files | Configure per-semester course-file requirements (required/optional, deadlines) |
| `course_file.upload` | course_files | Upload course files for an assigned section |
| `course_file.review` | course_files | Approve/reject submitted course files |
| `course_file.view` | course_files | View course files and their requirements |
| `course_change_request.create` | course_change_request | Propose a change to admin-controlled course information |
| `course_change_request.review` | course_change_request | Approve or reject a course change request |
| `course_type.manage` | course_change_request | Add/deactivate Course Types and configure which course-level sections are editable per type |
| `course_change_request.review_admin` | course_change_request | Stage-1 (Section Coordinator) review of a course change request |
| `course_change_request.review_program` | course_change_request | Stage-2 (Program Coordinator) final review of a two-stage course change request |
