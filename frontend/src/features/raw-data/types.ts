/** Types matching backend/app/schemas/raw_data.py exactly. */

export type ColumnTypeTag =
  | 'string'
  | 'text'
  | 'integer'
  | 'numeric'
  | 'boolean'
  | 'date'
  | 'datetime'
  | 'uuid'
  | 'json'

export interface ColumnSchema {
  name: string
  type: ColumnTypeTag
  nullable: boolean
  is_primary_key: boolean
  foreign_key: string | null
}

export interface TableSchema {
  table_name: string
  columns: ColumnSchema[]
}

export type RawRow = Record<string, unknown>

export interface RowsPage {
  rows: RawRow[]
  total: number
  page: number
  page_size: number
}

export interface RowMutationResult {
  mode: 'immediate' | 'propose'
  row: RawRow | null
  change_request_id: string | null
}

export interface InstitutionOption {
  id: string
  name: string
  slug: string
  schema_name: string
}

export type ChangeOperation = 'insert' | 'update' | 'delete'
export type ChangeStatus = 'pending' | 'approved' | 'rejected'

export interface ChangeRequestRead {
  id: string
  requested_by: string
  table_name: string
  operation: ChangeOperation
  row_pk: string | null
  payload_json: RawRow | null
  previous_json: RawRow | null
  status: ChangeStatus
  scope_type: string
  scope_id: string
  reviewed_by: string | null
  review_note: string | null
  created_at: string
  reviewed_at: string | null
}
