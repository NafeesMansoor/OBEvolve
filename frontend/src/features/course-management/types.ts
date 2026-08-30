/** Grades tab (Faculty Module spec §21-24) — mirrors backend
 * app/schemas/grades.py. */

export interface AssessmentContribution {
  assessment_id: string
  title: string
  weight: string | null
  marks_obtained: string
  max_marks: string
  weighted_percent: string | null
}

export interface GradeSheetRow {
  student_enrollment_id: string
  student_user_id: string
  student_name: string
  enrollment_status: string
  assessments: AssessmentContribution[]
  overall_percent: string | null
  letter_grade: string | null
  grade_point: string | null
}

export interface GradeSheetReport {
  course_section_id: string
  rows: GradeSheetRow[]
  weight_recorded_percent: string
  weight_complete: boolean
  marks_complete: boolean
  incomplete_assessment_titles: string[]
  submission_status: 'draft' | 'submitted'
  submitted_at: string | null
  submitted_by: string | null
}

export interface GradeSubmission {
  id: string
  course_section_id: string
  status: 'draft' | 'submitted'
  submitted_by: string | null
  submitted_at: string | null
}

/** A joined, dashboard-friendly view of one course a faculty member
 * teaches — assembled client-side from `/academic/sections` +
 * `/academic/course-offerings` + `/curriculum/course-versions` +
 * `/curriculum/courses` + `/org/academic-terms`, since no single backend
 * endpoint returns this shape. */
export interface MyCourseCard {
  course_section_id: string
  course_offering_id: string
  course_version_id: string
  program_version_id: string | null
  course_code: string
  course_title: string
  section_code: string
  credits: string
  academic_term_id: string
  term_name: string
  is_current_term: boolean
  enrolled_count: number
  role: 'coordinator' | 'instructor'
}
