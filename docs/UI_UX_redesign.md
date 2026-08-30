# OBEvolve UI/UX Design & Implementation Specification

## 1. Product

**OBEvolve** is an Outcome-Based Education (OBE) management and accreditation platform designed to manage curriculum, course outcomes, program outcomes, assessment, attainment, analytics, academic operations, and accreditation evidence.

The interface must feel like a **premium modern SaaS analytics platform**, not a traditional university ERP.

The UI should prioritize:

* Clarity
* Information hierarchy
* Minimal cognitive load
* Fast navigation
* Data-rich dashboards
* Professional academic/institutional appearance
* Responsive design
* Strong accessibility
* Consistent interaction patterns
* Role-aware navigation and content
* Excellent light and dark themes

---

# 2. Visual Direction

## Light Theme

Use this design as the primary visual reference:

https://dribbble.com/shots/27237292-E-Commerce-Dashboard-SaaS-Analytics-Sales-Management

The light theme should take inspiration from:

* Clean white and very-light-gray surfaces
* Soft card separation
* Generous whitespace
* Modern SaaS dashboard layouts
* Compact but readable data tables
* Rounded cards
* Subtle shadows
* Clear KPI blocks
* Professional typography
* Refined charts
* Minimal borders
* Strong visual hierarchy

Do **not** copy the reference literally. Use it as a visual language reference.

### Light Theme Characteristics

* Background: very light neutral gray
* Main content surfaces: white
* Secondary surfaces: soft gray
* Primary accent: OBEvolve brand color
* Status colors: semantic and restrained
* Borders: subtle
* Shadows: soft and low contrast
* Cards: moderately rounded
* Buttons: compact and polished
* Tables: clean, spacious and easy to scan

The interface should feel similar to a high-end analytics SaaS product.

---

# 3. Dark Theme

Use the Framer website as the visual inspiration for the dark theme:

https://www.framer.com/?utm_source=dribbble&utm_medium=paid&utm_campaign=agents&utm_content=display&dub_id=gKRURzvqZauYVqKk

The dark theme should feel:

* Premium
* Modern
* Sophisticated
* High contrast
* Minimal
* Slightly futuristic
* Suitable for long working sessions

### Dark Theme Characteristics

* Deep charcoal/near-black background
* Slightly lighter elevated surfaces
* Clear distinction between cards and page background
* Bright but controlled accent colors
* Subtle gradients where appropriate
* Strong typography contrast
* Minimal borders
* Soft glow/highlight effects only where they improve hierarchy
* Charts optimized specifically for dark mode

Avoid making the dark theme simply an inverted light theme.

Both themes should feel intentionally designed.

---

# 4. Brand Direction

OBEvolve should communicate:

> **Outcome Intelligence for Modern Education**

The product should feel like a combination of:

* Academic management platform
* Accreditation management system
* Assessment intelligence platform
* Analytics dashboard
* Institutional quality assurance platform

Avoid the visual appearance of:

* Legacy ERP software
* Government portals
* Generic CRUD applications
* Overly colorful education apps
* Dense administrative systems

---

# 5. Global Layout

Use a modern SaaS application shell.

```text
┌─────────────────────────────────────────────────────────────┐
│ Top Bar                                                     │
│ Search       Context / Breadcrumbs       Notifications User │
├──────────────┬──────────────────────────────────────────────┤
│              │                                              │
│              │                                              │
│   Sidebar    │              Main Content                    │
│              │                                              │
│              │                                              │
│              │                                              │
├──────────────┴──────────────────────────────────────────────┤
│ Optional contextual footer / status                         │
└─────────────────────────────────────────────────────────────┘
```

## Sidebar

The sidebar must be role-aware.

Only display menu sections that the current role can access.

Do not display inaccessible modules and then disable them.

### Sidebar behavior

* Collapsible
* Expanded by default on desktop
* Icon-only collapsed mode
* Tooltips in collapsed mode
* Active route clearly highlighted
* Nested navigation supported
* Smooth transitions
* Mobile drawer
* Role-aware visibility
* Permission-aware actions

Example:

```text
OBEvolve
────────────────────

Overview
Dashboard

Academic
  Courses
  Sections
  Faculty
  Students
  Enrollments
  Calendar

Assessment
  Assessment Types
  Rubrics
  Question Bank
  Assessments
  Marks Entry
  Attainment
  Pending Documents

Analytics
  PO Attainment
  Course Attainment
  Program Analytics

Settings
  Course Settings
  Program Settings
  Institute Settings
```

The actual sidebar must be generated from the user's role and permissions.

---

# 6. Top Navigation

The top bar should contain:

### Left

* Sidebar toggle
* Breadcrumb
* Current institution/program/course context

### Center

Global search where appropriate.

Search should eventually support:

* Courses
* Students
* Faculty
* Assessments
* POs
* COs
* Programs
* Documents

### Right

* Notifications
* Pending approvals indicator
* Help
* Theme toggle
* User profile
* Role/context indicator

Example:

```text
☰  OBEvolve / Assessment / Attainment

                                      🔔  ?  ☀  Nafees ▾
```

---

# 7. Dashboard

The dashboard should be highly role-aware.

Do not create one generic dashboard for every user.

The content should adapt based on the user's role and permissions.

## Dashboard Design

Use:

### KPI Cards

Examples:

```text
Courses
42
↑ 4 this semester

Students
1,284
+8.2%

PO Attainment
78.4%
↑ 3.1%

Pending Reviews
12
Needs attention
```

### Analytics

Use:

* Line charts
* Bar charts
* Donut charts
* Progress indicators
* Heatmaps
* Trend cards
* Attainment matrices

### Action Center

For users with approval permissions:

```text
Pending Actions

12 Assessment Documents
5 Attainment Reviews
3 Outcome Approvals
2 Program Approvals
```

Each item should link directly to the relevant workflow.

---

# 8. Role-Aware UX

OBEvolve must implement **RBAC consistently across the entire interface**.

There are three distinct states:

### Read

User can view information.

### Read + Write

User can:

* Create
* Edit
* Submit
* Upload
* Manage

where permitted.

### Approval

Some actions require a separate approval permission.

For example:

```text
Create/Edit
    ↓
Draft
    ↓
Submit
    ↓
Approval
    ↓
Published
```

Do not assume that write access automatically means approval access.

---

# 9. Permission-Aware UI

The frontend must respect the backend permission catalogue.

Permissions include:

```text
institution.manage
institution.view
org.manage
org.view
program.manage
program.view
program.approve
academic_calendar.manage
academic_calendar.view
user.manage
user.view
role.manage
role.view
curriculum.view
outcome.create
outcome.approve
mapping.create
section.manage
section.view
student.manage
student.view
grading.manage
grading.view
assessment.create
assessment.approve
assessment.view
marks.enter
attainment.calculate
attainment.approve
survey.manage
evidence.upload
accreditation.manage
report.generate
audit.view
raw_data.manage_all
raw_data.manage_institution
raw_data.manage_scoped
raw_data.propose_scoped
raw_data.approve
```

Never rely only on frontend visibility for security.

The backend remains authoritative.

---

# 10. Course Level Settings

Route:

```text
/course-settings
```

Use a tabbed or segmented SaaS interface.

### Tabs

* Courses
* Course Versions
* Course Outcomes

### Course List

Use a modern data table.

Columns:

| Course Code | Course | Credits | Category | Status | Actions |
| ----------- | ------ | ------: | -------- | ------ | ------- |

Features:

* Search
* Filter
* Sort
* Pagination
* Status badges
* Bulk selection where appropriate
* Create button where permitted
* Export where permitted

---

# 11. Course Versions

Show version history clearly.

Example:

```text
CSE 410
Software Engineering

Version History

v3     Published       Spring 2026
v2     Archived        Fall 2025
v1     Archived        Spring 2025
```

Workflow should be visually obvious.

Use status badges:

```text
Draft
Submitted
Under Review
Approved
Published
Rejected
Archived
```

---

# 12. Course Outcomes

Create a clean outcome management interface.

Example:

```text
CO1
Explain fundamental software engineering principles.

Bloom Level
Understand

Mapped POs
PO1 · PO3

Status
Published
```

Actions depend on permissions.

---

# 13. Program Level Settings

Route:

```text
/program-settings
```

Tabs:

* Curriculum
* PEOs
* Program Outcomes
* CO-PO Mapping
* PEO-PO Mapping
* Accreditation Framework

---

# 14. PEO Management

PEOs should be displayed as structured cards or rows.

Example:

```text
PEO 1

Graduates will demonstrate professional competence...

Status
Published

Last Updated
12 Aug 2026
```

Support:

* Create
* Edit
* Version
* Submit
* Approve
* Publish

according to permissions.

---

# 15. Program Outcomes

Use a structured PO interface.

Example:

```text
PO1
Engineering Knowledge

Description
Apply knowledge of mathematics, science...

Indicators
Coming later

Status
Published
```

The system should be designed so that **PO indicators can be introduced later without requiring a major UI redesign**.

---

# 16. CO-PO Mapping

This is a core OBEvolve feature and should receive a premium data visualization.

Use a matrix:

```text
             PO1   PO2   PO3   PO4   PO5
CO1           ●     ●
CO2                 ●     ●
CO3           ●           ●     ●
CO4                       ●     ●
```

Allow mapping strength indicators such as:

```text
Low
Medium
High
```

or the configured institutional mapping scale.

Use:

* Sticky headers
* Row/column highlighting
* Hover states
* Inline editing
* Keyboard navigation
* Clear legends
* Save/unsaved state

---

# 17. PEO-PO Mapping

Use a similar matrix interface but clearly distinguish it from CO-PO mapping.

Provide:

* PEO rows
* PO columns
* Mapping levels
* Save state
* Version context
* Approval state where applicable

---

# 18. Accreditation Framework

This area is read-only.

Display:

### Program Outcomes

PO catalogue

### Knowledge Profiles

WK catalogue

### Problem Attributes

WP catalogue

### Engineering Activities

EA catalogue

Use structured cards and expandable details.

Clearly indicate:

```text
Official Accreditation Framework
Read-only
```

Do not provide misleading edit buttons.

---

# 19. Academic Operations

Route:

```text
/academic
```

Tabs:

* Course Offerings
* Sections
* Faculty Assignments
* Enrollments
* Students
* Academic Calendar

Use consistent table components across all screens.

---

# 20. Assessment Module

Route:

```text
/assessment
```

This is one of the most important areas of OBEvolve.

Tabs:

* Assessment Types
* Rubrics
* Question Bank
* Assessments
* Marks Entry
* Attainment
* Pending Documents

---

# 21. Question Bank

Use a rich question-management interface.

Each question should show:

```text
Question
──────────────────────────
Explain the difference between...

Course
CSE 301

Bloom Level
Understand

CO Mapping
CO2

Difficulty
Medium

Status
Approved
```

Question detail should open in a drawer or dedicated page.

### Mappings Panel

Every question should support:

* Bloom's cognitive level
* Course Outcome mapping

The mapping interface should be accessible without overwhelming the question editor.

---

# 22. Assessment Builder

The assessment builder should feel like a modern document/workflow application.

Example:

```text
Midterm Examination
CSE 301

Assessment Details
────────────────────────

Date       15 Oct 2026
Duration   90 minutes
Total      50 marks

Questions
────────────────────────

Q1   10 marks   CO1   Understand
Q2   10 marks   CO2   Apply
Q3   15 marks   CO3   Analyze
Q4   15 marks   CO4   Evaluate
```

Provide a clear workflow:

```text
Draft → Submitted → Review → Approved → Published
```

---

# 23. Assessment Documents

Documents should be managed within the assessment context.

Document categories:

* Question Paper
* Moderation Form
* Compliance Form
* Answer Scripts
* Course Evaluation / CEP Documents
* Supporting Evidence

Each document should show:

```text
Document
Type
Uploaded By
Uploaded At
Status
Reviewer
Actions
```

Actions must be permission-aware.

---

# 24. Marks Entry

Marks entry must prioritize speed and accuracy.

Use spreadsheet-like interaction.

Example:

| Student ID | Student   | Q1 | Q2 | Q3 | Q4 | Total | Status   |
| ---------- | --------- | -: | -: | -: | -: | ----: | -------- |
| 241001     | Student A |  8 |  7 | 12 | 13 |    40 | Complete |
| 241002     | Student B |  6 |  9 | 10 | 12 |    37 | Complete |

Features:

* Keyboard navigation
* Copy/paste
* Validation
* Auto-save
* Draft state
* Missing mark detection
* Out-of-range validation
* Submission workflow
* Locking after approval

---

# 25. Attainment

Attainment is a core differentiator of OBEvolve.

The interface should visually communicate:

```text
Course
    ↓
Assessment
    ↓
Question
    ↓
CO
    ↓
Student CO Attainment
    ↓
Course CO Attainment
    ↓
PO Attainment
    ↓
Program Attainment
```

---

# 26. CO Attainment

Use KPI cards and visual analytics.

Example:

```text
CO1
82.4%
Target 70%
✓ Achieved

CO2
64.2%
Target 70%
⚠ Below Target

CO3
78.8%
Target 70%
✓ Achieved
```

Use clear visual distinction between:

* Achieved
* At risk
* Not achieved

---

# 27. Attainment Calculation

The interface should clearly show the calculation configuration.

For example:

```text
Student CO Attainment
──────────────────────

Assessment contribution
Quiz       20%
Midterm    30%
Final      50%

CO threshold
60%

Course attainment threshold
70% of eligible students
```

Support configuration where authorized.

The system must distinguish between:

* Student-level attainment
* Course-level attainment
* PO-level attainment
* Program-level attainment

---

# 28. Pending Documents

For users with `assessment.approve`, show a dedicated review queue.

Example:

```text
Pending Review

12 documents awaiting action

Assessment      Document           Submitted     Status
CSE301 Midterm  Question Paper     28 Aug        Review
CSE410 Final    Moderation Form    27 Aug        Review
```

Actions:

```text
Review
Approve
Reject
Request Changes
```

---

# 29. Analytics

Route:

```text
/analytics
```

Tabs:

* PO Attainment
* Program Analytics
* Course Attainment

Analytics must be visually rich but not decorative.

---

# 30. PO Attainment Dashboard

Include:

### Overall PO attainment

```text
PO1    82%
PO2    76%
PO3    71%
PO4    84%
PO5    68%
```

### Trend

Show attainment over semesters.

### Heatmap

```text
             Spring   Fall   Spring   Fall
PO1            72      75      80      82
PO2            68      71      73      76
PO3            65      68      70      71
```

### Risk indicators

Automatically highlight POs below configured thresholds.

---

# 31. Program Analytics

This is a read-only roll-up.

Provide:

* Program attainment
* PO distribution
* CO distribution
* Semester trends
* Course contribution
* Weak areas
* Strong areas

Do not create fake editing controls.

---

# 32. Course Attainment

Provide detailed course-level analytics.

Include:

* CO attainment
* Assessment contribution
* Student distribution
* PO contribution
* Historical comparison
* Threshold analysis

Where permitted, allow recalculation and configuration.

---

# 33. Institute Settings

Route:

```text
/organization
```

Tabs/cards:

* Institution
* Schools
* Departments
* Programs
* Users & Roles

Campuses should be embedded within Institution.

---

# 34. Users & Roles

Use a modern administration interface.

Example:

```text
Users

Name
Email
Role
Scope
Status
Last Active
Actions
```

Role management should provide a clear permission matrix.

Example:

```text
Permission                 Granted
────────────────────────────────────
assessment.create          ✓
assessment.approve         ✓
marks.enter                ✓
attainment.calculate       ✕
report.generate            ✓
```

Do not expose raw permission complexity unnecessarily to ordinary users.

---

# 35. Raw Data Console

The Raw Data Console is a privileged administrative interface.

It should feel intentionally different from normal application screens.

Provide:

* Database/table navigation
* Search
* Filters
* Structured data grid
* JSON/detail inspector
* Create/edit/delete where authorized
* Audit trail
* Scope indicator

Always display the current scope prominently.

Example:

```text
RAW DATA CONSOLE

Scope
Institution: ULAB
Access: Institution-wide

⚠ Administrative data access
```

---

# 36. Scoped Raw Data Workflow

For scoped proposal permissions:

```text
User Change
    ↓
Proposal Created
    ↓
Pending Approval
    ↓
Program Administrator Review
    ↓
Approved / Rejected
    ↓
Change Applied
```

Clearly distinguish proposed changes from live data.

---

# 37. About

Simple static informational page.

Do not over-design it.

Include:

* OBEvolve identity
* Version
* Platform information
* Accreditation framework information
* Documentation/help links

---

# 38. Platform Administrator

Platform Administrator is a separate system.

Route:

```text
/platform-login
```

After authentication:

```text
/platform
/platform/raw-data
```

Do not mix Platform Administrator navigation with tenant-level navigation.

---

# 39. Platform Dashboard

Display:

```text
Institutions
24

Active Institutions
21

Total Users
8,421

Active Programs
143
```

Institution table:

| Institution | Status | Programs | Users | Created | Actions |
| ----------- | ------ | -------: | ----: | ------- | ------- |

Create Institution should initiate tenant provisioning.

---

# 40. Platform Raw Data

Cross-institution data access.

Clearly show:

```text
Platform Scope
ALL INSTITUTIONS
```

This is outside the tenant RBAC system.

---

# 41. Roles

## Active by Default

### Super Administrator

Scope:

```text
Whole tenant
```

Full tenant control.

Visible sections:

* Dashboard
* Course Level Settings
* Program Level Settings
* Academic Operations
* Grading
* Assessment
* Analytics
* Institute Settings
* Raw Data Console
* About

---

### Institution Administrator

Scope:

```text
Whole tenant
```

Responsible for:

* Organization
* Programs
* Curriculum
* Academic operations
* Users
* Assessment
* Raw data within institution

---

### Program Administrator

Scope:

```text
One program
```

Responsible for:

* Program-level outcomes
* Mapping
* Academic operations
* Assessment
* Attainment
* Scoped raw data
* Approval workflows

---

### Program Coordinator

Scope:

```text
One program
```

Responsible primarily for:

* Course offerings
* Sections
* Faculty assignments
* Program coordination
* Read-only program-level information
* Scoped raw-data proposals

---

### Course Administrator

Scope:

```text
One course
```

Responsible for:

* Course information
* Course outcomes
* Course delivery
* Assessment
* Marks
* Attainment
* Course-scoped raw data

---

### Faculty

Scope:

```text
Assigned sections
```

Primary workflow:

```text
Teach Course
    ↓
Create Assessment
    ↓
Map Questions to COs
    ↓
Enter Marks
    ↓
Submit
    ↓
View Attainment
```

Faculty should not be presented with unnecessary administrative controls.

---

### Course Coordinator

Scope:

```text
One course
```

Faculty capabilities plus:

* Assessment approval
* Document review
* Attainment review
* Pending document queue

---

### Student

Scope:

```text
Own record
```

Student experience should be significantly simpler.

Navigation:

* Dashboard
* Course information
* Program information
* About

Dashboard should show:

```text
My Attainment

Overall
78%

PO1
82%
PO2
75%
PO3
79%

Current Courses
5
```

Students should never see administrative controls.

---

# 42. Seeded Disabled Roles

These roles exist but are disabled by default:

* Accreditation Administrator
* Dean
* Head of Department
* Examination/Assessment Administrator
* Quality Assurance Officer
* Accreditation Reviewer
* External Stakeholder

The UI should visually communicate:

```text
Disabled by default
```

when managing roles.

---

# 43. Accreditation Administrator

Scope:

```text
Whole tenant
```

Primary focus:

* Accreditation
* Evidence
* Analytics
* Program information

---

# 44. Dean

Scope:

```text
One school
```

Primary focus:

* Program oversight
* Curriculum
* Approvals
* Analytics

---

# 45. Head of Department

Scope:

```text
One department
```

Primary focus:

* Courses
* Curriculum
* Academic operations
* Assessment oversight
* Analytics

---

# 46. Examination / Assessment Administrator

Scope:

```text
Whole tenant
```

Primary focus:

* Assessment scheduling
* Assessment configuration
* Assessment approval
* Marks
* Attainment

---

# 47. Quality Assurance Officer

Scope:

```text
Whole tenant
```

Primary focus:

* Attainment monitoring
* Course analytics
* QA activities

---

# 48. Accreditation Reviewer

Scope:

```text
Assigned criteria
```

Read-only experience focused on:

* Courses
* Outcomes
* Program outcomes
* Mapping
* Accreditation framework
* Evidence

---

# 49. External Stakeholder

Scope:

```text
Survey only
```

The role currently has no operational menu beyond the basic system shell.

The future survey module should be designed independently.

---

# 50. Responsive Design

OBEvolve must work across:

* Desktop
* Laptop
* Tablet
* Mobile

Desktop is the primary workspace.

For mobile:

* Sidebar becomes drawer
* Tables become horizontally scrollable or card-based
* Complex matrices become horizontally scrollable
* Filters become drawers
* Actions remain accessible
* Avoid shrinking complex data until it becomes unreadable

---

# 51. Tables

Create one reusable table system.

Features:

* Search
* Filters
* Sorting
* Pagination
* Column visibility
* Density control
* Export
* Row actions
* Bulk actions
* Empty states
* Loading states
* Error states

Use consistent table behavior throughout OBEvolve.

---

# 52. Forms

Forms should use:

* Clear labels
* Helpful descriptions
* Inline validation
* Required indicators
* Grouped sections
* Autosave where appropriate
* Unsaved-change warnings
* Keyboard accessibility

Avoid extremely long forms.

Break complex workflows into logical steps.

---

# 53. Modals and Drawers

Prefer drawers for:

* Details
* Quick editing
* Reviewing records

Use full pages for:

* Complex workflows
* Assessment builder
* Curriculum management
* Analytics
* Large data-entry interfaces

Avoid unnecessary modal stacking.

---

# 54. Status System

Use consistent semantic statuses.

### Success

```text
Published
Approved
Achieved
Complete
```

### Warning

```text
Pending
At Risk
Needs Review
```

### Error

```text
Rejected
Failed
Below Threshold
```

### Neutral

```text
Draft
Archived
Inactive
```

Never rely only on color. Include text/icons.

---

# 55. Notifications

Notifications should be actionable.

Examples:

```text
Assessment approval required
CSE301 Midterm is awaiting review

PO attainment below threshold
PO4 dropped below the configured target

Marks submission
CSE410 marks are ready for approval
```

Clicking a notification should take the user directly to the relevant workflow.

---

# 56. Empty States

Every module needs a professional empty state.

Example:

```text
No assessments yet

Create your first assessment to begin
tracking CO attainment.

[ Create Assessment ]
```

Do not display blank tables without explanation.

---

# 57. Loading States

Use skeleton loaders rather than full-screen spinners whenever possible.

Tables:

```text
████████████
████████
██████████████
```

Cards should maintain their final dimensions during loading.

---

# 58. Error States

Errors should be understandable.

Avoid:

```text
Error 500
```

Prefer:

```text
Unable to load course outcomes

Something went wrong while retrieving this data.
Please try again.

[ Try Again ]
```

---

# 59. Accessibility

Target WCAG 2.1 AA or better.

Requirements:

* Keyboard navigation
* Visible focus states
* Semantic HTML
* Screen-reader labels
* Sufficient contrast
* Accessible tables
* Accessible charts
* No color-only meaning
* Reduced-motion support

---

# 60. Theme Switching

Provide:

```text
Light
Dark
System
```

Theme preference should persist.

Charts, tables, badges, inputs, dialogs and navigation must all respond correctly to theme changes.

Avoid flash of the wrong theme during page load.

---

# 61. Design Tokens

Centralize all design values.

Create tokens for:

```text
Colors
Typography
Spacing
Radius
Shadows
Borders
Transitions
Z-index
Breakpoints
```

Do not hard-code visual values throughout components.

---

# 62. Component System

Build reusable components.

At minimum:

```text
AppShell
Sidebar
TopBar
Breadcrumb
PageHeader
KPI Card
Stat Card
DataTable
FilterBar
SearchInput
StatusBadge
PermissionGate
RoleBadge
Tabs
Drawer
Modal
Form
EmptyState
ErrorState
Skeleton
Toast
NotificationPanel
ChartCard
AttainmentCard
Matrix
ApprovalQueue
FileUploader
AuditTimeline
```

---

# 63. Permission Components

Create reusable permission-aware components.

Conceptually:

```text
<Can permission="assessment.create">
    <CreateAssessmentButton />
</Can>
```

and:

```text
<Can permission="assessment.approve">
    <ApproveButton />
</Can>
```

The frontend should hide or disable actions based on permissions, while backend authorization remains mandatory.

---

# 64. Scope Awareness

The UI must always communicate the user's data scope.

Examples:

```text
Institution-wide
Program: CSE
Course: CSE301
Assigned Section
Own Record
```

Scope should appear in relevant headers, filters or context selectors.

This is particularly important for:

* Program Administrator
* Program Coordinator
* Course Administrator
* Course Coordinator
* Faculty
* Student

---

# 65. Approval UX

Approval should be a first-class workflow.

Example:

```text
                    ┌────────────┐
                    │    Draft   │
                    └─────┬──────┘
                          ↓
                    ┌────────────┐
                    │ Submitted  │
                    └─────┬──────┘
                          ↓
                    ┌────────────┐
                    │  Review    │
                    └─────┬──────┘
                          ↓
                  ┌───────┴────────┐
                  ↓                ↓
              Approved          Rejected
                  ↓                ↓
             Published        Changes Needed
```

Use timelines and status indicators rather than relying only on text.

---

# 66. Audit Trail

Where appropriate, provide:

```text
Activity

29 Aug 2026
Dr. X changed CO2 mapping

28 Aug 2026
Dr. Y submitted assessment

27 Aug 2026
Dr. Z approved question paper
```

Audit information should be immutable and clearly differentiated from ordinary activity.

---

# 67. Data Visualization Principles

Charts should answer a question.

Avoid decorative charts.

Good examples:

* PO attainment trend
* CO attainment distribution
* Course contribution to PO
* Student attainment distribution
* Assessment contribution
* Threshold comparison
* Semester comparison

Every chart should provide:

* Title
* Context
* Units
* Legend where needed
* Tooltip
* Accessible textual interpretation where appropriate

---

# 68. Core UX Principle

OBEvolve should progressively expose complexity.

A:

```text
Student
```

should see a simple academic dashboard.

A:

```text
Faculty
```

should see teaching and assessment workflows.

A:

```text
Program Administrator
```

should see program-level OBE management.

A:

```text
Super Administrator
```

can access the full institutional system.

Do not expose the full complexity of OBEvolve to every user.

---

# 69. Critical UX Rule

**Visibility and authorization are separate concepts.**

The frontend should determine:

```text
What should this user see?
```

The backend should determine:

```text
What is this user actually allowed to do?
```

Never treat hidden UI elements as a security mechanism.

---

# 70. Design Quality Bar

The final interface should look like a product that could compete with premium modern SaaS applications.

It should be:

* Polished
* Cohesive
* Fast
* Minimal
* Professional
* Data-rich
* Intuitive
* Responsive
* Accessible
* Role-aware

Avoid:

* Generic Bootstrap appearance
* Excessive borders
* Excessive shadows
* Huge headings
* Random colors
* Inconsistent spacing
* Inconsistent buttons
* Dense legacy ERP layouts
* Unnecessary animations
* Decorative UI that does not improve usability

---

# 71. Implementation Priority

Implement the UI in this order:

### Phase 1

* App shell
* Sidebar
* Top bar
* Theme system
* Dashboard
* Permission-aware navigation
* Role-aware rendering

### Phase 2

* Course Settings
* Program Settings
* Academic Operations
* Institute Settings

### Phase 3

* Assessment
* Question Bank
* Assessment Builder
* Marks Entry
* Documents
* Approval workflows

### Phase 4

* Attainment
* PO Analytics
* Course Analytics
* Program Analytics
* Visualization system

### Phase 5

* Raw Data Console
* Platform Administrator
* Audit interfaces
* Advanced administration

---

# 72. Final Design Instruction

Treat the supplied Dribbble light-theme reference and Framer dark-theme reference as **visual quality benchmarks**, not templates to copy.

The result should be unmistakably **OBEvolve**.

The interface should combine:

```text
Modern SaaS UX
        +
OBE / Accreditation Intelligence
        +
Academic Workflow
        +
Assessment Management
        +
Institutional Analytics
```

The final experience should make complex OBE processes feel simple, structured and understandable.

**Build the interface as a premium, production-grade SaaS application rather than an academic CRUD dashboard.**
