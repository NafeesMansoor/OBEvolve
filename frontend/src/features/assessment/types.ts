export interface AssessmentType {
  id: string
  name: string
  is_custom: boolean
  requires_documents: boolean
  requires_cep_documents: boolean
  requires_oep_validation: boolean
}

export interface Rubric {
  id: string
  name: string
  description: string | null
  is_reusable: boolean
  created_at: string
  updated_at: string
}

export interface RubricCriterion {
  id: string
  rubric_id: string
  criterion: string
  weight: string
  created_at: string
  updated_at: string
}

export interface RubricLevel {
  id: string
  rubric_criterion_id: string
  label: string
  score: string
  description: string | null
  created_at: string
  updated_at: string
}

export interface Question {
  id: string
  course_version_id: string
  text: string
  question_type: string
  difficulty: string | null
  marks: string
  topic: string | null
  status: string
  author_id: string | null
  reviewer_id: string | null
  /** K/P/A classification — Complex Engineering Problem tasks only. */
  kpa: 'K' | 'P' | 'A' | null
  /** Question Bank sharing (Faculty Module spec §17) — default false. */
  is_globally_shared: boolean
  created_at: string
  updated_at: string
}

export interface QuestionCourseOutcomeMapping {
  id: string
  question_id: string
  course_outcome_id: string
}

/** CEP task -> Program Outcome mapping, scoped to one AssessmentQuestion
 * (not the shared Question bank row) — spec §18. */
export interface AssessmentQuestionProgramOutcomeMapping {
  id: string
  assessment_question_id: string
  program_outcome_id: string
}

export interface QuestionBloomMapping {
  id: string
  question_id: string
  bloom_level_id: string
}

export interface BloomLevel {
  id: string
  name: string
  sequence_order: number
  is_active: boolean
}

export interface Assessment {
  id: string
  course_section_id: string
  academic_term_id: string
  assessment_type_id: string
  title: string
  max_marks: string
  weight: string | null
  date: string | null
  duration_minutes: number | null
  rubric_id: string | null
  /** Problem statement for a CEP/OEP assessment (spec §18-19) — null for
   * ordinary exam-type assessments. */
  purpose: string | null
  status: string
  document_deadline_extended_to: string | null
  document_deadline_extended_by: string | null
  document_deadline_extended_at: string | null
  created_at: string
  updated_at: string
}

export interface AssessmentQuestion {
  id: string
  assessment_id: string
  question_id: string
  marks_allocated: string
  sequence: number
  created_at: string
  updated_at: string
}

export type AssessmentDocumentType =
  | 'question_paper'
  | 'moderation_form'
  | 'compliance_form'
  | 'script_highest'
  | 'script_lowest'
  | 'script_median'
  | 'problem_definition'
  | 'marked_rubric_sample'
  | 'project_report'
export type AssessmentDocumentStatus = 'pending' | 'approved' | 'rejected'

export interface AssessmentDocument {
  id: string
  assessment_id: string
  document_type: AssessmentDocumentType
  file_name: string
  file_size: number
  content_type: string
  status: AssessmentDocumentStatus
  uploaded_by: string | null
  uploaded_at: string
  reviewed_by: string | null
  reviewed_at: string | null
  review_note: string | null
  created_at: string
  updated_at: string
}

export interface PendingAssessmentDocument {
  document: AssessmentDocument
  assessment_id: string
  assessment_title: string
  course_section_id: string
}

export interface AssessmentWeightSummary {
  course_section_id: string
  assessment_count: number
  weighted_count: number
  total_weight: string
  is_complete: boolean
}

export interface StudentMark {
  id: string
  assessment_question_id: string
  student_enrollment_id: string
  marks_obtained: string
  entered_by: string | null
  entered_at: string
}

export interface CourseAttainmentConfig {
  id: string
  course_version_id: string
  min_marks_percent: string
  min_students_percent: string
  wi_treatment: string
  created_at: string
  updated_at: string
}

export interface CourseOutcomeAttainment {
  course_outcome_id: string
  code: string
  statement: string
  assessed: boolean
  marks_allocated: string | null
  students_attained: number | null
  eligible_students: number | null
  attainment_percent: string | null
  is_attained: boolean | null
}

export interface CourseAttainmentReport {
  course_section_id: string
  course_version_id: string
  min_marks_percent: string
  min_students_percent: string
  total_enrolled: number
  excluded_wi: number
  eligible_students: number
  outcomes: CourseOutcomeAttainment[]
}

export interface ProgramAttainmentConfig {
  id: string
  program_version_id: string
  min_po_attainment_percent: string
  created_at: string
  updated_at: string
}

export interface COContribution {
  course_outcome_id: string
  course_code: string
  co_code: string
  mapping_strength: number
  co_attainment_percent: string | null
}

export interface ProgramOutcomeAttainment {
  program_outcome_id: string
  code: string
  statement: string
  assessed: boolean
  attainment_percent: string | null
  is_attained: boolean | null
  contributions: COContribution[]
}

export interface ProgramAttainmentReport {
  program_version_id: string
  min_po_attainment_percent: string
  batch_year: number | null
  sections_included: number
  outcomes: ProgramOutcomeAttainment[]
}

export interface CourseAttainmentSummary {
  course_version_id: string
  course_code: string
  course_title: string
  cos_assessed: number
  cos_below_threshold: number
  average_co_attainment_percent: string | null
}

export interface ImprovementPlanCounts {
  proposed: number
  approved: number
  rejected: number
  implemented: number
  total: number
}

export interface ProgramAnalyticsSummary {
  program_version_id: string
  batch_year: number | null
  po_outcomes: ProgramOutcomeAttainment[]
  course_summaries: CourseAttainmentSummary[]
  improvement_plan_counts: ImprovementPlanCounts
}

export interface StudentAssessmentMark {
  assessment_id: string
  title: string
  max_marks: string
  obtained: string | null
}

export interface StudentCourseOutcomeStatus {
  course_outcome_id: string
  code: string
  statement: string
  score_percent: string | null
  threshold_percent: string
  attained: boolean | null
}

export interface StudentEnrollmentAttainment {
  course_section_id: string
  course_code: string
  course_title: string
  section_code: string
  academic_term_id: string
  term_name: string
  enrollment_status: string
  assessments: StudentAssessmentMark[]
  total_obtained: string
  total_max: string
  letter_grade: string | null
  grade_point: string | null
  course_outcomes: StudentCourseOutcomeStatus[]
}

export interface StudentProgramOutcomeStatus {
  program_outcome_id: string
  code: string
  statement: string
  contributing_cos_total: number
  contributing_cos_attained: number
  attained: boolean | null
}

export interface StudentAttainmentSummary {
  program_version_id: string
  enrollments: StudentEnrollmentAttainment[]
  po_status: StudentProgramOutcomeStatus[]
}
