## Course-Level Settings and Approval Workflow

Implement the following functionality for **Course Level Settings** and course configuration/approval workflows.

### 1. Course Type Management

Under **Course Level Settings**, the **Program Coordinator and/or Section Coordinator** should be able to:

* Add a new Course Type.
* Remove an existing Course Type.
* View all currently configured Course Types.
* Ensure that removing a Course Type does not unintentionally delete historical course data associated with that type.

### 2. Configurable Course-Level Sections

For each Course Type, the administrator should be able to independently **enable or disable** the following course-level configuration sections:

* Course Overview
* Course Settings
* Students / Student Enrollment
* Assessments

The configuration should clearly indicate whether each section is currently enabled or disabled.

### 3. Course Teacher Editing Permissions

When a particular course-level section is **enabled**, the Course Teacher should see a **green "Edit" button** against that corresponding section in their course interface.

For example:

| Course Section  | Enabled | Course Teacher    |
| --------------- | ------- | ----------------- |
| Course Overview | Yes     | Green Edit button |
| Course Settings | No      | No Edit button    |
| Students        | Yes     | Green Edit button |
| Assessments     | Yes     | Green Edit button |

If a section is disabled, the Course Teacher should not be allowed to edit that section.

### 4. Change Submission and Approval Workflow

Any modification made by a Course Teacher must **not immediately become final**.

Instead, the change should follow an approval workflow.

#### Step 1: Course Teacher

The Course Teacher makes changes to an enabled course-level section and submits the changes.

The system should:

* Record the proposed changes.
* Preserve the existing/current version.
* Create a pending change/request.
* Record who made the change and when.
* Clearly indicate that the change is awaiting approval.

#### Step 2: Section Coordinator

The submitted change first goes to the **Section Coordinator** for review.

The approver should be able to:

* View the proposed changes.
* Compare the existing value with the proposed value.
* Edit/modify the proposed changes before approval.
* Accept/approve the changes.
* Reject the changes.
* Return/revise the changes where appropriate.

### 5. Different Approval Levels

Not all changes require the same approval level.

#### A. Course Overview

Changes to **Course Overview** can be directly accepted by the Section Coordinator.

Workflow:

**Course Teacher → Section Coordinator → Final**

Once accepted, the changes become the current course data.

#### B. Student Enrollment

Changes related to **Student Enrollment** can also be directly accepted by the Section Coordinator.

Workflow:

**Course Teacher → Section Coordinator → Final**

#### C. Other Course-Level Changes

Changes to:

* Course Settings
* Assessments
* Any other configured course-level section requiring higher approval

must follow a two-stage approval process:

**Course Teacher → Section Coordinator → Program Coordinator → Final**

The Section Coordinator first reviews and approves the proposed change.

After the Section Coordinator accepts it, the request moves to the **Program Coordinator** for final approval.

Only after the Program Coordinator approves the request should the proposed change become the final/current course configuration.

### 6. Editing During Approval

An **Edit** option must be available to the approver during every approval stage.

For example:

**Course Teacher submits → Section Coordinator reviews → Edit/Accept/Reject**

If accepted:

**Section Coordinator approves → Program Coordinator reviews → Edit/Accept/Reject**

If the Section Coordinator or Program Coordinator edits the proposed change, the system should maintain a clear audit trail showing:

* Original value
* Proposed value
* Modified value
* User who made the modification
* Timestamp
* Approval status

The system should never silently overwrite previous values.

### 7. Approval Status

Each pending change should have a clear status, such as:

* Draft
* Pending Section Coordinator
* Pending Program Coordinator
* Approved
* Rejected
* Returned for Revision

The relevant users should be able to see pending approvals from their dashboard or course management interface.

### 8. Semester-Based Course Visibility

For **all users and all course-selection interfaces**, the default view must contain **only courses from the current semester**.

This applies to:

* Dropdown menus
* Course tables
* Course lists
* Course assignment interfaces
* Course configuration interfaces
* Course management screens
* Other relevant course selectors

Do not mix previous-semester courses into the default current-semester view.

### 9. Accessing Previous-Semester Courses

Previous-semester courses must remain accessible, but through a **separate explicit action**, such as:

**"View Previous Semesters"**

or

**"Previous Courses"**

When the user selects this option, they should be able to select a previous semester and view the corresponding courses.

The historical courses should remain available for:

* Viewing
* Historical records
* Reference
* Appropriate administrative operations

Do not treat previous-semester courses as current courses.

### 10. Import Functionality

Whenever a user is **offering courses or configuring a course**, provide an **Import** option.

The import functionality should allow the user to reuse relevant information from an existing course, particularly a course from a previous semester.

For example:

**Offer Course → Add Course → Import**

or

**Configure Course → Import Previous Configuration**

The user should be able to select an appropriate previous course/semester and import its relevant configuration.

The import process should preferably allow the user to review what will be imported before confirming.

### 11. Important Data Integrity Rules

Implement the workflow without destroying existing or historical data.

In particular:

* Never overwrite an approved/current configuration directly when a teacher submits a change.
* Store pending changes separately until they are approved.
* Preserve historical versions where appropriate.
* Previous-semester course data must remain intact.
* Approval actions must be auditable.
* Changes must be associated with the user who performed them.
* Current-semester filtering should be based on the system's active/current semester configuration rather than hard-coded dates or semester names.

### 12. UI/UX Expectations

Keep the workflow simple and obvious.

Use clear visual indicators for:

* Enabled/disabled configuration sections
* Editable sections
* Pending approval
* Approval stage
* Approved/rejected status
* Current vs previous semester

Use a **green Edit button** for sections that are enabled for Course Teacher editing.

For approval requests, provide a clear review interface showing:

**Current Value → Proposed Value → Final/Edited Value**

with appropriate **Edit, Approve, Reject, and Return** actions based on the user's role.

### 13. Role-Based Access Control

Enforce these permissions at both the **UI level and backend/API level**.

Do not rely solely on hiding buttons.

The system must verify that:

* Course Teachers can only edit sections enabled for their Course Type.
* Section Coordinators can review and approve teacher submissions.
* Section Coordinators can directly finalize Course Overview and Student Enrollment changes.
* Program Coordinators can provide final approval for changes requiring program-level approval.
* Users cannot bypass the approval workflow through direct API/database operations.

### 14. Implementation Requirement

Before implementing this functionality:

1. Inspect the existing project architecture.
2. Identify the existing course, semester, role/permission, configuration, and approval models.
3. Reuse existing structures wherever possible.
4. Do not introduce duplicate models or workflows unnecessarily.
5. Check how current-semester courses are currently determined.
6. Check existing role-based access control.
7. Check whether an approval/versioning mechanism already exists.
8. Integrate this functionality into the existing architecture rather than creating an isolated parallel system.

After implementation, verify the complete workflow using realistic scenarios, including:

* Teacher edits Course Overview → Section Coordinator approves → finalized.
* Teacher edits Student Enrollment → Section Coordinator approves → finalized.
* Teacher edits Course Settings → Section Coordinator approves → Program Coordinator approves → finalized.
* Section Coordinator edits a pending request before approval.
* Program Coordinator edits a pending request before final approval.
* Teacher attempts to edit a disabled section.
* Previous-semester courses are hidden from default current-semester lists.
* Previous-semester courses can be accessed through the dedicated previous-semester option.
* A new course can import configuration from a previous-semester course.
* Historical data remains unchanged after importing or modifying a course.
* Unauthorized users cannot bypass the approval workflow.

Do not make assumptions about existing architecture. First inspect the codebase and existing patterns, then implement the feature consistently with the current system.
