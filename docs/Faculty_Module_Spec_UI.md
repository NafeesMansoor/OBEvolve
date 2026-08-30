# OBEvolve Faculty Module

## Functional and UI Specification

---

# 1. Faculty Module Overview

The Faculty module provides faculty members with access to their current and previous courses, course-level management, required course-file submissions, student enrollment, assessments, marks entry, grading, attainment calculations, and course analytics.

The faculty dashboard should be centered around the **current academic semester** while retaining access to courses and records from previous semesters. Any change request by faculty should forward to the Course Coordinator. 

---

# 2. Faculty Dashboard

## 2.1 Dashboard Overview

The Faculty Dashboard should contain the following sections:

### Current Courses

Displays all courses assigned to the faculty member in the **current academic semester**.

Each course card should display:

* Course Code
* Course Title
* Section
* Credit Hours
* Schedule
* Number of Students
* Course File Completion Status
* Assessment/Marks Status
* Action Required indicator

Selecting a course opens the **Course Management** page for that course and section.

---

### Students

Displays student information associated with the faculty member's courses in the **current semester**.

Faculty should be able to:

* View course-wise students
* View student ID
* View student name
* View enrollment information
* Add a student to a course
* Remove a student where permitted by institutional policy

Student enrollment management should be performed at the **course and section level**.

---

### Previous Courses

Displays courses taught by the faculty member in **earlier semesters**.

Faculty can select a previous course to:

* View course information
* View course files
* View assessments
* View submitted marks
* View grades
* View historical attainment
* View analytics
* Reuse eligible course configuration/question-bank content where permitted

Historical course records should not be editable unless the system explicitly permits an administrative correction workflow.

---

### Action Required

Displays pending faculty actions, particularly:

* Course files that need to be uploaded
* Mandatory documents approaching deadline
* Overdue submissions
* Pending assessment configuration
* Pending marks entry
* Pending grade submission
* Other course-level actions requiring faculty attention

Each item should provide a direct link to the relevant course and action.

---

# 3. Faculty Course Management

When a faculty member selects a course from **Current Courses**, the system should open the course-level management interface.

The course header should display:

> **CSE2301 | Database Management Systems | Section 1**
> Summer 2026 · 3 Credits · Dr. Nafees Mansoor

The course-level navigation should contain:

1. Overview
2. Course Settings
3. Course Files
4. Students
5. Assessments
6. Marks Entry
7. Grades
8. Analytics

---

# 4. Course Settings

Course Settings contains the approved academic and operational information associated with the selected course and section.

## 4.1 Course Settings Tabs

| Tab                          | Contents                                                                                                                                                                                                 | Faculty Access                                                                           |
| ---------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| **Overview**                 | Term, Course Title, Course Code, Section, Credit Hours, Class Schedule, Prerequisite, Program, Faculty, Contact Email, Office & Location, Consultation Hours, Classroom/Meeting Link, Number of Lectures | View. Faculty can edit Office & Location, Consultation Hours, and Classroom/Meeting Link |
| **Course Description**       | Course Description / Rationale, Course Objectives                                                                                                                                                        | Request Modification                                                                     |
| **Course Outcomes**          | CO1, CO2, CO3 and descriptions                                                                                                                                                                           | Request Modification                                                                     |
| **TLA & Assessment Mapping** | CO → Delivery Methods / Activities → Assessment Tools                                                                                                                                                    | Request Modification                                                                     |
| **Learning Materials**       | Textbooks, Reference Books, Other Course Resources                                                                                                                                                       | Request Modification                                                                     |
| **Assessment & Weights**     | Midterm, Final, Project, Participation, Quiz, Percentages, Total                                                                                                                                         | Request Modification                                                                     |
| **Grading Policy**           | Grade ranges, Letter Grades, Grade Points, Descriptions, I/W/AW policies                                                                                                                                 | Request Modification                                                                     |
| **Change Requests**          | Submitted requests, status, comments, approval history                                                                                                                                                   | View / Create                                                                            |
| **Audit History**            | Changed field, previous value, new value, changed by, date/time                                                                                                                                          | View                                                                                     |

---

## 4.2 Modification Workflow

For information controlled by the academic/program administration, faculty should not directly edit the approved value.

Instead:

**Current Value → Request Modification → Proposed Value → Reason → Submit → Review → Approve/Reject**

Each request should contain:

* Field being changed
* Current value
* Proposed value
* Reason
* Supporting document, if required
* Submitted by
* Submission date
* Status
* Reviewer
* Reviewer comments
* Approval/rejection date

---

# 5. Course Files

Course-level document management should be placed under a dedicated section called:

## **Course Files**

Each required document must have a **separate upload option** on the respective course page.

The system should not use one generic "Upload Course Documents" button.

Each document should have its own:

* Upload button
* Current file/status
* Submission status
* Submission deadline
* Required/Optional indicator
* Submission date
* Version
* Replace/update option, where permitted
* Approval/review status, if applicable

---

# 6. Course Files for Theory Courses

The following files should be available for regular/theory courses.

## 6.1 Course Outline

**Required/Optional:** Configurable by Program Administrator/Coordinator.

---

## 6.2 Attendance

Attendance should contain separate upload options:

### Class Attendance

Upload class attendance record.

### Mid-Term Attendance

Upload mid-term attendance record.

### Final-Term Attendance

Upload final-term attendance record.

---

## 6.3 Mid-Term Examination Files

Separate upload options:

1. Mid-Term Question Moderation
2. Mid-Term Question
3. Highest Sample Answer Script
4. Medium Sample Answer Script
5. Lowest Sample Answer Script

---

## 6.4 Final Examination Files

Separate upload options:

1. Final Question Moderation
2. Final Question
3. Highest Sample Answer Script
4. Medium Sample Answer Script
5. Lowest Sample Answer Script

---

## 6.5 Final Grade Report

Upload final grade report.

---

## 6.6 Marks Excel Breakdown

Upload the marks breakdown Excel file.

---

## 6.7 Complex Engineering Project

For **Dominant Courses** only:

1. Complex Engineering Project Form
2. Complex Engineering Project Report
3. Highest Rubric / Sample
4. Medium Rubric / Sample
5. Lowest Rubric / Sample

---

## 6.8 Additional Course Files

The following should also be available:

* CO-PO Excel File
* CQI Form
* Excuse Absent Form
* Class Summary Report

---

# 7. Course Files for Lab Courses

For laboratory courses, the Course Files section should contain:

### Basic Course Documents

1. Course Outline

### Attendance

2. Class Attendance
3. Mid-Term Attendance
4. Final-Term Attendance

### Assessment/Grade Documents

5. Final Grade Report
6. Marks Excel Breakdown

### Laboratory Documents

7. List of Lab Tasks

### Open-Ended Lab

8. Open-Ended Lab Form
9. Open-Ended Lab Report
10. Highest Rubric / Sample
11. Medium Rubric / Sample
12. Lowest Rubric / Sample

### Complex Engineering Project

For **Dominant Lab Courses**:

13. Complex Engineering Project Form
14. Complex Engineering Project Report
15. Highest Rubric / Sample
16. Medium Rubric / Sample
17. Lowest Rubric / Sample

The system should support both **soft-copy and hard-copy status** for CEP documentation where required.

### Additional Files

18. CO-PO Excel File
19. CQI Form
20. Excuse Absent Form
21. Class Summary Report

---

# 8. Semester-Level Course File Configuration

During semester configuration, the **Program Administrator or Program Coordinator** should configure the submission requirements for course files.

For each document, the configuration should support:

* Required / Optional
* Submission deadline
* Applicable course
* Applicable course type
* Applicable program
* Applicable semester
* Soft copy required
* Hard copy required, where applicable

---

## 8.1 Course-Wise vs Holistic Configuration

The administrator/coordinator should be able to configure requirements:

### Course-wise

Different requirements can be assigned to individual courses.

### Holistically

A common configuration can be applied to all applicable courses.

For example:

> Course Outline → Mandatory → Deadline: Week 2

can be applied to all courses.

---

# 9. Import Configuration from Previous Semester

When configuring a new semester, the administrator/coordinator should have an option:

**Import Previous Semester Configuration**

Example:

> Import configuration from: **Spring 2026**

The system copies:

* Required/Optional status
* Deadlines
* Course-file requirements
* Course-type rules
* Other applicable configuration

The administrator/coordinator can then modify the imported configuration before activating the new semester.

---

# 10. Student Enrollment

A dedicated faculty menu item should be available for:

## **Students / Enrollment**

This replaces the need for faculty to access the broader Academic Operations module.

Academic Operations should **not be displayed to faculty** because faculty cannot read or write data within that module.

---

## 10.1 Course-Level Student List

After selecting:

**Course → Section**

the faculty member sees the enrolled students.

| Student ID | Student Name | Enrollment Status |
| ---------- | ------------ | ----------------- |
| 2026-001   | Student A    | Enrolled          |
| 2026-002   | Student B    | Enrolled          |

Faculty should have an:

**+ Add Student**

option.

The system should prevent duplicate enrollment of the same student into the same course and section.

---

# 11. Assessment Module

The faculty Assessment module should be accessed by:

**Assessment → Select Course → Select Section**

The faculty member should only see courses assigned to them.

---

# 12. Assessment Type

The general **Assessment Type configuration** should not appear as a separate faculty menu/configuration item.

The assessment form should handle assessment type as part of assessment creation.

Faculty should not see separate administrative configuration for:

* Assessment Type
* Rubric Management

---

# 13. Creating a New Assessment

When creating a new assessment, the form should contain:

* Assessment Title
* Academic Term
* Course
* Section
* Assessment Type
* Total Marks
* Weight (%)
* Exam/Assessment Date
* Duration
* Rubric Required? Yes/No
* Rubric Upload, if applicable
* Questions Required? Yes/No
* Question Upload, if applicable

The **Academic Term** should be automatically populated based on the selected course.

---

# 14. Standard Assessments

The system should treat the following as structured assessments:

* Mid-Term Examination
* Final Examination
* Complex Engineering Project
* Open-Ended Lab Problem

These assessments require specialized forms.

Other assessments can use the general assessment creation form.

---

# 15. Mid-Term and Final Examination Question Management

For Mid-Term and Final examinations, faculty should enter individual questions rather than simply uploading a question paper.

Each question should contain:

* Question
* Marks
* CO
* Bloom's Level
* Global Sharing: Yes / No

Default:

> **Global Sharing = No**

---

## 15.1 Examination Marks Validation

The assessment cannot be finalized until:

**Sum of Question Marks = Examination Total Marks**

Example:

> Examination Total = 50
> Question Total = 47

Status:

**Incomplete: Question marks must total 50.**

Only when:

> Question Total = Examination Total

can the examination be finalized.

---

# 16. Question Bank

Faculty should be able to reuse questions from the existing Question Bank.

Workflow:

**Add Question → Question Bank → Search/Filter → Select Question → Add to Assessment**

When an existing question is reused, the faculty member should be able to modify assessment-specific metadata:

* Marks
* CO
* Bloom's Level

The original question-bank question should remain unchanged unless the faculty explicitly creates a new version.

---

# 17. Global Question Sharing

For each examination question:

**Share Globally?**

* No — Default
* Yes

If **Yes**, the question becomes available to:

* Faculty teaching the same course in the current semester
* Faculty teaching the same course in future semesters

The question should then be searchable from the Question Bank.

Questions marked **No** remain private to the faculty member/course context according to institutional policy.

---

# 18. Complex Engineering Project

For CEP, the faculty member should create a project/problem using a dedicated form.

Each CEP problem should contain:

* Problem
* Purpose
* Tasks

Each task should contain:

* Task Description
* CO
* PO
* K/P/A
* Marks

The **K/P/A field may be null/empty** where not applicable.

The system should validate that all required CEP mappings are completed before the problem is finalized.

---

# 19. Open-Ended Lab Problem

For OEP, the problem form should contain:

* Problem
* Purpose
* Tasks

Each task should contain:

* Task Description
* CO
* Marks

Unlike CEP, PO and K/P/A are not required for OEP tasks.

---

# 20. Marks Entry

Marks Entry should only permit modification for:

> **Current Semester Courses**

Previous-semester marks should be view-only for faculty.

---

## 20.1 Marks Entry Workflow

Faculty selects:

**Course → Section → Assessment**

The system automatically generates the enrolled student list.

Example:

| Student ID | Student Name | Q1 | Q2 | Q3 | Q4 | Total |
| ---------- | ------------ | -: | -: | -: | -: | ----: |
| 20260101   | Student A    |  8 |  7 |  9 |  8 |    32 |
| 20260102   | Student B    |  7 |  9 |  8 |  9 |    33 |

The columns should automatically correspond to:

* Examination questions, for Mid-Term/Final
* Project tasks, for CEP
* Lab problem tasks, for OEP
* Other assessment components where applicable

---

## 20.2 Save Marks

The marks-entry page must have:

**Save**

Saved marks can be modified by the faculty member.

Saving does **not** finalize the marks.

---

# 21. Grades

The Grades tab should provide a consolidated view of student performance.

Faculty selects:

**Course → Section**

The system displays:

| Student ID | Student Name | Midterm | Final | Project | Quiz | Participation | Total | Letter Grade |
| ---------- | ------------ | ------: | ----: | ------: | ---: | ------------: | ----: | ------------ |

The system automatically calculates:

* Assessment totals
* Weighted marks
* Overall marks
* Letter Grade
* Grade Point

The grading policy configured for the course should be used for grade calculation.

---

# 22. Grade Submission

The Grades page should contain:

**Save**

and

**Submit Final Grades**

### Save

* Saves current calculations/data
* Faculty can continue modifying marks
* Does not finalize the grades

### Submit Final Grades

Once submitted:

* Faculty can no longer modify the marks
* Faculty can no longer modify the grades
* The submission becomes final for the faculty workflow
* Submission date/time is recorded
* Faculty identity is recorded

---

# 23. Grade Submission Validation

The **Submit Final Grades** button should only become enabled when all required assessments have been recorded.

The system should verify:

> **100% of the assessment weight has been recorded**

Example:

| Assessment    |   Weight | Recorded     |
| ------------- | -------: | ------------ |
| Midterm       |      25% | ✓            |
| Final         |      40% | ✓            |
| Project       |      20% | ✓            |
| Quiz          |      10% | ✓            |
| Participation |       5% | ✓            |
| **Total**     | **100%** | **Complete** |

If only 85% has been recorded:

> **Submission unavailable. 15% of assessment weight is still incomplete.**

---

# 24. Attainment Calculation

Upon successful submission of final grades, the system should automatically calculate and store:

### CO Attainment

Course Outcome attainment based on the assessment/question/task mappings and student performance.

### PO Attainment

Program Outcome attainment based on the applicable CO/PO mappings and assessment results.

The calculated attainment data should be stored in the database as a historical record associated with:

* Academic term
* Course
* Section
* Assessment
* Student
* CO
* PO
* Faculty
* Submission/version

Attainment calculations should be reproducible from the stored assessment and mapping data.

---

# 25. Analytics

The Faculty Analytics module should provide course-level analytical dashboards.

Faculty selects:

**Course → Section → Analytics**

---

## 25.1 Assessment-Wise Analytics

Analytics should include:

* Assessment average
* Highest mark
* Lowest mark
* Median
* Standard deviation
* Pass/fail distribution
* Score distribution
* Assessment-wise performance

Possible visualizations:

* Bar charts
* Histograms
* Box plots
* Distribution charts
* Performance tables

---

# 26. Grade-Wise Analytics

Show:

* A+ count
* A count
* A- count
* B+ count
* B count
* B- count
* C+ count
* C count
* D count
* F count
* I/W/AW where applicable

Visualizations:

* Grade distribution bar chart
* Grade percentage chart
* Pass/fail chart

---

# 27. CO Attainment Analytics

Provide course-level CO attainment.

Example:

| CO  | Target | Attainment | Status       |
| --- | -----: | ---------: | ------------ |
| CO1 |    70% |        82% | Achieved     |
| CO2 |    70% |        68% | Not Achieved |
| CO3 |    70% |        76% | Achieved     |

Analytics should support:

* CO-wise attainment
* Assessment-wise CO attainment
* Student-wise CO attainment
* CO achievement status
* CO comparison

---

# 28. PO Attainment Analytics

Provide:

* PO-wise attainment
* CO-to-PO contribution
* Assessment-to-PO contribution
* Student-level PO attainment where applicable
* PO achievement status

Example:

| PO  | Target | Attainment | Status       |
| --- | -----: | ---------: | ------------ |
| PO1 |    70% |        78% | Achieved     |
| PO2 |    70% |        72% | Achieved     |
| PO3 |    70% |        64% | Not Achieved |

---

# 29. Analytics Filters

Faculty should be able to filter analytics by:

* Academic Term
* Course
* Section
* Assessment
* Assessment Type
* CO
* PO
* Student
* Grade
* Achievement Status

Where appropriate, multiple filters should be combinable.

Example:

> Course: CSE2301
> Section: 1
> Assessment: Midterm
> CO: CO2
> Status: Not Achieved

The system then generates the corresponding graphical and tabular report.

---

# 30. Faculty Navigation

The final Faculty navigation should be:

```text
Faculty
│
├── Dashboard
│   ├── Overview
│   ├── Current Courses
│   ├── Students
│   ├── Previous Courses
│   └── Action Required
│
├── Courses
│   └── Course Selection
│       └── Course Management
│           ├── Overview
│           ├── Course Settings
│           ├── Course Files
│           ├── Students
│           ├── Assessments
│           ├── Marks Entry
│           ├── Grades
│           └── Analytics
│
└── Question Bank
```

**Academic Operations should not appear in the Faculty navigation.**

---

# 31. Faculty Permissions Summary

| Function                           | Faculty Permission    |
| ---------------------------------- | --------------------- |
| View Current Courses               | Yes                   |
| View Previous Courses              | Yes                   |
| View Program-Level Settings        | View Only             |
| Edit Program-Level Settings        | No                    |
| View Academic Operations           | No                    |
| Manage Course Settings             | Limited               |
| Edit Office Information            | Yes                   |
| Edit Consultation Hours            | Yes                   |
| Edit Classroom/Meeting Link        | Yes                   |
| Modify Academic Course Information | Request Only          |
| Upload Course Files                | Yes                   |
| View Course Files                  | Yes                   |
| Manage Students/Enrollment         | Yes, course-wise      |
| Create Assessment                  | Yes                   |
| Create Midterm/Final Questions     | Yes                   |
| Reuse Question Bank Questions      | Yes                   |
| Globally Share Questions           | Yes                   |
| Create CEP Problems                | Yes, where applicable |
| Create OEP Problems                | Yes, where applicable |
| Enter Current Semester Marks       | Yes                   |
| Modify Saved Marks                 | Yes                   |
| Enter Previous Semester Marks      | No                    |
| View Previous Semester Marks       | Yes                   |
| Save Grades                        | Yes                   |
| Submit Final Grades                | Yes                   |
| Modify Grades After Submission     | No                    |
| View CO Attainment                 | Yes                   |
| View PO Attainment                 | Yes                   |
| View Analytics                     | Yes                   |
| Modify Attainment Manually         | No                    |
| View Audit History                 | Yes                   |
| Create Change Request              | Yes                   |
| Approve Change Request             | No                    |

---

# 32. Core Business Rules

### BR-01: Current Semester

Faculty editing capabilities apply only to courses in the **current active semester**.

### BR-02: Previous Semesters

Previous-semester course records, marks, grades, and attainment data are view-only for faculty.

### BR-03: Course Ownership

Faculty can only manage courses and sections to which they are currently assigned.

### BR-04: Course Files

Each required document must have an independent upload control and submission status.

### BR-05: File Requirements

Required/optional status and deadlines are controlled by the Program Administrator/Coordinator during semester configuration.

### BR-06: Configuration Reuse

Semester configurations can be imported from a previous semester and subsequently modified.

### BR-07: Question Marks

For Midterm and Final examinations:

> `Sum(question marks) = assessment total marks`

must be satisfied before the assessment can be finalized.

### BR-08: Marks Entry

Marks are generated against the currently enrolled student list.

### BR-09: Grade Submission

Faculty may save grades multiple times before final submission.

### BR-10: Final Submission

After final grade submission, faculty cannot modify the submitted marks or grades.

### BR-11: Assessment Completion

Final grade submission is enabled only when:

> `Recorded Assessment Weight = 100%`

### BR-12: Attainment

CO and PO attainment calculations are automatically triggered after final grade submission.

### BR-13: Historical Data

Submitted grades and attainment results must remain historically traceable.

### BR-14: Auditability

Changes to important academic information must maintain:

* Previous value
* New value
* User
* Timestamp
* Action
* Approval status, where applicable

---

# 33. Overall Faculty Workflow

```text
Faculty Login
      │
      ▼
Faculty Dashboard
      │
      ├──────────────► Previous Courses
      │
      ▼
Current Courses
      │
      ▼
Select Course + Section
      │
      ▼
Course Management
      │
      ├── Overview
      │
      ├── Course Settings
      │      └── View / Edit / Request Modification
      │
      ├── Course Files
      │      └── Upload Required Documents
      │
      ├── Students
      │      └── View / Add Enrollment
      │
      ├── Assessments
      │      ├── Create Assessment
      │      ├── Create Questions
      │      ├── Question Bank
      │      ├── CEP
      │      └── OEP
      │
      ├── Marks Entry
      │      └── Enter / Save Marks
      │
      ├── Grades
      │      ├── Calculate Grades
      │      ├── Save
      │      └── Submit
      │
      │             ▼
      │       Validate 100%
      │             │
      │             ▼
      │       Final Grade Submission
      │             │
      │             ▼
      │       Calculate CO Attainment
      │             │
      │             ▼
      │       Calculate PO Attainment
      │             │
      │             ▼
      └──────► Analytics
              ├── Assessment Analytics
              ├── Grade Analytics
              ├── CO Analytics
              └── PO Analytics
```

# 34. Design Principle

The Faculty module should follow a simple principle:

> **Faculty manage the delivery of their current courses, submit required evidence, enter assessment results, and analyze attainment. Official academic structures and historical records remain controlled and auditable.**

This keeps the faculty interface focused while ensuring that the underlying OBE data remains structured enough to support **course files, CQI, CO/PO attainment, accreditation, and program-level analytics**.
