# OBEvolve: OBE Management Platform for ULAB CSE

## 1. Project Context

We are building **OBEvolve**, a modern, highly configurable Outcome-Based Education (OBE) management platform.

The initial implementation is for:

* **University:** University of Liberal Arts Bangladesh (ULAB)
* **Department:** Computer Science & Engineering (CSE)
* **Program:** Undergraduate B.Sc. in Computer Science & Engineering
* **Accreditation framework:** BAETE, Bangladesh
* **Current target:** BAETE Accreditation Manual v3.0
* **Primary purpose:** Manage OBE data, curriculum alignment, CO-PO mapping, attainment analysis, evidence and Continuous Quality Improvement (CQI).

Do NOT build this as a ULAB-only hard-coded system. ULAB CSE is the first tenant/program configuration. The underlying architecture must support other departments, programs, institutions and potentially other accreditation frameworks in the future.

---

# 2. Authoritative Sources

Before implementing or seeding data, inspect and use the following sources.

### BAETE

Use the current BAETE Accreditation Manual **v3.0**, effective from 1 July 2025, as the authoritative source for the current BAETE framework.

Important BAETE components include:

* 12 Program Outcomes (PO1-PO12)
* Knowledge and Attitude Profile: WK1-WK9
* Range of Complex Engineering Problem Solving: WP1-WP7
* Range of Complex Engineering Activities: EA1-EA5
* PEO requirements
* CO-PO correlation
* Curriculum mapping
* Outcome assessment and attainment
* Continuous Quality Improvement

Do not rely on outdated BAETE versions when defining the default framework.

### ULAB CSE

Use the current ULAB CSE website for:

* Program information
* PEOs
* Current course curriculum
* Course codes
* Course titles
* Course credits
* Course categories
* Current curriculum structure

The ULAB CSE website currently publishes three PEOs and 12 POs. However, where ULAB's published PO wording conflicts with the current BAETE v3.0 PO framework, do NOT silently overwrite or merge the two. The system must clearly distinguish:

1. BAETE standard/reference POs
2. ULAB CSE program-specific POs

For the initial ULAB CSE deployment, configure the program's POs according to the current approved ULAB/BAETE alignment after verifying the source material.

---

# 3. Curriculum Reference Folder

There is also a curriculum/reference document available in the project's `ref` folder.

Inspect the reference folder and identify the authoritative ULAB CSE curriculum document.

From the curriculum document, extract only the following course-level information:

### Course

* Course Title
* Course Code
* Course Credit
* Course Objective
* Course Learning Outcomes

Store Course Learning Outcomes as **Course Outcomes (COs)**.

A course normally has **2 to 5 COs**.

* CO1
* CO2
* CO3
* CO4
* CO5

Only create the COs that actually exist for a course.

* Course Content

### IMPORTANT DATA RESTRICTION

Do NOT store other information from the curriculum document unless explicitly required by the system design.

In particular, do NOT import/store:

* PEO-PO mapping from the source document
* CO-PO mapping from the source document
* Any other mapping tables from the curriculum document
* Unnecessary document metadata
* Narrative material unrelated to the above course fields

The maps must be created and managed through OBEvolve's own configurable mapping interface.

The source document is an input/reference source, not the database schema.

---

# 4. Core OBE Data Model

Design a proper normalized relational database.

At minimum, the conceptual model should support:

### Institution

* institution_id
* name
* code
* description
* active

### Department

* department_id
* institution_id
* name
* code
* description
* active

### Program

* program_id
* department_id
* name
* degree
* program_code
* description
* version
* effective_from
* effective_to
* accreditation_framework_id
* active

The architecture must support multiple programs.

---

# 5. Accreditation Framework

Do NOT hard-code BAETE into the core application logic.

Create configurable entities such as:

### AccreditationFramework

* framework_id
* name
* version
* issuing_body
* effective_date
* expiry_date
* description
* active

Example:

BAETE / Accreditation Manual / v3.0

The framework should be selectable for a program.

This allows future support for:

* another BAETE version
* another accreditation body
* institutional OBE frameworks
* other engineering accreditation systems

---

# 6. Program Educational Objectives

Create configurable PEO entities.

### PEO

* peo_id
* program_id
* code
* title
* statement
* description
* sequence
* active
* effective_from
* effective_to

Seed the ULAB CSE program with the currently published PEOs after verification.

The system must NOT hard-code three PEOs. A program may have any number of PEOs.

---

# 7. Program Outcomes

Create configurable PO entities.

### PO

* po_id
* program_id
* framework_id
* code
* title
* statement
* description
* sequence
* active
* effective_from
* effective_to

The UI must allow administrators to:

* Add PO
* Edit PO
* Delete/deactivate PO
* Reorder POs
* Change PO labels
* Change PO statements
* Add additional program-specific outcomes
* Associate outcomes with an accreditation framework
* Version outcomes

Do not assume PO1-PO12 are permanently fixed in application logic.

---

# 8. BAETE v3.0 Default PO Data

Seed the BAETE v3.0 framework with the official 12 POs.

Use the official BAETE wording rather than abbreviating the statements.

The current BAETE v3.0 POs are:

PO1:
Apply knowledge of mathematics, natural science, computing, engineering fundamentals and an engineering specialization as specified in WK1 to WK4 respectively to develop solutions of complex engineering problems.

PO2:
Identify, formulate, research literature and analyze complex engineering problems reaching substantiated conclusions using first principles of mathematics, natural sciences and engineering sciences with holistic considerations for sustainable development (WK1 to WK4).

PO3:
Design creative solutions for complex engineering problems and design systems, components or processes to meet identified needs with appropriate consideration for public health and safety, whole-life cost, net zero carbon as well as resource, cultural, societal, and environmental considerations as required (WK5).

PO4:
Conduct investigations of complex engineering problems using research methods including research-based knowledge, design of experiments, analysis and interpretation of data, and synthesis of information to provide valid conclusions (WK8).

PO5:
Create, select and apply and recognize limitations of appropriate techniques, resources, and modern engineering and IT tools, including prediction and modeling, to complex engineering problems (WK2, WK6).

PO6:
When solving complex engineering problems, analyze and evaluate sustainable development impacts to: society, the economy, sustainability, health and safety, legal frameworks, and the environment (WK1, WK5, and WK7).

PO7:
Apply ethical principles and commit to professional ethics and norms of engineering practice and adhere to relevant national and international laws. Demonstrate an understanding of the need for diversity and inclusion (WK9).

PO8:
Function effectively as an individual, and as a member or leader in diverse and inclusive teams and in multi-disciplinary, face-to-face, remote and distributed settings (WK9).

PO9:
Communicate effectively and inclusively on complex engineering activities with the engineering community and with society at large, such as being able to comprehend and write effective reports and design documentation, make effective presentations, taking into account cultural, language, and learning differences.

PO10:
Apply knowledge and understanding of engineering management principles and economic decision-making and apply these to one’s own work, as a member and leader in a team and to manage projects and in multidisciplinary environments.

PO11:
Recognize the need for, and have the preparation and ability for i) independent and life-long learning ii) adaptability to new and emerging technologies and iii) critical thinking in the broadest context of technological change (WK8).

PO12:
Demonstrate knowledge and understanding of the competences necessary to transform opportunities and ideas into a new business.

These must be stored as database records, NOT embedded in application code.

---

# 9. Knowledge and Attitude Profile

Create a configurable table/entity for the BAETE Knowledge and Attitude Profile.

### KnowledgeProfile

* knowledge_profile_id
* framework_id
* code
* title
* description
* sequence
* active

Seed:

* WK1
* WK2
* WK3
* WK4
* WK5
* WK6
* WK7
* WK8
* WK9

Use the official BAETE v3.0 descriptions.

The UI must allow administrators to modify, add, deactivate and reorder these attributes.

---

# 10. Complex Engineering Problem Solving

Create configurable entities for:

### ProblemAttribute

* problem_attribute_id
* framework_id
* code
* title
* description
* sequence
* active

Seed:

* WP1
* WP2
* WP3
* WP4
* WP5
* WP6
* WP7

Use the official BAETE v3.0 definitions.

---

# 11. Complex Engineering Activities

Create configurable entities for:

### EngineeringActivity

* engineering_activity_id
* framework_id
* code
* title
* description
* sequence
* active

Seed:

* EA1
* EA2
* EA3
* EA4
* EA5

Use the official BAETE v3.0 definitions.

---

# 12. Courses

Create a normalized Course entity.

### Course

* course_id
* program_id
* course_code
* course_title
* credit
* course_objective
* course_content
* active
* version
* effective_from
* effective_to

Support multiple curriculum versions.

A course code may remain the same while its title, credits, objective, content or COs change in a later curriculum version.

Therefore, consider a separate:

### CourseVersion

where appropriate.

Do not unnecessarily duplicate courses merely because they belong to different curriculum versions.

---

# 13. Course Outcomes

Create:

### CourseOutcome

* co_id
* course_id / course_version_id
* code
* statement
* sequence
* active

Examples:

CO1
CO2
CO3
CO4

Do NOT assume every course has exactly four COs.

Allow 2-5 COs by default, while keeping the database flexible enough to support configuration.

The UI should make CO management extremely easy.

---

# 14. CO-PO Mapping

Create a dedicated mapping table.

### CourseOutcomePOMap

* map_id
* course_outcome_id
* po_id
* correlation_level
* weight
* remarks
* created_at
* updated_at

Do NOT hard-code mapping values.

The mapping must be completely configurable from the UI.

Support common correlation schemes such as:

* None
* Low
* Medium
* High

But make the correlation scale itself configurable.

For example, an administrator should be able to configure:

Binary:

* Yes / No

or:

Ternary:

* None / Low / High

or:

Four-level:

* None / Low / Medium / High

Do not bake any one scale into the business logic.

---

# 15. PEO-PO Mapping

Create:

### ProgramOutcomePEOMap

* map_id
* po_id
* peo_id
* correlation_level
* weight
* remarks
* created_at
* updated_at

Again, this mapping must be managed by the application.

Do not import an existing PEO-PO map from the curriculum document.

The initial system should provide an empty/configurable mapping workspace so that authorized users can create the approved mapping.

---

# 16. Future CO Indicators

Do NOT implement PO indicators yet.

However, design the schema so that indicators can be introduced later without restructuring the database.

Future conceptual structure:

PO
→ PO Indicator
→ Assessment Evidence
→ CO
→ Assessment Tool
→ Attainment

For now:

PO is the terminal program-level outcome.

Do NOT create artificial indicators merely to satisfy future requirements.

---

# 17. Assessment Architecture

Even if full assessment functionality is implemented later, the database architecture should be prepared for it.

The future system must be able to support:

* Assessment
* Assessment component
* Assessment tool
* Rubric
* Question
* Question-to-CO mapping
* Assessment-to-CO mapping
* Student performance
* CO attainment
* PO attainment
* Direct assessment
* Indirect assessment
* Target attainment
* Actual attainment
* Course-level attainment
* Program-level attainment

Do not overbuild these features in the first implementation unless necessary.

But avoid a database structure that makes these impossible later.

---

# 18. Fully Customizable UI

This is one of the MOST IMPORTANT requirements.

OBEvolve must be **100% configurable** from the UI.

Do not create screens where BAETE/ULAB values are hard-coded into frontend components.

Administrators should be able to configure:

### Program

* Program name
* Degree
* Program code
* Department
* Curriculum version
* Effective dates

### PEO

* Add/edit/remove/reorder PEOs

### PO

* Add/edit/remove/reorder POs
* Change labels
* Change descriptions
* Activate/deactivate

### CO

* Add/edit/delete/reorder COs
* Configure number of COs

### Mapping

* Configure PEO-PO mappings
* Configure CO-PO mappings
* Configure correlation scale
* Configure mapping terminology

### Framework

* Add accreditation frameworks
* Add framework versions
* Configure PO structures
* Configure knowledge profiles
* Configure problem attributes
* Configure engineering activities

---

# 19. Mapping UI

The mapping interface should be one of the strongest parts of the application.

Provide matrix-based mapping screens.

## CO-PO Matrix

Rows:

CO1
CO2
CO3
...

Columns:

PO1
PO2
...
PO12

Each cell should be editable.

Example:

| CO / PO | PO1 | PO2 | PO3 | PO4 |
| ------- | --- | --- | --- | --- |
| CO1     | H   | M   |     |     |
| CO2     |     | H   | M   |     |
| CO3     |     |     | H   | M   |

Use visual indicators for correlation levels.

Provide:

* Bulk edit
* Clear row
* Clear column
* Copy mapping
* Save
* Reset
* Validation
* Export

Do NOT use hard-coded PO columns.

Generate them dynamically from database records.

---

# 20. PEO-PO Matrix

Similarly provide:

PEO rows × PO columns

Dynamic columns and rows.

Allow configurable correlation levels.

---

# 21. Curriculum Mapping

Prepare the UI architecture for future mapping of:

* Courses → POs
* Courses → PEOs
* Courses → WK
* Courses → WP
* Courses → EA
* Courses → SDGs

These should be independent mapping structures.

Do not collapse all mappings into a single generic table unless the design genuinely supports different mapping semantics cleanly.

---

# 22. Curriculum Dashboard

Create a dashboard showing:

* Total courses
* Total credits
* Total COs
* Number of POs
* Number of PEOs
* CO-PO mapping coverage
* PEO-PO mapping coverage
* WK coverage
* WP coverage
* EA coverage
* Unmapped COs
* Unmapped POs
* Courses without COs
* Courses with incomplete mappings

The dashboard should calculate these dynamically.

---

# 23. Data Validation

Implement OBE-specific validation.

Examples:

* Every active course should have COs.
* Every CO should have a meaningful statement.
* Every active CO should have an optional/configurable PO mapping.
* Every PO should contribute to at least one PEO, subject to configuration.
* Detect POs with no CO coverage.
* Detect COs with no PO mapping.
* Detect PEOs with no PO contribution.
* Detect mapping inconsistencies.
* Detect duplicate course codes within the same curriculum version.
* Detect missing course credits.
* Detect invalid CO numbering.

Do not prevent legitimate intermediate editing states unless necessary. Provide warnings/errors appropriately.

---

# 24. Versioning

OBE data changes over time.

Support versioning for:

* Programs
* Curriculum
* Courses
* COs
* PEOs
* POs
* Accreditation frameworks
* Mappings

Historical data must not be destroyed when a new curriculum or framework becomes effective.

A user should be able to select:

**Curriculum 2026**
**Curriculum 2027**

and see the corresponding courses, COs and mappings.

---

# 25. Source Traceability

For imported/seeding data, maintain source metadata where useful:

* source_name
* source_url
* source_document
* imported_at
* imported_by

However, do NOT store the entire source documents in the OBE database merely because they were used for extraction.

The database should contain the structured data required by OBEvolve.

---

# 26. ULAB CSE Initial Data Population

Populate the initial system with verified ULAB CSE data.

Use:

1. Current ULAB CSE website
2. Curriculum/reference document in the project `ref` folder
3. Current BAETE v3.0 documentation

For courses, extract only:

* Course Title
* Course Code
* Course Credit
* Course Objective
* Course Learning Outcomes → CO
* Course Content

Do not populate mappings from the curriculum source.

Mappings should be configured separately through OBEvolve.

Where two sources disagree:

1. Identify the discrepancy.
2. Do not silently choose one.
3. Prefer the currently approved/current curriculum source for course data.
4. Prefer BAETE v3.0 for the accreditation framework.
5. Flag the discrepancy for administrator review.

---

# 27. Important ULAB PO Consideration

The current ULAB CSE website lists POs that appear to use an older BAETE formulation.

The application must therefore support both:

### Accreditation Framework PO

The official BAETE v3.0 PO definition.

and

### Program PO

The PO actually adopted by ULAB CSE for the selected curriculum/version.

Do not overwrite one with the other.

The data model should allow a program PO to reference its framework PO where appropriate.

This distinction is important for accreditation traceability.

---

# 28. Security and Roles

Implement role-based access control.

At minimum:

### Super Admin

Full configuration.

### Program Admin / OBE Coordinator

Manage program, curriculum, PEO, PO, CO and mappings.

### Faculty

View assigned courses and manage course-level OBE information according to permissions.

### Reviewer

Read-only access to OBE data, mappings and reports.

### Viewer

Dashboard/read-only access.

Do not allow ordinary users to modify accreditation framework definitions unless explicitly authorized.

---

# 29. Audit Trail

OBE data is accreditation evidence.

Track:

* Who created a record
* Who changed it
* What changed
* Previous value
* New value
* Timestamp
* Mapping changes
* Framework changes
* Curriculum changes

Mapping changes are particularly important.

---

# 30. Reporting

Design the application so reports can eventually be generated for:

* PEO list
* PO list
* CO list by course
* CO-PO matrix
* PEO-PO matrix
* Curriculum structure
* Course profile
* Knowledge Profile coverage
* Complex Problem coverage
* Complex Engineering Activity coverage
* CO attainment
* PO attainment
* PEO attainment
* CQI
* Accreditation evidence

Reports should be dynamically generated from database data, not hard-coded templates containing ULAB-specific values.

---

# 31. UX Requirements

The interface should feel like a modern academic quality-management platform.

Prioritize:

* Clean dashboard
* Responsive design
* Clear navigation
* Matrix-based mapping
* Inline editing where appropriate
* Search/filter
* Bulk operations
* Import/export
* Validation indicators
* Version selectors
* Accreditation status indicators
* Audit history

Avoid making it look like an old administrative ERP.

The core workflow should be intuitive:

**Program → PEO → PO → Curriculum → Course → CO → Mapping → Assessment → Attainment → CQI**

---

# 32. Do Not Hard-Code

Absolutely do NOT hard-code:

* ULAB
* CSE
* B.Sc.
* BAETE
* PO1-PO12
* PEO1-PEO3
* CO1-CO5
* WK1-WK9
* WP1-WP7
* EA1-EA5
* Mapping scales
* Course categories
* Curriculum versions

These should be database-driven configuration.

The initial seed data may contain these values, but the application logic must not depend on their existence or exact numbering.

---

# 33. Database Design Requirement

Before coding UI features, design and document the normalized database schema.

Show:

1. Entity list
2. Attributes
3. Primary keys
4. Foreign keys
5. Relationships
6. Cardinalities
7. Constraints
8. Versioning strategy
9. Mapping strategy
10. Audit strategy

Pay particular attention to avoiding duplicated PO/PEO/CO data.

Mappings must be represented through proper associative tables.

---

# 34. Seed Data Strategy

Create seed scripts/migrations for:

### Accreditation

* BAETE v3.0
* PO1-PO12
* WK1-WK9
* WP1-WP7
* EA1-EA5

### ULAB CSE

* Institution
* Department
* Program
* PEO1-PEO3
* Current curriculum
* Courses
* Course objectives
* Course contents
* COs

Do NOT seed PEO-PO or CO-PO mappings unless the approved mapping is independently verified and explicitly provided as an authoritative source.

---

# 35. Data Integrity Principle

OBEvolve is not simply a CRUD application.

Treat OBE data as **accreditation-critical academic data**.

Never silently:

* overwrite source data
* delete historical mappings
* change PO definitions
* change CO statements
* change curriculum versions
* modify attainment calculations

without appropriate versioning/audit handling.

---

# 36. Development Approach

Before implementation:

### Phase 1

Inspect the existing repository and architecture.

### Phase 2

Inspect the `ref` folder and identify the authoritative ULAB CSE curriculum source.

### Phase 3

Verify current BAETE v3.0 requirements.

### Phase 4

Design the normalized database.

### Phase 5

Create migrations and seed data.

### Phase 6

Build the configuration/admin layer.

### Phase 7

Build curriculum/course/CO management.

### Phase 8

Build PEO/PO management.

### Phase 9

Build dynamic PEO-PO and CO-PO mapping matrices.

### Phase 10

Build dashboards and validation.

### Phase 11

Prepare assessment/attainment architecture.

### Phase 12

Test with the complete ULAB CSE dataset.

---

# 37. Critical Instruction

Do not rush into frontend implementation.

First understand:

* the existing codebase
* current database
* framework
* project structure
* authentication
* API architecture
* existing UI patterns
* reference files
* ULAB curriculum
* BAETE v3.0

Then produce a concise implementation plan and database ERD/schema before making major changes.

If the repository already contains an OBE/academic data model, carefully evaluate whether it should be extended or refactored rather than creating duplicate structures.

The final result should be a **generic, configurable OBE platform seeded for ULAB CSE**, not a one-off CSE database application.

## Primary architectural principle

**Configure the framework. Do not hard-code the framework.**

OBEvolve should be capable of evolving from:

**ULAB CSE → other ULAB programs → other universities → other accreditation frameworks**

without requiring a fundamental rewrite of the application.
