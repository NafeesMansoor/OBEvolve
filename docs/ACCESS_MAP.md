# OBEvolve Access Map

Every role, every menu item, every tab — and whether that role can just look, or actually change something. Generated from the live permission catalogue (`backend/app/core/permissions.py`), default role grants (`backend/app/seed/default_roles.py`), and the frontend’s actual navigation/tab gating — not a hand-maintained description of it. If the code changes, this doc goes stale; regenerate rather than hand-edit.

Interactive version: [Access Map](https://claude.ai/code/artifact/f984e975-d442-4367-8a1e-df55b14d53b8) (role picker + the same data, browsable).

**Legend** — **Read**: can view. **Read + Write**: can create / edit / approve. Sections not listed for a role aren’t in that role’s sidebar at all.

## Contents

**Active by default**
- [Super Administrator](#super-administrator)
- [Institution Administrator](#institution-administrator)
- [Program Administrator](#program-administrator)
- [Program Coordinator](#program-coordinator)
- [Course Administrator](#course-administrator)
- [Faculty](#faculty)
- [Course Coordinator](#course-coordinator)
- [Student](#student)

**Seeded, disabled by default**
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

### Super Administrator

*Scope: Whole tenant* &nbsp;·&nbsp; `active`

Full control within the institution’s tenant, including raw-data access to every institution via the ALL sentinel.

**10** menu sections visible · **8** with write access · **39** permission codes granted

**Dashboard** (`/`)
  Content adapts by role rather than by a permission gate: the Student role sees a read-only “My Attainment” panel in place of the usual overview. Anyone holding assessment.approve additionally sees a “documents awaiting review” card — itself just a link, not a write surface.

**Course Level Settings** (`/course-settings`)
  - Courses — **Read + Write** — All courses / by category — a client-side filter, not permission-gated
  - Course versions — **Read + Write** _Creating/editing a version needs outcome.create; advancing its workflow status (draft→submitted→…→published) additionally needs outcome.approve._
  - Course Outcomes — **Read + Write** _Same split as Course versions: outcome.create to write, outcome.approve to advance status._

**Program Level Setting** (`/program-settings`)
  - Curriculum — **Read + Write** _Creating/editing a program version needs program.manage; advancing its status needs program.approve._
  - PEOs — **Read + Write** _outcome.create to write, outcome.approve to advance status._
  - Program Outcomes — **Read + Write** _outcome.create to write, outcome.approve to advance status._
  - CO-PO Mapping — **Read + Write**
  - PEO-PO Mapping — **Read + Write**
  - Accreditation Framework — **Read** _Read-only for every role — the accreditation body’s own catalogue, not tenant-editable data._ — Program Outcomes (POs); Knowledge Profiles (WK); Problem Attributes (WP); Engineering Activities (EA)

**Academic Operations** (`/academic`)
  - Course offerings — **Read + Write**
  - Sections — **Read + Write**
  - Faculty assignments — **Read + Write**
  - Enrollments — **Read + Write**
  - Students — **Read + Write**
  - Academic calendar — **Read + Write**

**Grading** (`/grading`)
  - Grading policies — **Read + Write** — Grade bands — nested inside each policy, same permission

**Assessment** (`/assessment`)
  - Assessment types — **Read + Write**
  - Rubrics — **Read + Write**
  - Question bank — **Read + Write** _assessment.create to write/create a question; advancing its status needs assessment.approve. Every question opens a Mappings panel (Bloom’s level + CO mapping) under the same assessment.create gate._ — Mappings panel — Bloom’s cognitive level + course-outcome mapping per question
  - Assessments — **Read + Write** _assessment.create to write/attach questions; advancing status needs assessment.approve. The Documents panel (question paper, moderation/compliance forms, scripts, CEP docs) is upload = assessment.create, review/approve = assessment.approve._ — Attach Questions panel — assessment.create; Documents panel — upload: assessment.create · review/approve: assessment.approve
  - Marks entry — **Read + Write**
  - Attainment — **Read + Write** _Recalculating/locking attainment needs attainment.calculate or assessment.approve; otherwise read-only._
  - Pending documents — **Read + Write** _The whole tab is a review queue — visible only to Course Coordinators / Program Administrators / anyone else holding assessment.approve._

**Analytics** (`/analytics`)
  - PO Attainment — **Read + Write** _Read-only analysis for most roles; recalculating/configuring thresholds needs attainment.calculate or program.manage._
  - Program Analytics — **Read** _Read-only roll-up — no write action exists on this tab for any role._
  - Course Attainment — **Read + Write** _Same component as Assessment → Attainment, reused here at the course level._

**Institute Settings** (`/organization`)
  - Institution — **Read + Write** _Campuses are managed inline on this same tab, not a separate one — org.manage to write them._ — Campuses — embedded card, write needs org.manage
  - Schools — **Read + Write**
  - Departments — **Read + Write**
  - Programs — **Read + Write**
  - Users & roles — **Read + Write** _user.manage to create/deactivate accounts; role.manage to change what a role grants._

**Raw Data Console** (`/raw-data`)
  Tiered access — Every institution — read/write/delete any table (`raw_data.manage_all`)

**About** (`/about`)
  Static, informational — the same for everyone.

---

### Institution Administrator

*Scope: Whole tenant* &nbsp;·&nbsp; `active`

Manages org structure, programs, curriculum, delivery, and users — the day-to-day admin a Super Administrator delegates to. Raw-data console scoped to this institution.

**10** menu sections visible · **8** with write access · **29** permission codes granted

**Dashboard** (`/`)
  Content adapts by role rather than by a permission gate: the Student role sees a read-only “My Attainment” panel in place of the usual overview. Anyone holding assessment.approve additionally sees a “documents awaiting review” card — itself just a link, not a write surface.

**Course Level Settings** (`/course-settings`)
  - Courses — **Read + Write** — All courses / by category — a client-side filter, not permission-gated
  - Course versions — **Read + Write** _Creating/editing a version needs outcome.create; advancing its workflow status (draft→submitted→…→published) additionally needs outcome.approve._
  - Course Outcomes — **Read + Write** _Same split as Course versions: outcome.create to write, outcome.approve to advance status._

**Program Level Setting** (`/program-settings`)
  - Curriculum — **Read + Write** _Creating/editing a program version needs program.manage; advancing its status needs program.approve._
  - PEOs — **Read + Write** _outcome.create to write, outcome.approve to advance status._
  - Program Outcomes — **Read + Write** _outcome.create to write, outcome.approve to advance status._
  - CO-PO Mapping — **Read + Write**
  - PEO-PO Mapping — **Read + Write**
  - Accreditation Framework — **Read** _Read-only for every role — the accreditation body’s own catalogue, not tenant-editable data._ — Program Outcomes (POs); Knowledge Profiles (WK); Problem Attributes (WP); Engineering Activities (EA)

**Academic Operations** (`/academic`)
  - Course offerings — **Read + Write**
  - Sections — **Read + Write**
  - Faculty assignments — **Read + Write**
  - Enrollments — **Read + Write**
  - Students — **Read + Write**
  - Academic calendar — **Read + Write**

**Grading** (`/grading`)
  - Grading policies — **Read + Write** — Grade bands — nested inside each policy, same permission

**Assessment** (`/assessment`)
  - Assessment types — **Read + Write**
  - Rubrics — **Read + Write**
  - Question bank — **Read + Write** _assessment.create to write/create a question; advancing its status needs assessment.approve. Every question opens a Mappings panel (Bloom’s level + CO mapping) under the same assessment.create gate._ — Mappings panel — Bloom’s cognitive level + course-outcome mapping per question
  - Assessments — **Read + Write** _assessment.create to write/attach questions; advancing status needs assessment.approve. The Documents panel (question paper, moderation/compliance forms, scripts, CEP docs) is upload = assessment.create, review/approve = assessment.approve._ — Attach Questions panel — assessment.create; Documents panel — upload: assessment.create · review/approve: assessment.approve
  - Marks entry — **Read + Write**
  - Attainment — **Read + Write** _Recalculating/locking attainment needs attainment.calculate or assessment.approve; otherwise read-only._
  - Pending documents — **Read + Write** _The whole tab is a review queue — visible only to Course Coordinators / Program Administrators / anyone else holding assessment.approve._

**Analytics** (`/analytics`)
  - PO Attainment — **Read + Write** _Read-only analysis for most roles; recalculating/configuring thresholds needs attainment.calculate or program.manage._
  - Program Analytics — **Read** _Read-only roll-up — no write action exists on this tab for any role._
  - Course Attainment — **Read + Write** _Same component as Assessment → Attainment, reused here at the course level._

**Institute Settings** (`/organization`)
  - Institution — **Read** _Campuses are managed inline on this same tab, not a separate one — org.manage to write them._ — Campuses — embedded card, write needs org.manage
  - Schools — **Read + Write**
  - Departments — **Read + Write**
  - Programs — **Read + Write**
  - Users & roles — **Read + Write** _user.manage to create/deactivate accounts; role.manage to change what a role grants._

**Raw Data Console** (`/raw-data`)
  Tiered access — Own institution — read/write/delete any tenant table (`raw_data.manage_institution`)

**About** (`/about`)
  Static, informational — the same for everyone.

---

### Program Administrator

*Scope: One program* &nbsp;·&nbsp; `active`

Full control over one program’s data — the program-scoped peer of Institution Administrator. Approves Program Coordinators’ pending raw-data changes.

**10** menu sections visible · **7** with write access · **18** permission codes granted

**Dashboard** (`/`)
  Content adapts by role rather than by a permission gate: the Student role sees a read-only “My Attainment” panel in place of the usual overview. Anyone holding assessment.approve additionally sees a “documents awaiting review” card — itself just a link, not a write surface.

**Course Level Settings** (`/course-settings`)
  - Courses — **Read + Write** — All courses / by category — a client-side filter, not permission-gated
  - Course versions — **Read + Write** _Creating/editing a version needs outcome.create; advancing its workflow status (draft→submitted→…→published) additionally needs outcome.approve._
  - Course Outcomes — **Read + Write** _Same split as Course versions: outcome.create to write, outcome.approve to advance status._

**Program Level Setting** (`/program-settings`)
  - Curriculum — **Read** _Creating/editing a program version needs program.manage; advancing its status needs program.approve._
  - PEOs — **Read + Write** _outcome.create to write, outcome.approve to advance status._
  - Program Outcomes — **Read + Write** _outcome.create to write, outcome.approve to advance status._
  - CO-PO Mapping — **Read + Write**
  - PEO-PO Mapping — **Read + Write**
  - Accreditation Framework — **Read** _Read-only for every role — the accreditation body’s own catalogue, not tenant-editable data._ — Program Outcomes (POs); Knowledge Profiles (WK); Problem Attributes (WP); Engineering Activities (EA)

**Academic Operations** (`/academic`)
  - Course offerings — **Read + Write**
  - Sections — **Read + Write**
  - Faculty assignments — **Read + Write**
  - Enrollments — **Read + Write**
  - Students — **Read + Write**

**Grading** (`/grading`)
  - Grading policies — **Read + Write** — Grade bands — nested inside each policy, same permission

**Assessment** (`/assessment`)
  - Assessment types — **Read + Write**
  - Rubrics — **Read + Write**
  - Question bank — **Read + Write** _assessment.create to write/create a question; advancing its status needs assessment.approve. Every question opens a Mappings panel (Bloom’s level + CO mapping) under the same assessment.create gate._ — Mappings panel — Bloom’s cognitive level + course-outcome mapping per question
  - Assessments — **Read + Write** _assessment.create to write/attach questions; advancing status needs assessment.approve. The Documents panel (question paper, moderation/compliance forms, scripts, CEP docs) is upload = assessment.create, review/approve = assessment.approve._ — Attach Questions panel — assessment.create; Documents panel — upload: assessment.create · review/approve: assessment.approve
  - Marks entry — **Read + Write**
  - Attainment — **Read + Write** _Recalculating/locking attainment needs attainment.calculate or assessment.approve; otherwise read-only._
  - Pending documents — **Read + Write** _The whole tab is a review queue — visible only to Course Coordinators / Program Administrators / anyone else holding assessment.approve._

**Analytics** (`/analytics`)
  - PO Attainment — **Read** _Read-only analysis for most roles; recalculating/configuring thresholds needs attainment.calculate or program.manage._
  - Program Analytics — **Read** _Read-only roll-up — no write action exists on this tab for any role._
  - Course Attainment — **Read + Write** _Same component as Assessment → Attainment, reused here at the course level._

**Institute Settings** (`/organization`)
  - Programs — **Read**

**Raw Data Console** (`/raw-data`)
  Tiered access — Own program/course — read/write directly, plus approves others’ pending proposals (`raw_data.manage_scoped, raw_data.approve`)

**About** (`/about`)
  Static, informational — the same for everyone.

---

### Program Coordinator

*Scope: One program* &nbsp;·&nbsp; `active`

Manages semester-level course offerings and curriculum for one program. Cannot touch program-level data (PEOs/POs); raw-data writes go through Program Administrator approval.

**9** menu sections visible · **4** with write access · **11** permission codes granted

**Dashboard** (`/`)
  Content adapts by role rather than by a permission gate: the Student role sees a read-only “My Attainment” panel in place of the usual overview. Anyone holding assessment.approve additionally sees a “documents awaiting review” card — itself just a link, not a write surface.

**Course Level Settings** (`/course-settings`)
  - Courses — **Read + Write** — All courses / by category — a client-side filter, not permission-gated
  - Course versions — **Read + Write** _Creating/editing a version needs outcome.create; advancing its workflow status (draft→submitted→…→published) additionally needs outcome.approve._
  - Course Outcomes — **Read + Write** _Same split as Course versions: outcome.create to write, outcome.approve to advance status._

**Program Level Setting** (`/program-settings`)
  - Curriculum — **Read** _Creating/editing a program version needs program.manage; advancing its status needs program.approve._
  - PEOs — **Read + Write** _outcome.create to write, outcome.approve to advance status._
  - Program Outcomes — **Read + Write** _outcome.create to write, outcome.approve to advance status._
  - CO-PO Mapping — **Read + Write**
  - PEO-PO Mapping — **Read + Write**
  - Accreditation Framework — **Read** _Read-only for every role — the accreditation body’s own catalogue, not tenant-editable data._ — Program Outcomes (POs); Knowledge Profiles (WK); Problem Attributes (WP); Engineering Activities (EA)

**Academic Operations** (`/academic`)
  - Course offerings — **Read + Write**
  - Sections — **Read + Write**
  - Faculty assignments — **Read + Write**
  - Enrollments — **Read**
  - Students — **Read**

**Grading** (`/grading`)
  - Grading policies — **Read** — Grade bands — nested inside each policy, same permission

**Analytics** (`/analytics`)
  - PO Attainment — **Read** _Read-only analysis for most roles; recalculating/configuring thresholds needs attainment.calculate or program.manage._
  - Program Analytics — **Read** _Read-only roll-up — no write action exists on this tab for any role._

**Institute Settings** (`/organization`)
  - Programs — **Read**

**Raw Data Console** (`/raw-data`)
  Tiered access — Own program: program-level tables read-only; course-level tables read + propose (a Program Administrator must approve before it takes effect) (`raw_data.propose_scoped`)

**About** (`/about`)
  Static, informational — the same for everyone.

---

### Course Administrator

*Scope: One course* &nbsp;·&nbsp; `active`

Full control over one course’s data — the course-scoped peer of Program Administrator.

**9** menu sections visible · **6** with write access · **13** permission codes granted

**Dashboard** (`/`)
  Content adapts by role rather than by a permission gate: the Student role sees a read-only “My Attainment” panel in place of the usual overview. Anyone holding assessment.approve additionally sees a “documents awaiting review” card — itself just a link, not a write surface.

**Course Level Settings** (`/course-settings`)
  - Courses — **Read + Write** — All courses / by category — a client-side filter, not permission-gated
  - Course versions — **Read + Write** _Creating/editing a version needs outcome.create; advancing its workflow status (draft→submitted→…→published) additionally needs outcome.approve._
  - Course Outcomes — **Read + Write** _Same split as Course versions: outcome.create to write, outcome.approve to advance status._

**Program Level Setting** (`/program-settings`)
  - PEOs — **Read + Write** _outcome.create to write, outcome.approve to advance status._
  - Program Outcomes — **Read + Write** _outcome.create to write, outcome.approve to advance status._
  - CO-PO Mapping — **Read + Write**
  - PEO-PO Mapping — **Read + Write**
  - Accreditation Framework — **Read** _Read-only for every role — the accreditation body’s own catalogue, not tenant-editable data._ — Program Outcomes (POs); Knowledge Profiles (WK); Problem Attributes (WP); Engineering Activities (EA)

**Academic Operations** (`/academic`)
  - Course offerings — **Read + Write**
  - Sections — **Read + Write**
  - Faculty assignments — **Read + Write**
  - Enrollments — **Read**
  - Students — **Read**

**Grading** (`/grading`)
  - Grading policies — **Read** — Grade bands — nested inside each policy, same permission

**Assessment** (`/assessment`)
  - Assessment types — **Read + Write**
  - Rubrics — **Read + Write**
  - Question bank — **Read + Write** _assessment.create to write/create a question; advancing its status needs assessment.approve. Every question opens a Mappings panel (Bloom’s level + CO mapping) under the same assessment.create gate._ — Mappings panel — Bloom’s cognitive level + course-outcome mapping per question
  - Assessments — **Read + Write** _assessment.create to write/attach questions; advancing status needs assessment.approve. The Documents panel (question paper, moderation/compliance forms, scripts, CEP docs) is upload = assessment.create, review/approve = assessment.approve._ — Attach Questions panel — assessment.create; Documents panel — upload: assessment.create · review/approve: assessment.approve
  - Marks entry — **Read + Write**
  - Attainment — **Read + Write** _Recalculating/locking attainment needs attainment.calculate or assessment.approve; otherwise read-only._
  - Pending documents — **Read + Write** _The whole tab is a review queue — visible only to Course Coordinators / Program Administrators / anyone else holding assessment.approve._

**Analytics** (`/analytics`)
  - Course Attainment — **Read + Write** _Same component as Assessment → Attainment, reused here at the course level._

**Raw Data Console** (`/raw-data`)
  Tiered access — Own program/course — read/write directly (`raw_data.manage_scoped`)

**About** (`/about`)
  Static, informational — the same for everyone.

---

### Faculty

*Scope: Assigned sections* &nbsp;·&nbsp; `active`

Delivers courses: creates assessments and enters marks for sections they teach.

**8** menu sections visible · **2** with write access · **8** permission codes granted

**Dashboard** (`/`)
  Content adapts by role rather than by a permission gate: the Student role sees a read-only “My Attainment” panel in place of the usual overview. Anyone holding assessment.approve additionally sees a “documents awaiting review” card — itself just a link, not a write surface.

**Course Level Settings** (`/course-settings`)
  - Courses — **Read** — All courses / by category — a client-side filter, not permission-gated
  - Course versions — **Read** _Creating/editing a version needs outcome.create; advancing its workflow status (draft→submitted→…→published) additionally needs outcome.approve._
  - Course Outcomes — **Read** _Same split as Course versions: outcome.create to write, outcome.approve to advance status._

**Program Level Setting** (`/program-settings`)
  - PEOs — **Read** _outcome.create to write, outcome.approve to advance status._
  - Program Outcomes — **Read** _outcome.create to write, outcome.approve to advance status._
  - CO-PO Mapping — **Read + Write**
  - PEO-PO Mapping — **Read + Write**
  - Accreditation Framework — **Read** _Read-only for every role — the accreditation body’s own catalogue, not tenant-editable data._ — Program Outcomes (POs); Knowledge Profiles (WK); Problem Attributes (WP); Engineering Activities (EA)

**Academic Operations** (`/academic`)
  - Course offerings — **Read**
  - Sections — **Read**
  - Faculty assignments — **Read**
  - Enrollments — **Read**
  - Students — **Read**

**Grading** (`/grading`)
  - Grading policies — **Read** — Grade bands — nested inside each policy, same permission

**Assessment** (`/assessment`)
  - Assessment types — **Read + Write**
  - Rubrics — **Read + Write**
  - Question bank — **Read + Write** _assessment.create to write/create a question; advancing its status needs assessment.approve. Every question opens a Mappings panel (Bloom’s level + CO mapping) under the same assessment.create gate._ — Mappings panel — Bloom’s cognitive level + course-outcome mapping per question
  - Assessments — **Read + Write** _assessment.create to write/attach questions; advancing status needs assessment.approve. The Documents panel (question paper, moderation/compliance forms, scripts, CEP docs) is upload = assessment.create, review/approve = assessment.approve._ — Attach Questions panel — assessment.create; Documents panel — upload: assessment.create · review/approve: assessment.approve
  - Marks entry — **Read + Write**
  - Attainment — **Read** _Recalculating/locking attainment needs attainment.calculate or assessment.approve; otherwise read-only._

**Analytics** (`/analytics`)
  - Course Attainment — **Read** _Same component as Assessment → Attainment, reused here at the course level._

**About** (`/about`)
  Static, informational — the same for everyone.

---

### Course Coordinator

*Scope: One course* &nbsp;·&nbsp; `active`

Owns one course’s assessment plan and approves marks entry for its sections — Faculty plus assessment.approve.

**8** menu sections visible · **3** with write access · **9** permission codes granted

**Dashboard** (`/`)
  Content adapts by role rather than by a permission gate: the Student role sees a read-only “My Attainment” panel in place of the usual overview. Anyone holding assessment.approve additionally sees a “documents awaiting review” card — itself just a link, not a write surface.

**Course Level Settings** (`/course-settings`)
  - Courses — **Read** — All courses / by category — a client-side filter, not permission-gated
  - Course versions — **Read** _Creating/editing a version needs outcome.create; advancing its workflow status (draft→submitted→…→published) additionally needs outcome.approve._
  - Course Outcomes — **Read** _Same split as Course versions: outcome.create to write, outcome.approve to advance status._

**Program Level Setting** (`/program-settings`)
  - PEOs — **Read** _outcome.create to write, outcome.approve to advance status._
  - Program Outcomes — **Read** _outcome.create to write, outcome.approve to advance status._
  - CO-PO Mapping — **Read + Write**
  - PEO-PO Mapping — **Read + Write**
  - Accreditation Framework — **Read** _Read-only for every role — the accreditation body’s own catalogue, not tenant-editable data._ — Program Outcomes (POs); Knowledge Profiles (WK); Problem Attributes (WP); Engineering Activities (EA)

**Academic Operations** (`/academic`)
  - Course offerings — **Read**
  - Sections — **Read**
  - Faculty assignments — **Read**
  - Enrollments — **Read**
  - Students — **Read**

**Grading** (`/grading`)
  - Grading policies — **Read** — Grade bands — nested inside each policy, same permission

**Assessment** (`/assessment`)
  - Assessment types — **Read + Write**
  - Rubrics — **Read + Write**
  - Question bank — **Read + Write** _assessment.create to write/create a question; advancing its status needs assessment.approve. Every question opens a Mappings panel (Bloom’s level + CO mapping) under the same assessment.create gate._ — Mappings panel — Bloom’s cognitive level + course-outcome mapping per question
  - Assessments — **Read + Write** _assessment.create to write/attach questions; advancing status needs assessment.approve. The Documents panel (question paper, moderation/compliance forms, scripts, CEP docs) is upload = assessment.create, review/approve = assessment.approve._ — Attach Questions panel — assessment.create; Documents panel — upload: assessment.create · review/approve: assessment.approve
  - Marks entry — **Read + Write**
  - Attainment — **Read + Write** _Recalculating/locking attainment needs attainment.calculate or assessment.approve; otherwise read-only._
  - Pending documents — **Read + Write** _The whole tab is a review queue — visible only to Course Coordinators / Program Administrators / anyone else holding assessment.approve._

**Analytics** (`/analytics`)
  - Course Attainment — **Read + Write** _Same component as Assessment → Attainment, reused here at the course level._

**About** (`/about`)
  Static, informational — the same for everyone.

---

### Student

*Scope: Own record* &nbsp;·&nbsp; `active`

Views their own program curriculum. The Dashboard replaces the usual overview with a read-only “My Attainment” panel for this role specifically.

**4** menu sections visible · **0** with write access · **1** permission codes granted

**Dashboard** (`/`)
  Content adapts by role rather than by a permission gate: the Student role sees a read-only “My Attainment” panel in place of the usual overview. Anyone holding assessment.approve additionally sees a “documents awaiting review” card — itself just a link, not a write surface.

**Course Level Settings** (`/course-settings`)
  - Courses — **Read** — All courses / by category — a client-side filter, not permission-gated
  - Course versions — **Read** _Creating/editing a version needs outcome.create; advancing its workflow status (draft→submitted→…→published) additionally needs outcome.approve._
  - Course Outcomes — **Read** _Same split as Course versions: outcome.create to write, outcome.approve to advance status._

**Program Level Setting** (`/program-settings`)
  - PEOs — **Read** _outcome.create to write, outcome.approve to advance status._
  - Program Outcomes — **Read** _outcome.create to write, outcome.approve to advance status._
  - CO-PO Mapping — **Read**
  - PEO-PO Mapping — **Read**
  - Accreditation Framework — **Read** _Read-only for every role — the accreditation body’s own catalogue, not tenant-editable data._ — Program Outcomes (POs); Knowledge Profiles (WK); Problem Attributes (WP); Engineering Activities (EA)

**About** (`/about`)
  Static, informational — the same for everyone.

---

## Seeded, disabled by default

### Accreditation Administrator

*Scope: Whole tenant* &nbsp;·&nbsp; `disabled by default`

Owns accreditation submissions and evidence across the institution.

> Seeded inactive — an Institution Administrator must enable this role before it can be assigned.

**6** menu sections visible · **0** with write access · **7** permission codes granted

**Dashboard** (`/`)
  Content adapts by role rather than by a permission gate: the Student role sees a read-only “My Attainment” panel in place of the usual overview. Anyone holding assessment.approve additionally sees a “documents awaiting review” card — itself just a link, not a write surface.

**Course Level Settings** (`/course-settings`)
  - Courses — **Read** — All courses / by category — a client-side filter, not permission-gated
  - Course versions — **Read** _Creating/editing a version needs outcome.create; advancing its workflow status (draft→submitted→…→published) additionally needs outcome.approve._
  - Course Outcomes — **Read** _Same split as Course versions: outcome.create to write, outcome.approve to advance status._

**Program Level Setting** (`/program-settings`)
  - Curriculum — **Read** _Creating/editing a program version needs program.manage; advancing its status needs program.approve._
  - PEOs — **Read** _outcome.create to write, outcome.approve to advance status._
  - Program Outcomes — **Read** _outcome.create to write, outcome.approve to advance status._
  - CO-PO Mapping — **Read**
  - PEO-PO Mapping — **Read**
  - Accreditation Framework — **Read** _Read-only for every role — the accreditation body’s own catalogue, not tenant-editable data._ — Program Outcomes (POs); Knowledge Profiles (WK); Problem Attributes (WP); Engineering Activities (EA)

**Analytics** (`/analytics`)
  - PO Attainment — **Read** _Read-only analysis for most roles; recalculating/configuring thresholds needs attainment.calculate or program.manage._
  - Program Analytics — **Read** _Read-only roll-up — no write action exists on this tab for any role._

**Institute Settings** (`/organization`)
  - Institution — **Read** _Campuses are managed inline on this same tab, not a separate one — org.manage to write them._ — Campuses — embedded card, write needs org.manage
  - Schools — **Read**
  - Departments — **Read**
  - Programs — **Read**

**About** (`/about`)
  Static, informational — the same for everyone.

---

### Dean

*Scope: One school* &nbsp;·&nbsp; `disabled by default`

School-level oversight of curriculum and program approvals.

> Seeded inactive — an Institution Administrator must enable this role before it can be assigned.

**6** menu sections visible · **0** with write access · **7** permission codes granted

**Dashboard** (`/`)
  Content adapts by role rather than by a permission gate: the Student role sees a read-only “My Attainment” panel in place of the usual overview. Anyone holding assessment.approve additionally sees a “documents awaiting review” card — itself just a link, not a write surface.

**Course Level Settings** (`/course-settings`)
  - Courses — **Read** — All courses / by category — a client-side filter, not permission-gated
  - Course versions — **Read** _Creating/editing a version needs outcome.create; advancing its workflow status (draft→submitted→…→published) additionally needs outcome.approve._
  - Course Outcomes — **Read** _Same split as Course versions: outcome.create to write, outcome.approve to advance status._

**Program Level Setting** (`/program-settings`)
  - Curriculum — **Read** _Creating/editing a program version needs program.manage; advancing its status needs program.approve._
  - PEOs — **Read** _outcome.create to write, outcome.approve to advance status._
  - Program Outcomes — **Read** _outcome.create to write, outcome.approve to advance status._
  - CO-PO Mapping — **Read**
  - PEO-PO Mapping — **Read**
  - Accreditation Framework — **Read** _Read-only for every role — the accreditation body’s own catalogue, not tenant-editable data._ — Program Outcomes (POs); Knowledge Profiles (WK); Problem Attributes (WP); Engineering Activities (EA)

**Analytics** (`/analytics`)
  - PO Attainment — **Read** _Read-only analysis for most roles; recalculating/configuring thresholds needs attainment.calculate or program.manage._
  - Program Analytics — **Read** _Read-only roll-up — no write action exists on this tab for any role._

**Institute Settings** (`/organization`)
  - Institution — **Read** _Campuses are managed inline on this same tab, not a separate one — org.manage to write them._ — Campuses — embedded card, write needs org.manage
  - Schools — **Read**
  - Departments — **Read**
  - Programs — **Read**
  - Users & roles — **Read** _user.manage to create/deactivate accounts; role.manage to change what a role grants._

**About** (`/about`)
  Static, informational — the same for everyone.

---

### Head of Department

*Scope: One department* &nbsp;·&nbsp; `disabled by default`

Department-level curriculum and assessment oversight.

> Seeded inactive — an Institution Administrator must enable this role before it can be assigned.

**8** menu sections visible · **4** with write access · **11** permission codes granted

**Dashboard** (`/`)
  Content adapts by role rather than by a permission gate: the Student role sees a read-only “My Attainment” panel in place of the usual overview. Anyone holding assessment.approve additionally sees a “documents awaiting review” card — itself just a link, not a write surface.

**Course Level Settings** (`/course-settings`)
  - Courses — **Read + Write** — All courses / by category — a client-side filter, not permission-gated
  - Course versions — **Read + Write** _Creating/editing a version needs outcome.create; advancing its workflow status (draft→submitted→…→published) additionally needs outcome.approve._
  - Course Outcomes — **Read + Write** _Same split as Course versions: outcome.create to write, outcome.approve to advance status._

**Program Level Setting** (`/program-settings`)
  - Curriculum — **Read** _Creating/editing a program version needs program.manage; advancing its status needs program.approve._
  - PEOs — **Read + Write** _outcome.create to write, outcome.approve to advance status._
  - Program Outcomes — **Read + Write** _outcome.create to write, outcome.approve to advance status._
  - CO-PO Mapping — **Read + Write**
  - PEO-PO Mapping — **Read + Write**
  - Accreditation Framework — **Read** _Read-only for every role — the accreditation body’s own catalogue, not tenant-editable data._ — Program Outcomes (POs); Knowledge Profiles (WK); Problem Attributes (WP); Engineering Activities (EA)

**Academic Operations** (`/academic`)
  - Course offerings — **Read + Write**
  - Sections — **Read + Write**
  - Faculty assignments — **Read + Write**
  - Enrollments — **Read**
  - Students — **Read**

**Grading** (`/grading`)
  - Grading policies — **Read** — Grade bands — nested inside each policy, same permission

**Analytics** (`/analytics`)
  - PO Attainment — **Read** _Read-only analysis for most roles; recalculating/configuring thresholds needs attainment.calculate or program.manage._
  - Program Analytics — **Read** _Read-only roll-up — no write action exists on this tab for any role._
  - Course Attainment — **Read + Write** _Same component as Assessment → Attainment, reused here at the course level._

**Institute Settings** (`/organization`)
  - Institution — **Read** _Campuses are managed inline on this same tab, not a separate one — org.manage to write them._ — Campuses — embedded card, write needs org.manage
  - Schools — **Read**
  - Departments — **Read**
  - Programs — **Read**
  - Users & roles — **Read** _user.manage to create/deactivate accounts; role.manage to change what a role grants._

**About** (`/about`)
  Static, informational — the same for everyone.

---

### Examination/Assessment Administrator

*Scope: Whole tenant* &nbsp;·&nbsp; `disabled by default`

Institution-wide assessment scheduling and approval.

> Seeded inactive — an Institution Administrator must enable this role before it can be assigned.

**6** menu sections visible · **2** with write access · **7** permission codes granted

**Dashboard** (`/`)
  Content adapts by role rather than by a permission gate: the Student role sees a read-only “My Attainment” panel in place of the usual overview. Anyone holding assessment.approve additionally sees a “documents awaiting review” card — itself just a link, not a write surface.

**Academic Operations** (`/academic`)
  - Course offerings — **Read**
  - Sections — **Read**
  - Faculty assignments — **Read**

**Grading** (`/grading`)
  - Grading policies — **Read** — Grade bands — nested inside each policy, same permission

**Assessment** (`/assessment`)
  - Assessment types — **Read + Write**
  - Rubrics — **Read + Write**
  - Question bank — **Read + Write** _assessment.create to write/create a question; advancing its status needs assessment.approve. Every question opens a Mappings panel (Bloom’s level + CO mapping) under the same assessment.create gate._ — Mappings panel — Bloom’s cognitive level + course-outcome mapping per question
  - Assessments — **Read + Write** _assessment.create to write/attach questions; advancing status needs assessment.approve. The Documents panel (question paper, moderation/compliance forms, scripts, CEP docs) is upload = assessment.create, review/approve = assessment.approve._ — Attach Questions panel — assessment.create; Documents panel — upload: assessment.create · review/approve: assessment.approve
  - Marks entry — **Read + Write**
  - Attainment — **Read + Write** _Recalculating/locking attainment needs attainment.calculate or assessment.approve; otherwise read-only._
  - Pending documents — **Read + Write** _The whole tab is a review queue — visible only to Course Coordinators / Program Administrators / anyone else holding assessment.approve._

**Analytics** (`/analytics`)
  - Course Attainment — **Read + Write** _Same component as Assessment → Attainment, reused here at the course level._

**About** (`/about`)
  Static, informational — the same for everyone.

---

### Quality Assurance Officer

*Scope: Whole tenant* &nbsp;·&nbsp; `disabled by default`

Monitors attainment results and survey cycles for institutional QA.

> Seeded inactive — an Institution Administrator must enable this role before it can be assigned.

**5** menu sections visible · **1** with write access · **6** permission codes granted

**Dashboard** (`/`)
  Content adapts by role rather than by a permission gate: the Student role sees a read-only “My Attainment” panel in place of the usual overview. Anyone holding assessment.approve additionally sees a “documents awaiting review” card — itself just a link, not a write surface.

**Course Level Settings** (`/course-settings`)
  - Courses — **Read** — All courses / by category — a client-side filter, not permission-gated
  - Course versions — **Read** _Creating/editing a version needs outcome.create; advancing its workflow status (draft→submitted→…→published) additionally needs outcome.approve._
  - Course Outcomes — **Read** _Same split as Course versions: outcome.create to write, outcome.approve to advance status._

**Program Level Setting** (`/program-settings`)
  - PEOs — **Read** _outcome.create to write, outcome.approve to advance status._
  - Program Outcomes — **Read** _outcome.create to write, outcome.approve to advance status._
  - CO-PO Mapping — **Read**
  - PEO-PO Mapping — **Read**
  - Accreditation Framework — **Read** _Read-only for every role — the accreditation body’s own catalogue, not tenant-editable data._ — Program Outcomes (POs); Knowledge Profiles (WK); Problem Attributes (WP); Engineering Activities (EA)

**Analytics** (`/analytics`)
  - Course Attainment — **Read + Write** _Same component as Assessment → Attainment, reused here at the course level._

**About** (`/about`)
  Static, informational — the same for everyone.

---

### Accreditation Reviewer

*Scope: Assigned criteria* &nbsp;·&nbsp; `disabled by default`

Reviews submitted evidence against accreditation criteria (typically external/part-time).

> Seeded inactive — an Institution Administrator must enable this role before it can be assigned.

**4** menu sections visible · **0** with write access · **3** permission codes granted

**Dashboard** (`/`)
  Content adapts by role rather than by a permission gate: the Student role sees a read-only “My Attainment” panel in place of the usual overview. Anyone holding assessment.approve additionally sees a “documents awaiting review” card — itself just a link, not a write surface.

**Course Level Settings** (`/course-settings`)
  - Courses — **Read** — All courses / by category — a client-side filter, not permission-gated
  - Course versions — **Read** _Creating/editing a version needs outcome.create; advancing its workflow status (draft→submitted→…→published) additionally needs outcome.approve._
  - Course Outcomes — **Read** _Same split as Course versions: outcome.create to write, outcome.approve to advance status._

**Program Level Setting** (`/program-settings`)
  - PEOs — **Read** _outcome.create to write, outcome.approve to advance status._
  - Program Outcomes — **Read** _outcome.create to write, outcome.approve to advance status._
  - CO-PO Mapping — **Read**
  - PEO-PO Mapping — **Read**
  - Accreditation Framework — **Read** _Read-only for every role — the accreditation body’s own catalogue, not tenant-editable data._ — Program Outcomes (POs); Knowledge Profiles (WK); Problem Attributes (WP); Engineering Activities (EA)

**About** (`/about`)
  Static, informational — the same for everyone.

---

### External Stakeholder

*Scope: Survey only* &nbsp;·&nbsp; `disabled by default`

Employers/alumni/advisory-board members — survey participation only once that module ships; no menu access today.

> Seeded inactive — an Institution Administrator must enable this role before it can be assigned.

**2** menu sections visible · **0** with write access · **0** permission codes granted

**Dashboard** (`/`)
  Content adapts by role rather than by a permission gate: the Student role sees a read-only “My Attainment” panel in place of the usual overview. Anyone holding assessment.approve additionally sees a “documents awaiting review” card — itself just a link, not a write surface.

**About** (`/about`)
  Static, informational — the same for everyone.

---

## Separate system

### Platform Administrator

*Scope: Cross-institution* &nbsp;·&nbsp; `separate login`

A completely separate login (/platform-login), outside the tenant permission system entirely. Creates institutions and can browse/edit raw data across every institution.

| Menu section | Access | Notes |
|---|---|---|
| **Platform Dashboard** (`/platform`) | Read + Write | Lists every institution on the deployment. *Create institution* provisions a brand-new tenant schema, seeded roles/permissions/assessment types/Bloom levels, and optionally demo data. |
| **Platform Raw Data Console** (`/platform/raw-data`) | Read + Write | Cross-institution table browser/editor — not governed by the tenant permission system at all; any platform admin has full access to every institution’s tables. |

---

## Permission code reference

| Code | Unlocks |
|---|---|
| `institution.manage` | manage institution |
| `institution.view` | view institution |
| `org.manage` | manage org structure |
| `org.view` | view org structure |
| `program.manage` | manage programs |
| `program.view` | view programs |
| `program.approve` | approve program versions |
| `academic_calendar.manage` | manage calendar |
| `academic_calendar.view` | view calendar |
| `user.manage` | manage users |
| `user.view` | view users |
| `role.manage` | manage roles |
| `role.view` | view roles |
| `curriculum.view` | view curriculum |
| `outcome.create` | create/edit outcomes |
| `outcome.approve` | approve outcomes |
| `mapping.create` | edit outcome mappings |
| `section.manage` | manage sections |
| `section.view` | view sections |
| `student.manage` | manage students |
| `student.view` | view students |
| `grading.manage` | manage grading policy |
| `grading.view` | view grading policy |
| `assessment.create` | create/edit assessments |
| `assessment.approve` | approve assessments |
| `assessment.view` | view assessments |
| `marks.enter` | enter marks |
| `attainment.calculate` | trigger attainment calc |
| `attainment.approve` | approve attainment results |
| `survey.manage` | manage surveys |
| `evidence.upload` | upload evidence |
| `accreditation.manage` | manage accreditation |
| `report.generate` | generate reports |
| `audit.view` | view audit log |
| `raw_data.manage_all` | raw data — every institution |
| `raw_data.manage_institution` | raw data — own institution |
| `raw_data.manage_scoped` | raw data — own scope |
| `raw_data.propose_scoped` | raw data — propose (own scope) |
| `raw_data.approve` | approve raw-data proposals |

