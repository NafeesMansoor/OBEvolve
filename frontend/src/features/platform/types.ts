export interface InstitutionRead {
  id: string
  name: string
  code: string
  slug: string
  schema_name: string
  status: string
  subscription_plan: string | null
  contact_email: string
  logo_url: string | null
  timezone: string
  created_at: string
  updated_at: string
}

export interface InstitutionCreateInput {
  name: string
  code: string
  slug: string
  contact_email: string
  subscription_plan?: string | null
  timezone?: string
  seed_demo?: boolean
  admin_full_name?: string | null
  admin_email?: string | null
}

export interface InstitutionCreateResult {
  institution: InstitutionRead
  admin_temporary_password: string | null
}

export type InstitutionStatus = 'trial' | 'active' | 'suspended' | 'archived'

export interface InstitutionAdminRead {
  id: string
  email: string
  full_name: string
  is_active: boolean
  must_change_password: boolean
  created_at: string
}

export interface InstitutionAdminCreateInput {
  full_name: string
  email: string
}

export interface InstitutionAdminCreateResult {
  admin: InstitutionAdminRead
  temporary_password: string
}

export interface InstitutionAdminResetPasswordResult {
  temporary_password: string
}

/** The fixed code-level permission catalogue (app.core.permissions.PERMISSIONS)
 * — not a tenant DB row (a platform admin has no tenant session), but the
 * same shape as the tenant-side Permission catalogue entry. */
export interface PermissionCatalogueEntry {
  code: string
  description: string
  module: string
}

export interface RoleTemplateRead {
  id: string
  name: string
  description: string | null
  permission_codes: string[]
  all_permissions: boolean
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface RoleTemplateCreateInput {
  name: string
  description?: string | null
  permission_codes: string[]
  all_permissions?: boolean
}

export interface RoleTemplateUpdateInput {
  name?: string
  description?: string | null
  permission_codes?: string[]
  all_permissions?: boolean
  is_active?: boolean
}

export interface RoleTemplateResyncResult {
  succeeded: string[]
  failed: string[]
}
