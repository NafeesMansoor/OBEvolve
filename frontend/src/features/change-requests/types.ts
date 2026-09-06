export type SectionKey = 'overview' | 'settings' | 'students' | 'assessments'

export type ChangeRequestTargetField =
  | 'description'
  | 'objectives'
  | 'outcomes'
  | 'tla_mapping'
  | 'learning_materials'
  | 'weights'
  | 'grading_policy'
  | 'enrollment_add'
  | 'enrollment_drop'
  | 'enrollment_status'
  | 'assessment_details'

export type ChangeRequestStatus =
  | 'draft'
  | 'pending_admin'
  | 'pending_program_coordinator'
  | 'approved'
  | 'rejected'
  | 'returned'

export interface CourseChangeRequest {
  id: string
  course_section_id: string
  section_key: SectionKey
  target_field: ChangeRequestTargetField
  current_value_json: Record<string, unknown> | null
  proposed_value_json: Record<string, unknown>
  edited_value_json: Record<string, unknown> | null
  reason: string
  status: ChangeRequestStatus
  requested_by: string
  reviewed_by: string | null
  review_note: string | null
  reviewed_at: string | null
  program_coordinator_reviewed_by: string | null
  program_coordinator_review_note: string | null
  program_coordinator_reviewed_at: string | null
  edited_by: string | null
  edited_at: string | null
  apply_status: string | null
  apply_error: string | null
  created_at: string
  updated_at: string
}

export const TARGET_FIELD_LABELS: Record<ChangeRequestTargetField, string> = {
  description: 'Course Description',
  objectives: 'Course Objectives',
  outcomes: 'Course Outcomes',
  tla_mapping: 'TLA & Assessment Mapping',
  learning_materials: 'Learning Materials',
  weights: 'Assessment & Weights',
  grading_policy: 'Grading Policy',
  enrollment_add: 'Add Student',
  enrollment_drop: 'Drop Student',
  enrollment_status: 'Enrollment Status',
  assessment_details: 'Assessment Details',
}

export const STATUS_LABELS: Record<ChangeRequestStatus, string> = {
  draft: 'Draft',
  pending_admin: 'Pending Course Administrator',
  pending_program_coordinator: 'Pending Program Coordinator',
  approved: 'Approved',
  rejected: 'Rejected',
  returned: 'Returned for Revision',
}

/** Fields `OverviewTab` lets a Course Teacher propose a change to —
 * single-stage approval (spec §5.A: Course Teacher -> Course Administrator
 * -> final). Deliberately excludes everything `SETTINGS_TARGET_FIELDS`
 * covers, so a field is only ever proposable under one section_key/tier —
 * both tabs pick from disjoint field lists rather than letting a caller
 * choose whichever tier is more convenient for the same field. */
export const OVERVIEW_TARGET_FIELDS: ChangeRequestTargetField[] = ['description', 'objectives']

/** Which fields (within the "settings" section) `CourseSettingsTab` lets a
 * Course Teacher propose a change to — two-stage approval (spec §5.C). */
export const SETTINGS_TARGET_FIELDS: ChangeRequestTargetField[] = [
  'outcomes',
  'tla_mapping',
  'learning_materials',
  'weights',
  'grading_policy',
]
