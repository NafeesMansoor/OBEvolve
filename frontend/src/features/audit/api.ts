import { useQuery } from '@tanstack/react-query'

import { apiClient } from '@/lib/api-client'
import type { AuditLogEntry, AuditLogFilters } from '@/features/audit/types'

const FETCH_LIMIT = 150

export function useAuditLog(filters: AuditLogFilters) {
  return useQuery<AuditLogEntry[]>({
    queryKey: ['audit-log', filters],
    queryFn: async () =>
      (
        await apiClient.get<AuditLogEntry[]>('/audit', {
          params: { ...filters, limit: FETCH_LIMIT },
        })
      ).data,
  })
}
