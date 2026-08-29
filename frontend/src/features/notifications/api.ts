import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiClient } from '@/lib/api-client'
import type { Notification, PendingApprovalsSummary } from '@/features/notifications/types'

const REFETCH_INTERVAL_MS = 60_000

export function useNotifications(enabled: boolean) {
  return useQuery<Notification[]>({
    queryKey: ['notifications', 'list'],
    queryFn: async () => (await apiClient.get<Notification[]>('/notifications')).data,
    enabled,
    refetchInterval: REFETCH_INTERVAL_MS,
  })
}

export function useUnreadCount(enabled: boolean) {
  return useQuery<number>({
    queryKey: ['notifications', 'unread-count'],
    queryFn: async () =>
      (await apiClient.get<{ count: number }>('/notifications/unread-count')).data.count,
    enabled,
    refetchInterval: REFETCH_INTERVAL_MS,
  })
}

export function usePendingApprovals(enabled: boolean) {
  return useQuery<PendingApprovalsSummary>({
    queryKey: ['notifications', 'pending-approvals'],
    queryFn: async () =>
      (await apiClient.get<PendingApprovalsSummary>('/notifications/pending-approvals')).data,
    enabled,
    refetchInterval: REFETCH_INTERVAL_MS,
  })
}

export function useMarkNotificationRead() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) => {
      await apiClient.post(`/notifications/${id}/read`)
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['notifications'] })
    },
  })
}

export function useMarkAllNotificationsRead() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async () => {
      await apiClient.post('/notifications/read-all')
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['notifications'] })
    },
  })
}
