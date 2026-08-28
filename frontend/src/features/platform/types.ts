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
}
