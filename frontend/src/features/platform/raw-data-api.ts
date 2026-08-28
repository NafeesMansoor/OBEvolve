import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { platformApiClient } from '@/lib/platform-api-client'
import type { RawRow, RowMutationResult, RowsPage, TableSchema } from '@/features/raw-data/types'

/** Platform-admin equivalent of features/raw-data/api.ts, hitting
 * /platform-raw-data instead of /raw-data — `institution_slug` is always
 * required here (a platform admin has no "home" institution to default
 * to), and `program_code` gates PROGRAM_SCHEMA_TABLES tables (see
 * app/services/raw_data.py). */

function qs(institutionSlug: string, programCode: string | null) {
  const params: Record<string, string> = { institution_slug: institutionSlug }
  if (programCode) params.program_code = programCode
  return params
}

export function usePlatformRawDataTables(institutionSlug: string | null) {
  return useQuery<string[]>({
    queryKey: ['platform-raw-data', 'tables', institutionSlug],
    queryFn: async () =>
      (
        await platformApiClient.get<string[]>('/platform-raw-data/tables', {
          params: { institution_slug: institutionSlug },
        })
      ).data,
    enabled: Boolean(institutionSlug),
  })
}

export function usePlatformTableSchema(tableName: string | null) {
  return useQuery<TableSchema>({
    queryKey: ['platform-raw-data', 'schema', tableName],
    queryFn: async () =>
      (
        await platformApiClient.get<TableSchema>(`/platform-raw-data/tables/${tableName}/schema`)
      ).data,
    enabled: Boolean(tableName),
  })
}

export function usePlatformTableRows(
  tableName: string | null,
  institutionSlug: string | null,
  programCode: string | null,
  page: number,
  pageSize: number,
) {
  return useQuery<RowsPage>({
    queryKey: ['platform-raw-data', 'rows', tableName, institutionSlug, programCode, page, pageSize],
    queryFn: async () =>
      (
        await platformApiClient.get<RowsPage>(`/platform-raw-data/tables/${tableName}/rows`, {
          params: { ...qs(institutionSlug!, programCode), page, page_size: pageSize },
        })
      ).data,
    enabled: Boolean(tableName && institutionSlug),
  })
}

function invalidateRows(
  queryClient: ReturnType<typeof useQueryClient>,
  tableName: string,
  institutionSlug: string | null,
) {
  void queryClient.invalidateQueries({
    queryKey: ['platform-raw-data', 'rows', tableName, institutionSlug],
  })
}

export function usePlatformInsertRow(
  tableName: string,
  institutionSlug: string | null,
  programCode: string | null,
) {
  const queryClient = useQueryClient()
  return useMutation<RowMutationResult, unknown, RawRow>({
    mutationFn: async (payload) =>
      (
        await platformApiClient.post<RowMutationResult>(
          `/platform-raw-data/tables/${tableName}/rows`,
          payload,
          { params: qs(institutionSlug!, programCode) },
        )
      ).data,
    onSuccess: () => invalidateRows(queryClient, tableName, institutionSlug),
  })
}

export function usePlatformUpdateRow(
  tableName: string,
  institutionSlug: string | null,
  programCode: string | null,
) {
  const queryClient = useQueryClient()
  return useMutation<RowMutationResult, unknown, { pk: string; payload: RawRow }>({
    mutationFn: async ({ pk, payload }) =>
      (
        await platformApiClient.patch<RowMutationResult>(
          `/platform-raw-data/tables/${tableName}/rows/${pk}`,
          payload,
          { params: qs(institutionSlug!, programCode) },
        )
      ).data,
    onSuccess: () => invalidateRows(queryClient, tableName, institutionSlug),
  })
}

export function usePlatformDeleteRow(
  tableName: string,
  institutionSlug: string | null,
  programCode: string | null,
) {
  const queryClient = useQueryClient()
  return useMutation<RowMutationResult, unknown, string>({
    mutationFn: async (pk) =>
      (
        await platformApiClient.delete<RowMutationResult>(
          `/platform-raw-data/tables/${tableName}/rows/${pk}`,
          { params: qs(institutionSlug!, programCode) },
        )
      ).data,
    onSuccess: () => invalidateRows(queryClient, tableName, institutionSlug),
  })
}
