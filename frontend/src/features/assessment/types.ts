export interface AssessmentType {
  id: string
  name: string
  is_custom: boolean
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
  created_at: string
  updated_at: string
}

export interface QuestionCourseOutcomeMapping {
  id: string
  question_id: string
  course_outcome_id: string
}

export interface QuestionBloomMapping {
  id: string
  question_id: string
  bloom_level_id: string
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
  status: string
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
