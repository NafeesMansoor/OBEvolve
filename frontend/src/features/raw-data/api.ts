import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { apiClient } from '@/lib/api-client'
import type {
  ChangeRequestRead,
  InstitutionOption,
  RawRow,
  RowMutationResult,
  RowsPage,
  TableSchema,
} from '@/features/raw-data/types'

/**
 * Hand-rolled (not the generic crud-hooks wrappers) because every URL here
 * is parameterized by a dynamically-selected table name and an optional
 * institution_slug query param that must ride along on every call for this
 * page's session — the generic wrappers assume a fixed URL per resource.
 */

function qs(institutionSlug: string | null | undefined): Record<string, string | undefined> {
  return institutionSlug ? { institution_slug: institutionSlug } : {}
}

export function useInstitutions(enabled: boolean) {
  return useQuery<InstitutionOption[]>({
    queryKey: ['raw-data', 'institutions'],
    queryFn: async () => (await apiClient.get<InstitutionOption[]>('/raw-data/institutions')).data,
    enabled,
  })
}

export function useRawDataTables(institutionSlug: string | null) {
  return useQuery<string[]>({
    queryKey: ['raw-data', 'tables', institutionSlug],
    queryFn: async () =>
      (
        await apiClient.get<string[]>('/raw-data/tables', {
          params: qs(institutionSlug),
        })
      ).data,
  })
}

export function useTableSchema(tableName: string | null, institutionSlug: string | null) {
  return useQuery<TableSchema>({
    queryKey: ['raw-data', 'schema', tableName, institutionSlug],
    queryFn: async () =>
      (
        await apiClient.get<TableSchema>(`/raw-data/tables/${tableName}/schema`, {
          params: qs(institutionSlug),
        })
      ).data,
    enabled: Boolean(tableName),
  })
}

export function useTableRows(
  tableName: string | null,
  institutionSlug: string | null,
  page: number,
  pageSize: number,
) {
  return useQuery<RowsPage>({
    queryKey: ['raw-data', 'rows', tableName, institutionSlug, page, pageSize],
    queryFn: async () =>
      (
        await apiClient.get<RowsPage>(`/raw-data/tables/${tableName}/rows`, {
          params: { ...qs(institutionSlug), page, page_size: pageSize },
        })
      ).data,
    enabled: Boolean(tableName),
  })
}

function invalidateRows(
  queryClient: ReturnType<typeof useQueryClient>,
  tableName: string,
  institutionSlug: string | null,
) {
  void queryClient.invalidateQueries({
    queryKey: ['raw-data', 'rows', tableName, institutionSlug],
  })
}

export function useInsertRow(tableName: string, institutionSlug: string | null) {
  const queryClient = useQueryClient()
  return useMutation<RowMutationResult, unknown, RawRow>({
    mutationFn: async (payload) =>
      (
        await apiClient.post<RowMutationResult>(`/raw-data/tables/${tableName}/rows`, payload, {
          params: qs(institutionSlug),
        })
      ).data,
    onSuccess: () => invalidateRows(queryClient, tableName, institutionSlug),
  })
}

export function useUpdateRow(tableName: string, institutionSlug: string | null) {
  const queryClient = useQueryClient()
  return useMutation<RowMutationResult, unknown, { pk: string; payload: RawRow }>({
    mutationFn: async ({ pk, payload }) =>
      (
        await apiClient.patch<RowMutationResult>(
          `/raw-data/tables/${tableName}/rows/${pk}`,
          payload,
          { params: qs(institutionSlug) },
        )
      ).data,
    onSuccess: () => invalidateRows(queryClient, tableName, institutionSlug),
  })
}

export function useDeleteRow(tableName: string, institutionSlug: string | null) {
  const queryClient = useQueryClient()
  return useMutation<RowMutationResult, unknown, string>({
    mutationFn: async (pk) =>
      (
        await apiClient.delete<RowMutationResult>(`/raw-data/tables/${tableName}/rows/${pk}`, {
          params: qs(institutionSlug),
        })
      ).data,
    onSuccess: () => invalidateRows(queryClient, tableName, institutionSlug),
  })
}

export function usePendingChanges() {
  return useQuery<ChangeRequestRead[]>({
    queryKey: ['raw-data', 'pending-changes'],
    queryFn: async () =>
      (await apiClient.get<ChangeRequestRead[]>('/raw-data/pending-changes')).data,
  })
}

export function useReviewPendingChange(decision: 'approve' | 'reject') {
  const queryClient = useQueryClient()
  return useMutation<ChangeRequestRead, unknown, { id: string; reviewNote?: string }>({
    mutationFn: async ({ id, reviewNote }) =>
      (
        await apiClient.post<ChangeRequestRead>(`/raw-data/pending-changes/${id}/${decision}`, {
          review_note: reviewNote || undefined,
        })
      ).data,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['raw-data', 'pending-changes'] })
    },
  })
}
