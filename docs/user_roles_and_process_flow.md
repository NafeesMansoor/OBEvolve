Below is a structured prompt you can give to Claude or another coding agent to design the system around the workflow you described.

# Prompt: Design and Implement the Academic Outcome-Based Education (OBE) Management System

You are an expert **software architect, OBE/accreditation-system designer, and full-stack developer**. I want you to design and implement an OBE management system for an undergraduate academic program.

The system should support the complete workflow from **program-level outcome configuration → course delivery → assessment → CO attainment → PO attainment → analytics → improvement action**.

Do not make assumptions about the workflow. First understand and model the roles, entities, relationships, permissions, calculations, and workflow described below.

---

## 1. Core Concept

The system follows an **Outcome-Based Education (OBE)** model.

The hierarchy is:

**Program → PEO → PO → Course → CO → Assessment → Student Marks → CO Attainment → PO Attainment → Analytics → Continuous Improvement**

The system must maintain a clear distinction between:

* Program-level configuration
* Course-level configuration
* Section/semester-level operation
* Student-level attainment
* Program-level analytics
* Continuous improvement actions

The architecture should allow the rules and thresholds to be changed by the program administrator without requiring code changes.

---

# 2. User Roles

The system should have at least the following roles.

## A. Program Administrator

Responsible for maintaining the program's OBE framework.

Can:

* Create, edit, activate/deactivate PEOs
* Create, edit, activate/deactivate POs
* Define PO descriptions and metadata
* Create and maintain COs where appropriate at the program/course framework level
* Maintain **PO-CO mappings**
* Define attainment calculation settings
* Define thresholds and rules
* Configure treatment of W and I grades
* Configure cohort definitions
* View program-level analytics
* View PO attainment by:

  * PO
  * Cohort
  * Semester
  * Course
  * Section
* Review course-level attainment
* Review improvement/action plans
* Monitor continuous improvement

The administrator should be able to configure rules such as:

### Individual Student CO Attainment

Example:

> If a student obtains at least **X% of the marks associated with a CO**, that student is considered to have attained the CO.

Example:

CO1 has 20 marks associated with it.

If the configured threshold is 50%, then:

20 × 50% = 10

A student obtaining 10 or more marks for CO1 is considered to have attained CO1.

The X% must be configurable.

---

# 3. Course-Level CO Attainment

For each course/section:

> If at least **Y% of eligible students attain a particular CO**, the CO is considered attained at course level.

Example:

* 40 eligible students
* 60% required CO attainment
* At least 24 students must attain the CO

If fewer than the required percentage attain the CO, the CO is considered **Not Attained**.

The Y% threshold must be configurable.

---

# 4. W and I Grade Treatment

The system must allow the program administrator to configure how students with:

* W = Withdrawn
* I = Incomplete

are treated in attainment calculations.

Possible configurations:

1. Exclude W and I students completely
2. Include W and I students
3. Partially include them according to a configurable rule

Do not hard-code this behavior.

The calculation engine should use the configured rule.

The system should clearly show which students were included/excluded from each calculation and why.

---

# 5. CO Failure / Continuous Improvement Workflow

If a course-level CO does not meet the configured attainment threshold:

**CO Attainment = Not Attained**

the system should automatically flag the CO for review.

The course teacher/coordinator should then be asked to submit an **Improvement / Action Plan**.

The system should allow the teacher to propose one or more interventions, such as:

* Introduce a new assessment
* Revise an existing assessment
* Change assessment type
* Increase/decrease marks allocated to a CO
* Revise CO wording
* Introduce a new CO
* Remove/restructure a CO
* Introduce a new topic
* Revise existing topics
* Change teaching methodology
* Change marks distribution
* Change assessment distribution
* Provide additional learning materials
* Add remedial activities
* Revise course content
* Other, with explanation

The teacher should provide:

* Problem/observation
* Proposed action
* Reason for action
* Expected improvement
* Implementation semester
* Responsible person
* Status
* Evidence, if applicable

The system should maintain the history of these actions for accreditation and continuous improvement purposes.

---

# 6. Program Coordinator

The Program Coordinator manages semester-level course offerings.

For each semester, the coordinator can:

* Create/open a semester
* Define course offerings
* Offer courses
* Create sections
* Assign faculty to sections
* Designate course coordinator
* View section/course status
* Monitor assessment and attainment submission
* View course-level OBE performance

Example:

Semester: Fall 2026

Course:

CSE 3201 – Database Systems

Sections:

* 1
* 2
* 3

Each section may have one or more faculty members.

The system must support the distinction between:

**Course → Course Offering → Section → Faculty**

---

# 7. Course Coordinator

The Course Coordinator manages course-level OBE information in collaboration with course faculty.

The Course Coordinator should be able to:

* Maintain course information
* Define/revise Course Outcomes (COs), subject to appropriate approval
* Map COs to POs
* Define CO-related topics
* Define assessment structure
* Map assessment components/questions to COs
* Define marks distribution
* Review faculty-submitted marks
* Review CO attainment
* Review PO contribution
* Submit improvement plans
* Monitor course-level attainment across sections where applicable

The system should distinguish between:

**Approved program-level configuration**

and

**course-level operational configuration**.

Changes that require approval should have an approval workflow rather than immediately changing the approved framework.

---

# 8. Course Faculty

Course faculty are responsible for operational academic activities.

They can:

* View assigned courses/sections
* View approved COs
* View PO-CO mappings
* Define/maintain assessment components where permitted
* Enter/upload student marks
* Associate marks/questions with COs
* Submit marks
* View student-level CO attainment
* View section-level CO attainment
* View relevant PO attainment
* Submit improvement/action plans when required

The system should support multiple assessment components, for example:

* Quiz
* Assignment
* Midterm
* Final
* Lab
* Project
* Presentation
* Viva
* Participation
* Other

The number and type of assessments should be configurable.

---

# 9. Assessment and Marks

For every assessment, the system should maintain:

* Assessment ID
* Assessment name
* Assessment type
* Maximum marks
* Date
* CO mapping
* Question-level CO mapping where applicable
* Student marks
* Submission status

Example:

Midterm = 30 marks

| Question | Marks | CO  |
| -------- | ----: | --- |
| Q1       |     5 | CO1 |
| Q2       |     5 | CO1 |
| Q3       |    10 | CO2 |
| Q4       |    10 | CO3 |

The system should calculate each student's total marks associated with each CO.

---

# 10. Individual Student CO Attainment

For every student in every course section:

Calculate:

**CO Score = Marks obtained for the CO / Maximum marks associated with the CO × 100**

Compare the result against the configured individual CO attainment threshold.

Example:

CO1 maximum marks = 20

Student obtains = 14

CO1 percentage:

14 / 20 × 100 = 70%

If threshold = 60%:

**CO1 = Attained**

If threshold = 75%:

**CO1 = Not Attained**

The threshold must come from the attainment settings.

The system should preserve the underlying numerical score as well as the attained/not-attained result.

---

# 11. Course-Level CO Attainment

For each CO:

Calculate:

**CO Attainment % = Number of eligible students who attained the CO / Total eligible students × 100**

Compare it with the configured course-level threshold Y%.

Example:

Eligible students = 40

Students attaining CO1 = 28

CO attainment = 70%

If Y = 60%:

**CO1 = Attained**

If Y = 75%:

**CO1 = Not Attained**

The system should show:

* Total students
* Eligible students
* Excluded students
* Number attained
* Number not attained
* Attainment percentage
* Required threshold
* Final status

---

# 12. PO Attainment

The system must support PO attainment analytics based on the approved **PO-CO mappings**.

A CO may contribute to one or more POs.

The system should maintain configurable mapping strength where required, for example:

* 0 = No
* 1 = Yes


Do not hard-code a particular calculation method unless explicitly configured.

The PO attainment engine should be designed so that the institution can define its preferred PO calculation methodology.

At minimum, the system should be able to generate:

* CO attainment
* PO attainment
* CO-to-PO contribution
* Student-level PO status where applicable
* Course-level PO contribution
* Cohort-level PO attainment
* Program-level PO attainment

---

# 13. Cohort Analytics

A **cohort** represents a particular intake of students.

Example:

* Spring 2025 Cohort
* Fall 2025 Cohort
* Spring 2026 Cohort

The system should maintain student-to-cohort relationships.

PO attainment analytics must be accessible by:

### PO

Example:

PO1:

* Spring 2025: 72%
* Fall 2025: 76%
* Spring 2026: 81%

### Cohort

Example:

Fall 2025 Cohort:

* PO1: 76%
* PO2: 71%
* PO3: 84%

The system should support filtering by:

* PO
* Cohort
* Semester
* Course
* Course section
* Academic year
* Program

Provide both tabular and graphical analytics where appropriate.

---

# 14. Student Dashboard

Students should be able to see their own academic outcome information.

They should be able to view:

### Marks

* Assessment-wise marks
* Total marks
* Course grade

### CO Attainment

For each course:

| CO  | Score | Threshold | Status       |
| --- | ----: | --------: | ------------ |
| CO1 |   72% |       60% | Attained     |
| CO2 |   54% |       60% | Not Attained |

### PO Attainment

Students should be able to see their PO status/attainment based on the approved calculation methodology.

The student should only see their own information.

---

# 15. Program Analytics Dashboard

Create a comprehensive program-level OBE dashboard.

The dashboard should provide:

### PO Performance

* PO-wise attainment
* PO attainment by cohort
* PO attainment by semester
* PO trend over time

### CO Performance

* CO attainment by course
* CO attainment by semester
* CO attainment by cohort
* CO attainment trends

### Course Performance

* Courses with strong attainment
* Courses with weak attainment
* COs below threshold
* Courses requiring improvement plans

### Continuous Improvement

* Number of failed COs
* Number of improvement plans
* Pending plans
* Implemented plans
* Improvement after intervention

---

# 16. Configuration-Driven Architecture

This is extremely important.

Do NOT hard-code OBE rules.

The following must be configurable:

* CO individual attainment threshold X%
* Course-level CO attainment threshold Y%
* W/I treatment
* PO-CO mapping
* Mapping strength
* PO attainment methodology
* Assessment types
* Grade definitions
* Passing thresholds
* Cohort definitions
* Academic semesters
* Approval requirements

Changing these settings should not require modifying application code.

---

# 17. Audit Trail

Because this system may be used for accreditation, maintain a complete audit trail.

Track:

* Who created a PO
* Who modified a PO
* Who changed a CO
* Who changed PO-CO mapping
* Who changed attainment settings
* Who entered marks
* Who modified marks
* Who submitted marks
* Who approved marks
* Who submitted improvement plans
* Who approved improvement plans
* When each action occurred
* Previous and new values where appropriate

Do not permanently overwrite important historical OBE data.

---

# 18. Historical Data and Versioning

OBE frameworks may change over time.

Therefore, support versioning for:

* PEOs
* POs
* COs
* PO-CO mappings
* Attainment settings
* Course structures

A change made for a future curriculum should not alter historical attainment calculations.

For example:

If PO definitions change in 2027, attainment calculated for 2025 must continue to use the 2025 configuration.

---

# 19. Workflow

The overall workflow should be:

```text
Program Administrator
        ↓
Define PEOs
        ↓
Define POs
        ↓
Define/approve CO framework
        ↓
Define PO-CO mappings
        ↓
Configure attainment rules
        ↓
Program Coordinator
        ↓
Offer courses
        ↓
Create sections
        ↓
Assign faculty
        ↓
Course Coordinator
        ↓
Maintain course/CO/assessment structure
        ↓
Course Faculty
        ↓
Conduct assessments
        ↓
Enter/submit marks
        ↓
System calculates
        ↓
Individual Student CO Attainment
        ↓
Course-Level CO Attainment
        ↓
PO Attainment
        ↓
Program / Cohort Analytics
        ↓
If CO below threshold
        ↓
Improvement Plan
        ↓
Review / Approval
        ↓
Implementation
        ↓
Next-cycle evaluation
```

---

# 20. Important Design Principle

The system should distinguish between:

**Configuration → Operation → Calculation → Analytics → Improvement**

These should not be mixed together.

For example:

* Program Administrator configures the OBE framework.
* Program Coordinator manages semester offerings.
* Course Coordinator manages course-level OBE structure.
* Faculty manages assessments and marks.
* System calculates attainment.
* Program administrators/coordinators analyze results.
* Teachers propose improvement actions.
* The institution tracks whether those actions improve future attainment.

---

# 21. Required Deliverables

Before writing code, provide:

### A. System Architecture

Describe:

* Frontend
* Backend
* Database
* Authentication/authorization
* Calculation engine
* Analytics engine
* Audit system
* Notification system

### B. Entity Relationship Model

Identify all major entities and relationships.

At minimum consider:

* Program
* PEO
* PO
* Course
* CO
* PO-CO Mapping
* Academic Year
* Semester
* Cohort
* Course Offering
* Section
* Faculty
* Student
* Enrollment
* Assessment
* Assessment Question
* Assessment-CO Mapping
* Student Marks
* CO Attainment
* PO Attainment
* Attainment Configuration
* Improvement Plan
* Approval
* Audit Log

Do not create unnecessary duplication.

### C. Role-Permission Matrix

Clearly define what each role can:

* Create
* Read
* Update
* Delete
* Submit
* Approve
* Analyze

### D. Calculation Engine

Document every calculation with examples.

Make the calculation engine configuration-driven.

### E. Workflow Diagram

Show the complete lifecycle from program configuration to continuous improvement.

### F. Dashboard Design

Design dashboards for:

* Program Administrator
* Program Coordinator
* Course Coordinator
* Faculty
* Student

### G. Database Schema

Provide tables, fields, primary keys, foreign keys, indexes, constraints and relationships.

### H. API Design

Define the major backend APIs required.

### I. Implementation Plan

Break implementation into logical phases.

Do not start coding until the architecture, database model, role model, calculation methodology, and workflow have been reviewed for consistency.

---

# 22. Critical Requirement

The system is intended to support **academic quality assurance and accreditation**.

Therefore prioritize:

1. Accuracy of calculations
2. Traceability
3. Configurability
4. Historical integrity
5. Role-based access
6. Auditability
7. Transparency of attainment calculations
8. Ease of use
9. Reporting and analytics
10. Continuous improvement tracking

Every reported attainment figure should be traceable back to:

**Student → Assessment → Marks → CO → PO → Calculation Rule → Final Attainment**

The user should be able to drill down from a program-level PO result all the way to the underlying student/assessment data.

Before implementation, identify any ambiguities or missing rules in the above workflow and clearly list them as **decisions required**, rather than silently making assumptions.
