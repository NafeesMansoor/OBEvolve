import { useQuery } from '@tanstack/react-query'

import { apiClient } from '@/lib/api-client'
import type { SearchResponse } from '@/features/search/types'

const MIN_QUERY_LENGTH = 2

export function useGlobalSearch(query: string, enabled: boolean) {
  const trimmed = query.trim()
  return useQuery<SearchResponse>({
    queryKey: ['search', trimmed],
    queryFn: async () =>
      (await apiClient.get<SearchResponse>('/search', { params: { q: trimmed } })).data,
    enabled: enabled && trimmed.length >= MIN_QUERY_LENGTH,
  })
}
