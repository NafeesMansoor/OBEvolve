import {
  useMutation,
  useQuery,
  useQueryClient,
  type QueryKey,
  type UseQueryOptions,
} from '@tanstack/react-query'

import { apiClient } from '@/lib/api-client'

/**
 * Thin generic wrappers around @tanstack/react-query for the many
 * near-identical REST resources this app talks to (see backend
 * app/api/v1/endpoints/{org,users,curriculum,academic_ops,grading,assessment}.py).
 * Every entity list/create/update/delete/advance flow rides these instead of
 * hand-rolled fetch + useState/useEffect plumbing.
 */

export function useEntityList<T>(
  queryKey: QueryKey,
  url: string,
  params?: Record<string, string | undefined>,
  options?: Partial<UseQueryOptions<T[]>>,
) {
  return useQuery<T[]>({
    queryKey,
    queryFn: async () => {
      const res = await apiClient.get<T[]>(url, { params })
      return res.data
    },
    ...options,
  })
}

export function useEntityGet<T>(
  queryKey: QueryKey,
  url: string,
  options?: Partial<UseQueryOptions<T>> & { enabled?: boolean },
) {
  return useQuery<T>({
    queryKey,
    queryFn: async () => {
      const res = await apiClient.get<T>(url)
      return res.data
    },
    ...options,
  })
}

function invalidate(queryClient: ReturnType<typeof useQueryClient>, keys: QueryKey[]) {
  keys.forEach((key) => void queryClient.invalidateQueries({ queryKey: key }))
}

export function useEntityCreate<TBody, TResp = unknown>(
  url: string,
  invalidateKeys: QueryKey[],
) {
  const queryClient = useQueryClient()
  return useMutation<TResp, unknown, TBody>({
    mutationFn: async (body: TBody) => {
      const res = await apiClient.post<TResp>(url, body)
      return res.data
    },
    onSuccess: () => invalidate(queryClient, invalidateKeys),
  })
}

export function useEntityUpdate<TBody, TResp = unknown>(
  urlFn: (id: string) => string,
  invalidateKeys: QueryKey[],
) {
  const queryClient = useQueryClient()
  return useMutation<TResp, unknown, { id: string; body: TBody }>({
    mutationFn: async ({ id, body }) => {
      const res = await apiClient.patch<TResp>(urlFn(id), body)
      return res.data
    },
    onSuccess: () => invalidate(queryClient, invalidateKeys),
  })
}

export function useEntityDelete(urlFn: (id: string) => string, invalidateKeys: QueryKey[]) {
  const queryClient = useQueryClient()
  return useMutation<void, unknown, string>({
    mutationFn: async (id: string) => {
      await apiClient.delete(urlFn(id))
    },
    onSuccess: () => invalidate(queryClient, invalidateKeys),
  })
}

/** For POST-style non-CRUD actions with no body, e.g. `.../advance`. */
export function useEntityAction<TResp = unknown>(
  urlFn: (id: string) => string,
  invalidateKeys: QueryKey[],
) {
  const queryClient = useQueryClient()
  return useMutation<TResp, unknown, string>({
    mutationFn: async (id: string) => {
      const res = await apiClient.post<TResp>(urlFn(id))
      return res.data
    },
    onSuccess: () => invalidate(queryClient, invalidateKeys),
  })
}
