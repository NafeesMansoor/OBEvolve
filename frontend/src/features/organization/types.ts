export interface Campus {
  id: string
  institution_id: string
  name: string
  code: string
  address: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface School {
  id: string
  campus_id: string
  name: string
  code: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Department {
  id: string
  school_id: string
  name: string
  code: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface Program {
  id: string
  department_id: string
  name: string
  code: string
  degree_level: string | null
  is_active: boolean
  session_names: string[]
  created_at: string
  updated_at: string
}

export interface ProgramVersion {
  id: string
  program_id: string
  version_label: string
  effective_academic_year_id: string
  status: string
  created_by: string | null
  approved_by: string | null
  published_by: string | null
  published_at: string | null
  unpublished_by: string | null
  unpublished_at: string | null
  previous_version_id: string | null
  po_definition_method: 'direct' | 'indicator_based'
  peo_numbering_style: string
  po_numbering_style: string
  created_at: string
  updated_at: string
}

export interface AcademicYear {
  id: string
  label: string
  start_date: string
  end_date: string
  is_active: boolean
}

export interface AcademicTerm {
  id: string
  academic_year_id: string
  name: string
  term_type: string
  start_date: string
  end_date: string
  add_drop_last_date: string | null
  midterm_start_date: string | null
  midterm_end_date: string | null
  final_exam_start_date: string | null
  final_exam_end_date: string | null
  result_due_date: string | null
  result_publication_date: string | null
  is_active: boolean
}

export interface TermEffectiveCurriculum {
  id: string
  academic_term_id: string
  program_version_id: string
  created_by: string | null
  created_at: string
}

export interface AppUser {
  id: string
  email: string
  full_name: string
  is_active: boolean
  mfa_enabled: boolean
  last_login_at: string | null
  created_at: string
  updated_at: string
}

export interface Role {
  id: string
  name: string
  description: string | null
  is_system_role: boolean
  is_active: boolean
  permission_codes: string[]
}

/** A permission catalogue entry — fixed, never created ad hoc (see
 * backend `Permission` model docstring). Grouped by `module` in the
 * role-creation/edit UI. */
export interface Permission {
  id: string
  code: string
  description: string
  module: string
}

export interface RoleCreateInput {
  name: string
  description?: string | null
  permission_codes: string[]
}

export interface RoleUpdateInput {
  name?: string
  description?: string | null
  is_active?: boolean
  permission_codes?: string[]
}

/** A platform default-role catalogue entry (`public.role_templates`),
 * read-only from a tenant's perspective — "fetch the default roles"
 * (Institute Settings feedback). */
export interface RoleTemplate {
  id: string
  name: string
  description: string | null
  permission_codes: string[]
  all_permissions: boolean
  is_active: boolean
}

export interface UserRoleGrant {
  id: string
  user_id: string
  role_id: string
  scope_type: string | null
  scope_id: string | null
}

export interface ProgramFaculty {
  id: string
  email: string
  full_name: string
}

export interface ProgramCourse {
  id: string
  code: string
  title: string
}

export interface ProgramRoleGrant {
  id: string
  user_id: string
  role_id: string
  scope_type: string | null
  scope_id: string | null
}

export interface ProgramRoster {
  faculty: ProgramFaculty[]
  assignable_roles: { id: string; name: string }[]
  courses: ProgramCourse[]
  grants: ProgramRoleGrant[]
}

export interface TermCommitStatus {
  academic_term_id: string
  term_name: string
  term_end_date: string
  is_committed: boolean
  manually_enabled: boolean
  committable: boolean
  committed_by: string | null
  committed_at: string | null
}
