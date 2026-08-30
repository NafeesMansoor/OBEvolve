# Development TODO

Living checklist for in-progress work. Update this as work completes or scope changes — don't
let it drift from reality. See `docs/Faculty_Module_Spec_UI.md` for the full spec this tracks
against, and `design-system/obevolve/MASTER.md` for the visual-redesign checklist.

## Faculty Module (in progress since 2026-08-30)

### Done — backend
- [x] Models: `CourseFileType`/`CourseFileRequirement`/`CourseFileSubmission`, `CourseChangeRequest`,
      `GradeSubmission`, `AttainmentSnapshot`, `AssessmentQuestionProgramOutcomeMapping`
- [x] New columns: `Assessment.purpose`, `Question.kpa`/`is_globally_shared`,
      `Course.delivery_format`, `FacultyAssignment.{office_location,consultation_hours,meeting_link}`,
      `AssessmentType.requires_oep_validation`
- [x] Migrations for all of the above, applied to `tenant_demo` and `tenant_ulab-cse`
- [x] `app/services/faculty_scope.py` — "own sections only" scoping, applied across
      `assessment.py`, `academic_ops.py`, `marks.py`
- [x] New permission codes (`course_file.*`, `course_change_request.*`) + role grants
- [x] Routers: `course_files.py`, `course_change_requests.py`, grade-sheet/submit in `marks.py`
- [x] CEP/OEP finalize-time validation guards in `advance_assessment`
- [x] `GET /academic/students/search` — scoped student-directory lookup for the enrollment flow
- [x] Integration test for the scoping layer (`tests/integration/test_faculty_scope.py`)

### Done — frontend
- [x] Faculty Dashboard panel (current/previous courses, action-required)
- [x] Course Management shell (`/courses/:sectionId`) — Overview, Course Settings, Course Files,
      Students, Assessments, Marks Entry, Grades, Analytics tabs
- [x] Question Bank page
- [x] Nav: "Courses"/"Question Bank" added; "Academic Operations" hidden from Faculty
- [x] Live-verified via Playwright against real data (login, all 8 tabs, assessment create round-trip)

### Fixed 2026-08-31 — real access-control bug found in manual testing

A Program Coordinator (program-wide `section.manage`, no personal `FacultyAssignment` on the
section) could enter marks/create assessments/submit final grades/upload course files for a
section they don't teach, because those endpoints used `ensure_section_access` (which
`is_section_authority` bypasses for `section.manage` holders — correct for genuinely
administrative actions, wrong for "I personally delivered this"). Found live: a Program
Coordinator account updated CS150 marks despite no assignment to it.

- [x] New `ensure_assigned_to_section` (no authority bypass at all) in `app/services/
      faculty_scope.py`, applied to: `create_assessment`/`update_assessment`/`delete_assessment`/
      `create_assessment_question` (not `advance_assessment` — that's a reviewer action),
      `bulk_upsert_student_marks`/`update_student_mark`/`delete_student_mark`/
      `submit_section_grades`, `upload_course_file`, `create_course_change_request`
- [x] Regression test added (`test_program_coordinator_cannot_enter_marks_for_a_section_they_do_not_teach`)
      and re-verified directly against the real Carol/CS150 data from the bug report
- [x] Frontend `useMyCourses` had the same class of bug: `/academic/faculty-assignments` without
      a `faculty_user_id` filter returns every assignment in the program for an authority-holder,
      so "Current Courses" on the Dashboard was showing sections the signed-in user didn't
      actually teach. Fixed by always passing `faculty_user_id: user.id` explicitly.

### Fixed 2026-08-31 — design/UX pass (per direct feedback)

- [x] Logo: "OBE" was nearly invisible on light backgrounds — `-webkit-text-stroke` was too thin
      (0.06em → 0.16em) to read at small sizes on a white card
- [x] Favicon/icon: was still the old (pre-rebrand) asset — regenerated as a clean vector-quality
      SVG + PNG fallbacks matching the current red mark; deleted the orphaned old `favicon.svg`.
      **If it still looks old after this, it's very likely browser favicon caching — hard
      refresh / clear site data / try an incognito window.**
- [x] Dark theme: neutrals were rotated to the same warm ~15° hue as light mode, which reads
      muddy/brownish at dark-mode's low lightness — corrected to true 0%-saturation neutral,
      matching real dark-mode-red-accent precedent (keep the surface neutral, let one accent
      color carry the brand hue)
- [x] Dashboard: reordered so a personalized Overview (current/previous course counts, students
      taught) leads, per spec §30's Dashboard nav order — was previously below Action Required
      with no summary at all
- [x] Dashboard: Action Required no longer duplicates each affected course as a full card under
      its own heading (unbounded clutter with several incomplete sections) — now a compact row
      list, with the same signal as a small badge on the course's own Current Courses card
      (one shared batched fetch, not duplicate requests)
- [x] Dashboard: removed the redundant generic institution-wide "Overview" stat row that used to
      render below the Faculty panel for anyone who teaches — it duplicated the new personalized
      one with less relevant numbers
- [x] Nav: "Course Level Settings"/"Program Level Setting"/"Grading"/"Assessment"/"Analytics" were
      gated on `*.view`-tier permissions Faculty legitimately holds for internal use (CO-mapping
      dropdowns, grading-policy resolution, etc.), which leaked those institution-wide admin pages
      into the Faculty nav — spec §30 says Faculty's nav is Dashboard/Courses/Question Bank only.
      Re-gated on manage/approve/create-authority tiers (`outcome.create`/`outcome.approve`,
      `grading.manage`, `assessment.approve`) instead — verified end-to-end with a real
      single-role Faculty account, nav now shows exactly Dashboard/Courses/Question Bank/About.
      `DashboardPage`'s `QUICK_LINKS` had the identical stale gating — fixed in lockstep.

### Not done yet
- [ ] Admin UI to configure `CourseFileRequirement` rows (course-wise/holistic) + "import from
      previous term" — backend endpoints exist (`/course-files/requirements*`), no frontend form
- [ ] Admin UI to edit the new `CourseVersion` syllabus fields (objectives/TLA items/learning
      materials/target assessment weights) and per-`CourseOutcome` delivery-methods/
      assessment-tools — backend supports it (`PATCH /curriculum/course-versions/{id}`,
      `PATCH /curriculum/course-outcomes/{id}`), currently only seeded directly via script (see
      CSE2301 in `tenant_ulab-cse`) or editable via raw API call; needs a real form
- [ ] "Import course settings from previous semester" (parallel to the existing course-files
      "import previous term" backend capability, but for the new syllabus-content fields) —
      not designed or built
- [ ] Question Bank → "reuse into this assessment" is only wired inline in the Assessments tab's
      add-task form for brand-new questions; no dedicated "browse bank, insert into assessment" flow
- [ ] Course Files: no version-history view (only current version + status shown)
- [ ] Pre-existing, found while verifying this round (not caused by it — both endpoints predate
      this round, from the "structural-gap features" commit): `GET /notifications/pending-approvals`
      and `GET /search` intermittently 400 on first load (looks like a `get_program_context`
      race — X-Program-Code header not yet resolved when the very first background poll fires).
      Also a recurring React "duplicate key `e4fa2101-...`" console warning from some
      always-mounted component (bell/search), not yet isolated to a specific file.

### Fixed 2026-08-30 — Faculty Course Settings content restoration, per-course CO-PO/CEP
guidance, cross-course Analytics, BR-01 enforcement (direct user feedback: "you have removed
some of the important components of the OBE platform for the faculty members")

- [x] `CourseSettingsTab` rebuilt to actually show real course-outline content instead of just
      the change-request form: description, objectives, Course Outcomes (with per-CO delivery
      methods/assessment tools), CO-PO mapping (only shown when the course's own COs have at
      least one recorded mapping — data-driven "dominant course" detection, no new boolean
      column), TLA items, learning materials, this section's live recorded assessment weights,
      and the resolved grading policy/bands. New nullable columns: `CourseVersion.
      {objectives,tla_items,learning_materials,target_assessment_weights}`,
      `CourseOutcome.{delivery_methods,assessment_tools}` (tenant migration 0018) — populated for
      real on CSE2301 (`tenant_ulab-cse`) from the course outline the user shared, everything
      else stays empty until an admin fills it in via the new `PATCH /curriculum/course-versions/
      {id}` endpoint (mirrors the existing `PATCH .../course-outcomes/{id}` pattern exactly).
- [x] Course Coordinators (`course_change_request.review`) can now Approve/Reject pending change
      requests directly from the same Course Settings card, not just create them — closes the
      loop the user asked for ("any changes here needs to be moderated or approved by the course
      coordinator").
- [x] CEP guidance: a read-only reference panel of the accreditation framework's Problem
      Attributes (WP1-WP7) now shows inside the CEP task-authoring dialog in the Assessments tab
      — reuses the existing `GET /curriculum/frameworks/{id}/problem-attributes` endpoint,
      no new backend surface.
- [x] New faculty-scoped Analytics: "My Courses" tab on the (now Faculty-visible) `/analytics`
      page — `FacultyAnalyticsPanel`, filterable by term/course, aggregating grade distribution,
      CO attainment, and PO attainment (filtered to POs reachable from the faculty's own courses)
      across every current+previous section they teach, in one place. Hand-rolled SVG/CSS bars,
      no new chart dependency. The institution-wide "Course Attainment" tab stays hidden for a
      Faculty-only viewer (would otherwise leak every section in the program).
- [x] BR-01 ("Faculty editing capabilities apply only to courses in the current active semester")
      now has a real backend guard: `ensure_current_term` in `app/services/faculty_scope.py`,
      called from inside `ensure_assigned_to_section` — every write path that already used that
      function (marks, grades, assessment authoring, course-file upload, change-request creation)
      now also 403s once the section's `AcademicTerm.is_active` is false. Frontend mirrors this
      by hiding/disabling the corresponding write actions (Save marks, Submit Final Grades,
      Upload, New assessment/task, Request modification) for a previous-term `MyCourseCard`.
      Regression test: `test_faculty_cannot_write_to_a_previous_semester_section`.
- [x] `LogoMark` (collapsed-sidebar icon) changed from a single "O" to "Ov", echoing the
      wordmark's OBE/volve split more distinctly.
- [x] `docs/CODECORTEX_BUG_REPORT.md` — standalone writeup of the two CodeCortex bugs found
      earlier this session, for handoff to whoever maintains that tool.

## Housekeeping

- [x] Version bumped to 1.0.2 (frontend `package.json`, `src/lib/version.ts`,
      backend `app/core/config.py: app_version`) — 2026-08-30
- [ ] Re-check `docs/CREDENTIALS.local.md` passwords are still valid before next test pass
- [x] Reset 3 more local test passwords while investigating the access-control bug — see
      `docs/CREDENTIALS.local.md` (never committed)
