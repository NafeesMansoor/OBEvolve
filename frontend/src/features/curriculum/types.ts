export interface AccreditationFramework {
  id: string
  accreditation_body_id: string
  name: string
  version: string
  effective_date: string
  expiry_date: string | null
  description: string | null
  is_active: boolean
}

export interface FrameworkPO {
  id: string
  framework_id: string
  code: string
  statement: string
  sequence: number
  is_active: boolean
}

export interface FrameworkDetail extends AccreditationFramework {
  framework_pos: FrameworkPO[]
}

export interface KnowledgeProfile {
  id: string
  framework_id: string
  code: string
  title: string | null
  description: string
  sequence: number
  is_active: boolean
}

export interface ProblemAttribute {
  id: string
  framework_id: string
  code: string
  title: string | null
  description: string
  sequence: number
  is_active: boolean
}

export interface EngineeringActivity {
  id: string
  framework_id: string
  code: string
  title: string | null
  description: string
  sequence: number
  is_active: boolean
}

export interface Course {
  id: string
  department_id: string
  code: string
  title: string
  description: string | null
  credits: string
  contact_hours: number | null
  course_type: string | null
  delivery_format: 'theory' | 'lab'
  is_active: boolean
  co_offered_with_id: string | null
  created_at: string
  updated_at: string
}

export interface CourseVersion {
  id: string
  course_id: string
  version_label: string
  effective_academic_year_id: string | null
  status: string
  objectives: string | null
  tla_items: string | null
  learning_materials: string | null
  target_assessment_weights: string | null
  created_by: string | null
  approved_by: string | null
  created_at: string
  updated_at: string
}

export interface PEO {
  id: string
  program_version_id: string
  code: string
  statement: string
  description: string | null
  sequence: number
  is_active: boolean
  status: string
  effective_from: string | null
  effective_to: string | null
  created_by: string | null
  approved_by: string | null
}

export interface ProgramOutcome {
  id: string
  program_version_id: string
  framework_po_id: string | null
  code: string
  title: string | null
  statement: string
  sequence: number
  is_active: boolean
  status: string
  effective_from: string | null
  effective_to: string | null
}

export interface CourseOutcome {
  id: string
  course_version_id: string
  code: string
  statement: string
  sequence: number
  bloom_target_level_id: string | null
  delivery_methods: string | null
  assessment_tools: string | null
  is_active: boolean
  status: string
}

export interface MappingScaleLevel {
  id: string
  mapping_scale_id: string
  value: number
  label: string
  sequence: number
}

export interface MappingScale {
  id: string
  name: string
  description: string | null
  is_default: boolean
  levels: MappingScaleLevel[]
}

export interface CourseOutcomePOMapping {
  id: string
  course_outcome_id: string
  program_outcome_id: string
  mapping_scale_level_id: string
  remarks: string | null
}

export interface ProgramOutcomePEOMapping {
  id: string
  program_outcome_id: string
  peo_id: string
  mapping_scale_level_id: string
  remarks: string | null
}
