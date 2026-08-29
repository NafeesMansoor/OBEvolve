export interface Notification {
  id: string
  type: string
  title: string
  body: string | null
  is_read: boolean
  created_at: string
}

export type PendingApprovalType = 'assessment_document' | 'raw_data_change' | 'improvement_plan'

export interface PendingApprovalItem {
  type: PendingApprovalType
  count: number
  label: string
}

export interface PendingApprovalsSummary {
  total: number
  items: PendingApprovalItem[]
}

/** Where a pending-approval category's "review it" page lives. Kept here
 * (not on the API response) since it's a frontend routing concern. */
export const PENDING_APPROVAL_ROUTES: Record<PendingApprovalType, string> = {
  assessment_document: '/assessment',
  raw_data_change: '/raw-data/pending-changes',
  improvement_plan: '/assessment',
}
