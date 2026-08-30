export type ChangeRequestTargetField =
  | 'description'
  | 'outcomes'
  | 'tla_mapping'
  | 'learning_materials'
  | 'weights'
  | 'grading_policy'

export type ChangeRequestStatus = 'pending' | 'approved' | 'rejected'

export interface CourseChangeRequest {
  id: string
  course_section_id: string
  target_field: ChangeRequestTargetField
  current_value_json: Record<string, unknown> | null
  proposed_value_json: Record<string, unknown>
  reason: string
  status: ChangeRequestStatus
  requested_by: string
  reviewed_by: string | null
  review_note: string | null
  reviewed_at: string | null
  created_at: string
  updated_at: string
}

export const TARGET_FIELD_LABELS: Record<ChangeRequestTargetField, string> = {
  description: 'Course Description',
  outcomes: 'Course Outcomes',
  tla_mapping: 'TLA & Assessment Mapping',
  learning_materials: 'Learning Materials',
  weights: 'Assessment & Weights',
  grading_policy: 'Grading Policy',
}
