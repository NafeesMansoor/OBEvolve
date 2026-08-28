export const PROPOSED_ACTIONS = [
  { value: 'new_assessment', label: 'Introduce a new assessment' },
  { value: 'revise_assessment', label: 'Revise an existing assessment' },
  { value: 'change_assessment_type', label: 'Change assessment type' },
  { value: 'adjust_co_marks', label: 'Increase/decrease marks allocated to a CO' },
  { value: 'revise_co_wording', label: 'Revise CO wording' },
  { value: 'new_co', label: 'Introduce a new CO' },
  { value: 'remove_restructure_co', label: 'Remove/restructure a CO' },
  { value: 'new_topic', label: 'Introduce a new topic' },
  { value: 'revise_topics', label: 'Revise existing topics' },
  { value: 'change_teaching_methodology', label: 'Change teaching methodology' },
  { value: 'change_marks_distribution', label: 'Change marks distribution' },
  { value: 'change_assessment_distribution', label: 'Change assessment distribution' },
  { value: 'additional_materials', label: 'Provide additional learning materials' },
  { value: 'remedial_activities', label: 'Add remedial activities' },
  { value: 'revise_content', label: 'Revise course content' },
  { value: 'other', label: 'Other' },
] as const

export interface ImprovementPlan {
  id: string
  course_section_id: string
  course_outcome_id: string
  problem_observation: string
  proposed_action: string
  proposed_action_detail: string | null
  reason: string
  expected_improvement: string
  implementation_term_id: string | null
  responsible_user_id: string | null
  status: 'proposed' | 'approved' | 'rejected' | 'implemented'
  evidence: string | null
  created_by: string | null
  reviewed_by: string | null
  reviewed_at: string | null
  created_at: string
  updated_at: string
}
