export interface GradingPolicy {
  id: string
  name: string
  program_version_id: string | null
  is_default: boolean
  description: string | null
  created_at: string
  updated_at: string
}

export interface GradingBand {
  id: string
  grading_policy_id: string
  letter_grade: string
  min_percentage: string
  max_percentage: string
  grade_point: string | null
  sequence: number
  created_at: string
  updated_at: string
}
