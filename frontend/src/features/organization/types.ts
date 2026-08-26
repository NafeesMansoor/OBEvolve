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
  is_active: boolean
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
}

export interface UserRoleGrant {
  id: string
  user_id: string
  role_id: string
  scope_type: string | null
  scope_id: string | null
}
