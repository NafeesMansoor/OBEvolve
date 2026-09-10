# Program, Curriculum & Trimester-Level Management

## 1. Architectural Principle

The system should distinguish clearly between two levels of academic configuration:

### A. Program & Curriculum Level

This is the **strategic and relatively stable academic framework** of the program.

It defines:

* Institutional mission and vision
* Program mission and vision
* Mission/vision mappings
* PEOs
* POs
* Knowledge Profiles
* Complex Engineering Problems
* Complex Engineering Activities
* Performance Indicators, where applicable
* Curriculum structure
* PO/PEO/CO/PI mappings
* Curriculum versions and effective periods

Only the **Program Administrator / Institution Administrator** has edit rights at this level.

Other users may have view access according to their permissions.

### B. Trimester / Academic Term Level

This is the **operational configuration for a particular trimester**.

It defines:

* Academic trimester and year
* Academic calendar dates
* Effective curriculum(s)
* Student cohort(s)
* Courses offered
* Number of sections
* Faculty
* Course-section assignments
* Course coordinators
* Students

The **Program Coordinator** manages this level after the Program Administrator has completed and published the required program/curriculum setup.

---

# 2. Recommended Main Navigation

The system should preferably use the following hierarchy:

```text
Program & Curriculum
│
├── Academic Framework
│   ├── Institutional Mission & Vision
│   ├── Program Mission & Vision
│   ├── Mission/Vision Mapping
│   ├── PEOs
│   ├── Program Outcomes (POs)
│   └── Outcome Framework
│
├── Curriculum Management
│   ├── Curricula
│   ├── Curriculum Versions
│   ├── Curriculum Structure
│   └── Curriculum-Cohort Assignment
│
├── Outcome Mapping
│   ├── PEO ↔ Program Vision
│   ├── PO ↔ PEO
│   ├── PO ↔ Knowledge Profiles
│   ├── PO ↔ Complex Engineering Problems
│   ├── PO ↔ Complex Engineering Activities
│   └── PO/PI ↔ CO
│
└── Publication & Versions
    ├── Published Versions
    ├── Draft Versions
    └── Change History
```

The operational area should be:

```text
Trimester Management
│
├── Trimester Settings
├── Effective Curriculum
├── Course Offering
├── Faculty Management
├── Course & Section Assignment
├── Student Cohorts
└── Students
```

---

# 3. Academic Trimester Definition

The **Program Administrator or Institution Administrator** must first define an academic trimester.

A trimester consists of:

* Trimester: Spring / Summer / Fall
* Year
* Class Start Date
* Add/Drop Last Date
* Midterm Start Date
* Midterm End Date
* Final Examination Start Date
* Final Examination End Date
* Result Submission/Due Date
* Result Publication Date
* Trimester/Semester End Date

The system must validate that dates are logically consistent.

For example:

```text
Class Start
    ↓
Add/Drop Deadline
    ↓
Midterm Start
    ↓
Midterm End
    ↓
Final Exam Start
    ↓
Final Exam End
    ↓
Result Due Date
    ↓
Result Publication
    ↓
Trimester End
```

The system should not hard-code these dates.

They are part of the academic calendar configuration.

---

# 4. Curriculum Effective for a Trimester

For every trimester, the administrator must define which **curriculum or curricula are effective**.

A trimester may have:

* One effective curriculum, or
* Multiple effective curricula.

This is necessary because different student cohorts may follow different curriculum versions during the same trimester.

For example:

```text
Fall 2026
│
├── Curriculum 2022 → Cohort 2022
├── Curriculum 2024 → Cohort 2024
└── Curriculum 2026 → Cohort 2026
```

The system must therefore treat:

**Curriculum → Cohort → Trimester**

as related but distinct concepts.

---

# 5. Student Cohort

Every new intake/batch of students should be represented as a **Cohort**.

A cohort should have, at minimum:

* Cohort identifier
* Intake trimester
* Intake year
* Assigned curriculum
* Status

Once a cohort has been assigned a curriculum, that curriculum should normally remain associated with that cohort throughout the students' academic lifecycle.

### Important Rule

Changing the curriculum assigned to an existing cohort should **not be a routine operation**.

If such a change is required, it should require explicit administrative action and should be fully recorded in the audit/history system.

---

# 6. Curriculum Lifecycle

Curricula should be treated as versioned academic artifacts.

A curriculum normally remains effective for several years, typically around four years, but the system **must not hard-code a four-year validity period**.

A curriculum may remain effective:

* Less than four years
* Approximately four years
* More than four years

depending on academic requirements.

Each curriculum should therefore have:

* Curriculum Name/Code
* Version
* Description
* Effective From
* Effective To, if applicable
* Status
* Publication Status
* Revision History

Possible statuses:

```text
Draft
Published
Unpublished
Superseded
Archived
```

---

# 7. Institutional Mission and Vision

As part of defining a curriculum/program framework, the administrator must define the institution's academic identity.

## Institutional Mission

The administrator should be able to enter the institution/university mission.

## Institutional Vision

The administrator should be able to define multiple numbered institutional visions.

Example:

```text
V1
V2
V3
V4
```

The numbering format should be configurable rather than hard-coded.

---

# 8. Program Mission and Vision

The administrator must define:

### Program Mission

A textual statement describing the mission of the program.

### Program Visions

Multiple numbered program visions.

Example:

```text
PV1
PV2
PV3
PV4
```

The system should allow the administrator to add, edit, remove, reorder, and renumber these items as appropriate.

---

# 9. Institutional Vision ↔ Program Vision Mapping

The administrator must define the relationship between:

**Institutional Vision → Program Vision**

The mapping interface should allow the administrator to identify which institutional visions are supported by each program vision.

Example:

| Program Vision | Institutional Vision |
| -------------- | -------------------- |
| PV1            | V1, V3               |
| PV2            | V2                   |
| PV3            | V1, V4               |

The mapping must be stored as structured data, not simply as text.

---

# 10. Program Educational Objectives (PEOs)

The administrator defines the Program Educational Objectives.

Each PEO should have:

* PEO Number
* PEO Statement
* Description, if required
* Status

Example:

```text
PEO1
PEO2
PEO3
```

The numbering convention should be configurable.

---

# 11. PEO ↔ Program Vision Mapping

Each PEO must be mapped to one or more Program Visions.

Example:

| PEO  | Program Vision |
| ---- | -------------- |
| PEO1 | PV1, PV2       |
| PEO2 | PV2, PV3       |
| PEO3 | PV1, PV4       |

---

# 12. Program Outcomes (POs)

The administrator must define the Program Outcomes.

Before defining the POs, the administrator must select the **PO Definition Method**.

The system should support two methods:

```text
1. Direct Method
2. Indicator-Based Method
```

This choice is an important curriculum-level configuration.

---

# 13. PO Numbering

PO numbering must be configurable.

The administrator should be able to choose a numbering convention such as:

```text
PO1, PO2, PO3...
```

or:

```text
PO(a), PO(b), PO(c)...
```

The system must not assume that POs are always numbered numerically.

The selected numbering scheme should be used consistently throughout the curriculum.

---

# 14. Knowledge Profiles

The administrator must define the Knowledge Profiles used by the curriculum.

The system should support the current engineering-accreditation-oriented structure, for example:

```text
K1–K8
```

or an alternative convention such as:

```text
WK1–WK8
```

The system should allow the administrator to define:

* Profile Code
* Profile Name
* Description
* Definition
* Status

The system should not permanently hard-code K1-K8.

The administrator should be able to modify the framework if the applicable accreditation framework changes.

Conceptually, the profiles represent progression from foundational mathematics/natural sciences through specialist engineering, research, and advanced knowledge.

---

# 15. Complex Engineering Problems

The administrator must define the **Complex Engineering Problem (CEP)** criteria.

The system should support the current structure:

```text
P1–P7
```

Each CEP should contain:

* Code
* Name/Title
* Definition
* Description
* Status

Again, the system should allow the framework to be updated rather than permanently hard-coding P1-P7.

---

# 16. Complex Engineering Activities

The administrator must define the **Complex Engineering Activity (CEA)** framework.

The current structure may contain:

```text
A1–A5
```

Each activity should contain:

* Code
* Name/Title
* Definition
* Description
* Status

The system should allow these definitions to evolve when accreditation requirements change.

---

# 17. Direct PO Definition Method

When the administrator selects:

**PO Definition Method = Direct**

the administrator defines the POs directly.

Example:

```text
PO1
PO2
PO3
...
```

Each PO has a statement/definition.

The administrator then configures the following mappings:

### PO ↔ Knowledge Profiles

Example:

```text
PO1 → K1, K2, K4
PO2 → K3, K5
```

### PO ↔ Complex Engineering Problems

Example:

```text
PO1 → P1, P3
PO2 → P2, P5
```

### PO ↔ Complex Engineering Activities

Example:

```text
PO1 → A1, A2
PO2 → A3, A5
```

### PO ↔ PEO

Each PO must also be mapped to one or more PEOs.

---

# 18. Indicator-Based PO Definition Method

When the administrator selects:

**PO Definition Method = Indicator-Based**

the administrator still defines:

* POs
* Knowledge Profiles
* CEPs
* CEAs

However, each PO must additionally contain **Performance Indicators (PIs)**.

For example:

```text
PO(a)
    ├── PI(a1)
    ├── PI(a2)

PO(b)
    ├── PI(b1)
    ├── PI(b2)
    └── PI(b3)
```

The PI numbering must automatically inherit the PO identifier.

Therefore:

```text
PO(a) → PI(a1), PI(a2), PI(a3)
PO(b) → PI(b1), PI(b2)
```

The system should generate the appropriate PI identifier based on the selected PO numbering convention.

---

# 19. Indicator-Based Mapping

Under the indicator-based method, the administrator must be able to map:

**POs and/or PIs → Knowledge Profiles**

**POs and/or PIs → Complex Engineering Problems**

**POs and/or PIs → Complex Engineering Activities**

The mapping interface must clearly distinguish whether a mapping belongs to:

* PO
* PI

The system must prevent ambiguous mapping records.

---

# 20. PO ↔ PEO Mapping

Regardless of whether the Direct or Indicator-Based method is selected:

**PO → PEO**

mapping must be available.

The system should maintain this mapping independently from the PO definition method.

---

# 21. Course-Level Outcome Mapping

The curriculum framework must eventually connect to the course level.

### Direct Method

```text
PO → CO
```

### Indicator-Based Method

```text
PI → CO
```

Therefore, the course configuration interface must dynamically adapt according to the curriculum's PO definition method.

If the curriculum uses Direct Method, course instructors map:

**CO → PO**

If the curriculum uses Indicator-Based Method, course instructors map:

**CO → PI**

The system must not display the wrong mapping type.

---

# 22. Curriculum Settings Inheritance

When a curriculum is selected as effective for a new trimester, the system should automatically load the **latest published configuration of that curriculum**.

This should include, as applicable:

* Mission
* Vision
* PEOs
* POs
* PIs
* Knowledge Profiles
* CEPs
* CEAs
* All applicable mappings
* Curriculum structure
* Course-level outcome framework

The new trimester should therefore begin with a stable snapshot of the last published curriculum configuration.

---

# 23. Curriculum Revision and Publishing

The administrator should be able to:

* Create a draft
* Edit existing curriculum settings
* Add items
* Remove items
* Modify definitions
* Modify mappings
* Review changes
* Publish the revised configuration

### Published Configuration

Once published, the configuration becomes the official version used by subsequent academic operations.

### Unpublish

The administrator should also have an explicit **Unpublish** operation.

When a curriculum is unpublished:

1. The system must clearly indicate that it is no longer in a published/editable-final state.
2. The administrator can modify the configuration.
3. Changes remain in draft/unpublished state.
4. The revised configuration does not become effective until it is published again.

Do not silently alter a published curriculum.

---

# 24. Versioning and Audit Trail

Every published curriculum configuration should be versioned.

For example:

```text
CSE Curriculum
├── Version 1.0
├── Version 1.1
├── Version 2.0
└── Version 2.1
```

The system should record:

* Version number
* Created by
* Created date
* Published by
* Published date
* Changes made
* Previous version
* Current status

Historical academic records must continue referencing the appropriate curriculum/version under which they were generated.

---

# 25. Program Coordinator Permissions

The Program Coordinator should have **view access** to Program & Curriculum Level settings.

The Program Coordinator must **not directly edit** these settings.

However, every relevant curriculum/program setting should provide a **Feedback** option.

Example:

```text
PEO1
────────────────────────
[View] [Provide Feedback]
```

The same mechanism should be available for:

* Mission
* Vision
* PEOs
* POs
* PIs
* Knowledge Profiles
* CEPs
* CEAs
* Mappings
* Curriculum structure
* Other relevant program-level settings

---

# 26. Program Coordinator Feedback Workflow

When the Program Coordinator submits feedback:

```text
Program Coordinator
        ↓
Feedback submitted
        ↓
Program Administrator notified
        ↓
Administrator reviews feedback
        ↓
┌───────────────┬───────────────┐
│ Accept/Act    │ Ignore        │
│ on feedback   │ feedback      │
└───────────────┴───────────────┘
```

The administrator may:

* Review the feedback
* Accept the recommendation
* Modify the relevant setting
* Ignore the feedback
* Mark the feedback as resolved

The feedback itself should remain in the audit/history system.

---

# 27. Trimester-Level Workflow for Program Coordinator

Once the administrator completes the initial Program & Curriculum setup and publishes the required configuration, the Program Coordinator's operational interface becomes enabled.

The Program Coordinator manages each trimester independently.

The workflow should be:

```text
Select Trimester
      ↓
Select Effective Curriculum(s)
      ↓
Offer Courses
      ↓
Define Number of Sections
      ↓
Manage Faculty
      ↓
Assign Faculty to Courses/Sections
      ↓
Select Course Coordinators
      ↓
Manage Student Cohorts
      ↓
Manage Students
```

---

# 28. Course Offering

The Program Coordinator selects courses from the effective curriculum(s) that will be offered during the selected trimester.

For every offered course, the coordinator should define:

* Course
* Number of Sections
* Offering status

Only courses belonging to the effective curriculum(s) should normally be available for selection.

---

# 29. Import Previous Trimester Course Offerings

The coordinator should have an **Import from Previous Trimester** option.

Example:

```text
+ Add Course
+ Import Previous Trimester
```

The import interface should allow the coordinator to select a previous trimester.

The system then displays the previous offering configuration.

The coordinator can review and confirm the import.

Imported data should be treated as a new trimester configuration, not as a modification of the previous trimester.

---

# 30. Faculty Management

The Program Coordinator can create and manage the faculty list for a trimester.

The faculty list should support:

### Add Individually

Fields:

* Name
* Designation
* Contract Type

  * Full Time
  * Part Time
* Email Address
* Password
* Active/Inactive

The faculty email address should serve as the login identifier.

### Initial Password

When a faculty account is created, the system may generate/set a default password.

The faculty member must be required to change the password after initial authentication.

### Google Authentication

Faculty members should also be able to authenticate using their Google account, subject to the system's authentication configuration.

The system must ensure that the Google account is correctly associated with the faculty's registered email.

---

# 31. Faculty Active/Inactive Status

Faculty accounts must contain an:

**Active / Inactive**

toggle.

If a faculty member is:

```text
Inactive
```

they must not be able to access the system.

The system should enforce this at the authentication/backend level, not merely hide the account in the UI.

Inactive faculty should also not be selectable for new course/section assignments.

Existing historical assignments should remain intact.

---

# 32. Import Faculty from Previous Trimester

The coordinator should be able to import the faculty list from a previous trimester.

Example:

```text
Faculty Management
    ├── Add Faculty
    ├── Import from Previous Trimester
    └── Manage Faculty
```

After importing, the coordinator can:

* Add faculty
* Remove faculty from the current trimester
* Modify faculty information
* Change active/inactive status

Importing faculty must not alter the faculty records of the previous trimester.

---

# 33. Course and Section Assignment

The Program Coordinator assigns faculty to:

**Course → Section**

Example:

```text
CSE101
├── Section 1 → Faculty A
├── Section 2 → Faculty B
└── Section 3 → Faculty C
```

The coordinator must also identify the **Course Coordinator** for the course.

A course may have multiple sections but should have a clearly defined course-level coordinator according to the program's rules.

---

# 34. Import Faculty Assignments from Previous Trimester

The coordinator should be able to import course/section assignments from a previous trimester.

The system must intelligently match current offerings against previous offerings.

### Example

Previous trimester:

```text
CSE101
└── Section 1 → Faculty A
```

Current trimester:

```text
CSE101
├── Section 1
└── Section 2
```

If Faculty A is currently active:

```text
CSE101
├── Section 1 → Faculty A
└── Section 2 → Unassigned
```

The system should preserve the historical section assignment pattern where possible.

### Matching Rules

When importing:

1. Match the course.
2. Match the section number where available.
3. Verify that the previously assigned faculty member currently exists and is active.
4. Assign the faculty member if eligible.
5. Leave the assignment unassigned if the faculty is inactive/unavailable.
6. Never assign an inactive faculty member automatically.
7. Allow the Program Coordinator to modify all imported assignments before finalizing.

---

# 35. Student Cohort Management

The Program Coordinator manages students at the cohort level.

For a new intake, the coordinator can create a new cohort.

Alternatively, the coordinator can load an existing cohort from a previous trimester.

Example:

```text
Fall 2026
├── New Cohort 2026
├── Cohort 2025
└── Cohort 2024
```

The purpose is to allow students from continuing cohorts to remain part of the current academic operation without manually recreating their records.

---

# 36. Import Existing Cohort

The coordinator should have:

**Load Existing Cohort**

The coordinator selects a previously populated cohort.

The system imports the student list into the current trimester context.

The original cohort/student data must remain unchanged.

---

# 37. Student Management

The Program Coordinator should be able to:

* Add students
* Edit students
* Remove students where permitted
* Import students/cohorts
* Change applicable student attributes
* Activate/deactivate student status

Student fields should include:

* Student Name
* Student ID
* Email Address
* Default Password
* Phone
* Cohort
* Enrolled Curriculum
* Active/Inactive Status

The system should automatically create/set the initial password according to the institution's authentication policy.

Students should be required to change the default password after initial login.

---

# 38. Student Status During Cohort Import

When an existing cohort is loaded into a new trimester:

**The student's current status must be preserved.**

For example:

Previous trimester:

```text
Student A → Active
Student B → Inactive
Student C → Active
```

After loading the cohort:

```text
Student A → Active
Student B → Inactive
Student C → Active
```

The system must not automatically reactivate inactive students.

---

# 39. Student-Curriculum Relationship

Every student must have an associated curriculum through their cohort/enrollment.

The system should therefore be able to determine:

```text
Student
   ↓
Cohort
   ↓
Curriculum
   ↓
Curriculum Version
```

This relationship is important for determining:

* Which courses are applicable
* Which POs/PIs apply
* Which CO mappings are valid
* Which curriculum framework governs the student's academic record

---

# 40. Current Trimester as Default Context

Throughout the application, the default academic context should always be the **current trimester**.

Current-trimester courses should be shown by default in:

* Dropdowns
* Course tables
* Course assignment screens
* Course configuration
* Faculty assignment
* Student/course interfaces
* Reports
* Other operational screens

Previous-trimester data should not clutter current operational interfaces.

A separate mechanism such as:

**Previous Trimesters**

should be provided for historical access.

---

# 41. Historical Data Principle

Previous trimester data is historical and must be treated as immutable academic history unless an explicitly authorized administrative correction mechanism exists.

Importing previous data must create a new current-trimester configuration.

It must never modify:

* Previous course offerings
* Previous faculty assignments
* Previous student records
* Previous curriculum versions
* Previous academic results

---

# 42. Dynamic UI Based on Curriculum Method

The UI must dynamically respond to the curriculum's selected PO definition method.

### Direct Method

Show:

```text
PO
Knowledge Profiles
CEP
CEA
PO ↔ PEO
CO ↔ PO
```

### Indicator-Based Method

Show:

```text
PO
PI
Knowledge Profiles
CEP
CEA
PO/PI ↔ Knowledge Profiles
PO/PI ↔ CEP
PO/PI ↔ CEA
PO ↔ PEO
CO ↔ PI
```

The application must not present unnecessary fields or mapping options.

---

# 43. Permission Model

The permission architecture should be role-based.

At this stage, the following roles need to be considered:

| Function                     | Institution Admin | Program Admin | Program Coordinator |
| ---------------------------- | ----------------: | ------------: | ------------------: |
| Academic Calendar            |              Edit |          Edit |                View |
| Institutional Mission/Vision |              Edit |    Edit/View* |                View |
| Program Mission/Vision       |              Edit |          Edit |     View + Feedback |
| PEO                          |              Edit |          Edit |     View + Feedback |
| PO/PI                        |              Edit |          Edit |     View + Feedback |
| K/CEP/CEA                    |              Edit |          Edit |     View + Feedback |
| Curriculum                   |              Edit |          Edit |     View + Feedback |
| Curriculum Mapping           |              Edit |          Edit |     View + Feedback |
| Curriculum Publish           |              Edit |          Edit |                View |
| Course Offering              |              View |          View |                Edit |
| Faculty Management           |              View |          View |                Edit |
| Course Assignment            |              View |          View |                Edit |
| Student Cohort               |              View |          View |                Edit |
| Student Management           |              View |          View |                Edit |

`*` Final permissions should be configurable according to the institution's organizational model.

---

# 44. Auditability

All important academic configuration changes must be auditable.

At minimum, record:

* User
* Role
* Action
* Entity
* Previous value
* New value
* Timestamp
* Academic trimester
* Curriculum/version
* Approval/publication status where applicable

This is particularly important for accreditation and academic quality assurance.

---

# 45. Design Principle: Configuration Over Hard-Coding

Do not hard-code academic/accreditation structures wherever avoidable.

The following should be configurable:

* Trimester names
* Academic years
* Curriculum versions
* PO numbering scheme
* PEO numbering
* PO numbering
* PI numbering
* Knowledge Profile framework
* CEP framework
* CEA framework
* Accreditation terminology
* Effective curriculum
* Cohort-curriculum relationship

The application should be designed so that an institution can revise its academic framework without requiring significant software redevelopment.

---

# 46. Important Implementation Requirement

Before implementing these features, inspect the existing application architecture thoroughly.

Do not immediately modify the code.

First identify:

1. Existing user/role architecture
2. Authentication system
3. Course model
4. Curriculum model
5. Semester/trimester model
6. Student model
7. Faculty model
8. Existing cohort model
9. Existing permissions
10. Existing database relationships
11. Existing audit/versioning mechanism
12. Existing course/CO/PO structures
13. Existing UI navigation
14. Existing import/export mechanisms
15. Existing approval mechanisms

Then produce an implementation plan showing:

```text
Existing Architecture
        ↓
Required Changes
        ↓
Database Changes
        ↓
Backend/API Changes
        ↓
Permission Changes
        ↓
Workflow Changes
        ↓
UI Changes
        ↓
Migration/Backward Compatibility
        ↓
Testing
```

Do not create duplicate models or parallel workflows if equivalent structures already exist.

---

# 47. Validation Scenarios

Before considering this module complete, test at least the following scenarios.

### Curriculum

* Create a curriculum.
* Define institutional mission and visions.
* Define program mission and visions.
* Map institutional visions to program visions.
* Define PEOs.
* Map PEOs to program visions.
* Define POs.
* Select Direct Method.
* Define K/CEP/CEA.
* Map POs to K/CEP/CEA.
* Map POs to PEOs.
* Map COs to POs.
* Switch to Indicator-Based Method for a separate curriculum.
* Define PIs.
* Verify automatic PI numbering.
* Map POs/PIs to K/CEP/CEA.
* Map POs to PEOs.
* Map COs to PIs.
* Publish curriculum.
* Unpublish curriculum.
* Modify and republish.
* Verify version history.

### Trimester

* Create Spring/Summer/Fall trimester.
* Define academic calendar dates.
* Assign effective curriculum(s).
* Associate curricula with cohorts.
* Offer courses.
* Define sections.
* Import previous course offerings.
* Import faculty.
* Add/modify faculty.
* Activate/deactivate faculty.
* Assign faculty to sections.
* Import previous faculty assignments.
* Verify inactive faculty are never automatically assigned.
* Create a new cohort.
* Import an existing cohort.
* Edit imported student data.
* Verify student status is preserved.
* Verify current trimester is the default context.
* Verify previous trimester data remains unchanged.

### Feedback

* Program Coordinator views curriculum settings.
* Program Coordinator submits feedback.
* Administrator receives notification.
* Administrator reviews feedback.
* Administrator accepts/modifies or ignores feedback.
* Feedback remains auditable.

---

# 48. Future Roles

The detailed workflows and permissions for the following users will be specified separately and should **not be prematurely implemented beyond what is necessary to support the architecture described above**:

* Course Coordinator
* Course Faculty
* Students

However, the architecture must be designed so these roles can be integrated cleanly later without restructuring the core curriculum, trimester, course, faculty, cohort, and student models.

---

# 49. Overall Academic Data Relationship

The intended high-level relationship is:

```text
Institution
   │
   ├── Mission
   └── Institutional Visions
             │
             ↓
       Program
       ├── Mission
       ├── Program Visions
       │       ↓
       │   Vision Mapping
       │
       ├── PEOs
       │       ↓
       │   PEO ↔ Vision
       │
       ├── POs
       │       ↓
       │   PO ↔ PEO
       │
       ├── Knowledge Profiles
       ├── Complex Engineering Problems
       ├── Complex Engineering Activities
       │
       └── Curriculum
               │
               ├── Curriculum Version
               │
               ├── Direct Method
               │      └── PO ↔ CO
               │
               └── Indicator-Based Method
                      ├── PO
                      ├── PI
                      └── PI ↔ CO


Curriculum
    │
    ↓
Cohort
    │
    ↓
Students


Academic Trimester
    │
    ├── Effective Curriculum(s)
    │
    ├── Course Offerings
    │       └── Sections
    │             └── Faculty
    │
    └── Cohorts
          └── Students
```

This relationship should be reflected consistently across the database, API, business logic, permissions, and UI.
