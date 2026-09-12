import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiClient } from '@/lib/api-client'
import type { AuditLogEntry, AuditLogFilters, AuditLogSettings } from '@/features/audit/types'

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

export function useAuditLogSettings() {
  return useQuery<AuditLogSettings>({
    queryKey: ['audit-log-settings'],
    queryFn: async () => (await apiClient.get<AuditLogSettings>('/audit/settings')).data,
  })
}

export function useUpdateAuditLogSettings() {
  const queryClient = useQueryClient()
  return useMutation<AuditLogSettings, unknown, { retention_days: number | null }>({
    mutationFn: async (body) =>
      (await apiClient.patch<AuditLogSettings>('/audit/settings', body)).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['audit-log-settings'] }),
  })
}
