export interface AuditLogEntry {
  id: string
  timestamp: string
  actor: string | null
  action: string
  entity_type: string
  entity_id: string | null
  previous_value_json: Record<string, unknown> | null
  new_value_json: Record<string, unknown> | null
}

export interface AuditLogFilters {
  entity_type?: string
  action?: string
  date_from?: string
  date_to?: string
}
