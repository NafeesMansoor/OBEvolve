# OBEvolve UI Redesign: Use This Dribbble Design as the Visual Benchmark

Redesign the **OBEvolve** frontend to achieve the same level of visual polish, clarity, spacing, hierarchy, and modern SaaS feel as this reference design:

https://dribbble.com/shots/27685852-AI-Shopping-Agent-Analytics-Dashboard

Use the reference as **visual and UX inspiration**, not something to copy literally.

The reference has the qualities I want for OBEvolve:

* premium SaaS appearance
* clean light interface
* sophisticated purple/lavender accent system
* excellent whitespace
* compact but highly usable sidebar
* strong typography hierarchy
* rounded but not excessively rounded components
* elegant analytics cards
* polished charts
* subtle borders and shadows
* clear data hierarchy
* minimal visual noise
* highly professional dashboard composition

OBEvolve should feel like a **modern AI-powered OBE analytics platform**, not a conventional university ERP.

---

## 1. Overall Visual Direction

Adopt the visual philosophy of the reference:

**Clean + Intelligent + Analytical + Premium + Calm**

Use a predominantly light interface.

Suggested visual direction:

* off-white / very light gray application background
* white content surfaces
* deep charcoal text
* muted gray secondary text
* sophisticated purple as the primary accent
* lavender as a supporting accent
* green for achieved/healthy
* amber for attention
* red for below-target
* subtle borders
* extremely subtle shadows

Do not make everything purple.

Purple should act as the brand/accent color, while the majority of the interface remains neutral.

The reference uses colors around:

* #F8F7FB
* #C3B6F9
* #AB98FF
* #452AFF
* #674CFF

You may adapt these into a coherent OBEvolve design system rather than copying them blindly.

---

# 2. Application Shell

Create a polished application shell inspired by the reference.

### Left Sidebar

Use a clean vertical sidebar with:

**OBEvolve logo / wordmark**

Then grouped navigation:

### Overview

* Dashboard

### OBE Framework

* PEOs
* POs
* KPAs / Indicators
* Courses
* Course Outcomes

### Mapping

* CO → PO
* Course → PO
* Curriculum Mapping

### Assessment

* Assessments
* CO Attainment
* Student Attainment

### Analytics

* Program Analytics
* PO Analytics
* CO Analytics
* Course Analytics
* Trends

### Improvement

* Issues & Deficiencies
* Action Plans
* Improvement Tracking

### Reports

* OBE Reports
* Accreditation
* Export

### Administration

* Users
* Settings

The exact navigation must be based on the existing OBEvolve functionality after inspecting the application.

Do not invent modules that don't exist.

---

# 3. Dashboard Must Be the Hero Screen

The OBEvolve dashboard should take strong inspiration from the composition of the reference dashboard.

Do not simply create:

"Total Courses | Total POs | Total COs | Total Students"

Instead, create an **OBE Intelligence Dashboard**.

The dashboard should immediately answer:

### How healthy is the program?

### Which outcomes are performing well?

### Which outcomes require attention?

### Which courses are contributing to problems?

### What improvement actions are pending?

---

# 4. Dashboard Layout

Use a layout similar in spirit to the reference.

### Top Header

Left:

**Good morning, [Name]**

Small contextual text:

**Here's your program's OBE performance overview.**

Right:

* academic year/semester selector
* notification
* profile

---

### KPI Row

Use elegant compact metric cards.

For example:

**Program Attainment**

84.6%

↑ 4.2% vs previous cycle

---

**POs Achieved**

8 / 10

80%

---

**Courses Reviewed**

42 / 48

87.5%

---

**Improvement Actions**

7

3 require attention

---

Do not make these cards oversized.

They should feel like the compact analytical cards in the reference design.

---

# 5. Main Analytics Area

Create a large primary visualization.

### Program Attainment Trend

Display attainment over multiple assessment cycles/semesters.

Example:

Fall 2024 → Spring 2025 → Fall 2025 → Spring 2026

Show:

* actual attainment
* target threshold
* improvement trend

The chart should visually communicate whether the program is improving.

---

# 6. PO Performance

Create an elegant analytical card showing all POs.

Example:

PO1
████████████ 92%

PO2
███████████ 84%

PO3
████████ 76%

PO4
██████████ 81%

PO5
███████████ 88%

Use subtle color states:

Green = achieved

Amber = near threshold

Red = below threshold

Allow the user to click a PO to drill down.

---

# 7. "Needs Attention" Section

This should be one of the most useful sections of the dashboard.

Example:

### Needs Attention

| Course  | Outcome | Attainment | Target | Status       |
| ------- | ------- | ---------: | -----: | ------------ |
| CSE 301 | CO3     |        61% |    70% | Below Target |
| CSE 405 | CO2     |        65% |    70% | Below Target |
| CSE 412 | CO4     |        68% |    70% | Attention    |

Each row should have a clear action:

**Review →**

The dashboard should move the user directly from analytics to action.

---

# 8. Continuous Improvement

Add a visually elegant section:

### Continuous Improvement

Show four stages:

**Identified**

12

↓

**Under Review**

5

↓

**Action Planned**

4

↓

**Implemented**

8

This communicates that OBEvolve is not merely an attainment-reporting system.

It is a **continuous improvement platform**.

---

# 9. OBE Framework Visualization

Create a polished visual representation of the OBE hierarchy.

For example:

PEOs

↓

POs

↓

KPAs / Indicators

↓

Courses

↓

COs

↓

Assessments

↓

Attainment

↓

Continuous Improvement

Make this visually elegant and interactive.

Users should be able to click through the hierarchy.

---

# 10. Mapping UI

The mapping interfaces should follow the same visual language.

Avoid old-fashioned spreadsheet-style interfaces.

Create modern matrix components with:

* fixed headers
* subtle row separation
* compact cells
* hover states
* clear mapping strength
* inline editing
* tooltips
* filtering
* search

Example:

| Course  | PO1 | PO2 | PO3 | PO4 |
| ------- | --: | --: | --: | --: |
| CSE 301 |   3 |   2 |   — |   1 |
| CSE 302 |   2 |   3 |   2 |   — |

Use elegant visual indicators for mapping strength.

---

# 11. Attainment Detail Page

Make attainment pages exceptionally polished.

At the top:

### CO3 Attainment

**61.4%**

Target: **70%**

🔴 Below Target

Then immediately explain:

**Why?**

Show contributing assessments.

Example:

Quiz 1 → 68%

Midterm → 57%

Assignment → 73%

Final → 59%

Then:

### Recommended Action

"CO3 is below the defined attainment threshold."

[Create Improvement Action]

This is the type of intelligent workflow the UI should encourage.

---

# 12. Course Detail Page

Design a premium course analytics page.

Header:

**CSE 301 — Database Systems**

Course Teacher
Semester
Credits

Then:

### Course Health

CO1  ✓ 82%

CO2  ✓ 76%

CO3  ! 61%

CO4  ✓ 88%

Then:

### CO → PO Mapping

### Assessment Performance

### Student Attainment

### Improvement Actions

Everything should be accessible without overwhelming the user.

---

# 13. Cards

Follow the reference's philosophy.

Cards should:

* have subtle borders
* use restrained corner radius
* have generous but not excessive padding
* have clear hierarchy
* contain meaningful information
* avoid unnecessary decoration

Do NOT turn every piece of information into a card.

Use cards to establish grouping and hierarchy.

---

# 14. Charts

Charts should feel like premium analytics software.

Use:

* smooth line charts
* clean bar charts
* compact progress visualizations
* threshold markers
* meaningful tooltips
* subtle gridlines
* clear labels

Avoid:

* 3D charts
* excessive colors
* unnecessary legends
* chart junk
* decorative visualizations

Every visualization should answer a specific OBE question.

---

# 15. Tables

Tables should feel modern and lightweight.

Use:

* white surfaces
* subtle separators
* compact rows
* strong typography hierarchy
* hover states
* status badges
* contextual actions

Avoid heavy borders around every cell.

---

# 16. Status Design

Create a consistent status system.

### Achieved

Green indicator

**84% · Achieved**

### Near Target

Amber indicator

**68% · Attention**

### Below Target

Red indicator

**54% · Action Required**

### Not Evaluated

Neutral gray

**Not Available**

Use both icon/text and color so the meaning is never dependent on color alone.

---

# 17. Empty States

Follow the same polished aesthetic.

Instead of:

"No data."

Use:

### No attainment data yet

Assessment results have not been submitted for this course.

[Go to Assessments]

Make empty states useful and actionable.

---

# 18. Interactions

Use subtle interactions inspired by premium SaaS products:

* smooth hover states
* soft transitions
* expandable analytics
* animated progress indicators
* contextual tooltips
* dropdown transitions
* skeleton loading
* toast confirmations

Do not over-animate.

The interface should feel fast and calm.

---

# 19. Typography

Use a modern UI font.

Create a strong hierarchy:

Large:

**Program Attainment**

Medium:

**PO Performance**

Small:

**Compared with previous cycle**

Numbers should have strong visual emphasis.

Use muted text for secondary information.

---

# 20. Responsive Behavior

The desktop version should closely resemble the quality of the reference.

Also support:

* laptop
* tablet
* smaller screens

The sidebar should collapse elegantly.

Charts should resize intelligently.

Tables should have a deliberate responsive behavior.

---

# 21. UX Principle

Adopt this principle throughout OBEvolve:

> **Analytics should lead naturally to action.**

For example:

**PO3 is below target**

↓

**Identify contributing courses**

↓

**Identify weak COs**

↓

**Inspect assessments**

↓

**Create improvement action**

↓

**Track implementation**

↓

**Measure again**

The UI should make this journey obvious.

---

# 22. Do Not Copy the Reference Literally

Important:

Do NOT reproduce the Dribbble design pixel-for-pixel.

Do NOT copy its content, illustrations, branding, or proprietary design elements.

Instead, extract its design principles:

* spacing
* composition
* visual hierarchy
* card design
* typography
* analytics presentation
* color discipline
* navigation structure
* overall polish

Then create a distinct **OBEvolve identity**.

---

# 23. Before Coding

First inspect the existing OBEvolve implementation.

Understand:

* current routes
* components
* pages
* APIs
* database
* authentication
* user roles
* existing design system
* actual OBE workflows

Then produce a concise UI audit identifying:

1. Current problem
2. Proposed improvement
3. Reference-inspired design pattern
4. Components affected

Only after that should implementation begin.

Do not break existing functionality.

Do not replace working backend functionality merely for visual reasons.

Do not use fake/mock data to make screenshots look impressive.

Use the real application data.

---

# 24. Final Acceptance Criteria

The redesigned OBEvolve should pass this test:

When someone opens the dashboard, they should immediately understand:

**Program health → Outcome performance → Problems → Required actions**

When someone opens a course:

**Course performance → CO performance → PO contribution → Assessment evidence → Improvement**

When someone opens an attainment result:

**Actual → Target → Gap → Cause → Action**

The application should feel like a **premium AI-enabled OBE analytics and continuous-improvement platform**.

The benchmark for visual quality is the referenced Dribbble design.

The benchmark for functionality is the actual OBEvolve application.

The final result must combine both.
