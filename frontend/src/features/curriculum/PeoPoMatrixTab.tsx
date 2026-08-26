import * as React from 'react'
import { useQueries, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { useAuth } from '@/features/auth/useAuth'
import type { MappingScale, PEO, ProgramOutcome, ProgramOutcomePEOMapping } from '@/features/curriculum/types'
import { MappingMatrix, type MatrixCell } from '@/features/curriculum/MappingMatrix'
import { useProgramVersionOptions } from '@/features/curriculum/useProgramVersionOptions'
import { ApiError, apiClient } from '@/lib/api-client'
import { useEntityList } from '@/lib/crud-hooks'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

export function PeoPoMatrixTab() {
  const { hasPermission } = useAuth()
  const canEdit = hasPermission('mapping.create')
  const queryClient = useQueryClient()

  const { options: pvOptions } = useProgramVersionOptions()
  const [programVersionId, setProgramVersionId] = React.useState('')

  const { data: pos, isLoading: posLoading } = useEntityList<ProgramOutcome>(
    ['curriculum', 'program-outcomes', programVersionId],
    '/curriculum/program-outcomes',
    { program_version_id: programVersionId || undefined },
    { enabled: Boolean(programVersionId) },
  )
  const { data: peos, isLoading: peosLoading } = useEntityList<PEO>(
    ['curriculum', 'peos', programVersionId],
    '/curriculum/peos',
    { program_version_id: programVersionId || undefined },
    { enabled: Boolean(programVersionId) },
  )
  const { data: scales } = useEntityList<MappingScale>(
    ['curriculum', 'mapping-scales'],
    '/curriculum/mapping-scales',
  )
  const defaultScale = React.useMemo(
    () => scales?.find((s) => s.is_default) ?? scales?.[0],
    [scales],
  )

  const poIds = React.useMemo(() => (pos ?? []).map((p) => p.id), [pos])
  const mappingQueries = useQueries({
    queries: poIds.map((poId) => ({
      queryKey: ['curriculum', 'peo-po-mappings', poId],
      queryFn: async () =>
        (
          await apiClient.get<ProgramOutcomePEOMapping[]>('/curriculum/program-outcome-peo-mappings', {
            params: { program_outcome_id: poId },
          })
        ).data,
      enabled: poIds.length > 0,
    })),
  })
  const mappingsLoading = mappingQueries.some((q) => q.isLoading)

  const cells = React.useMemo(() => {
    const map = new Map<string, MatrixCell>()
    mappingQueries.forEach((q) => {
      ;(q.data ?? []).forEach((m) => {
        map.set(`${m.program_outcome_id}:${m.peo_id}`, {
          mappingId: m.id,
          levelId: m.mapping_scale_level_id,
        })
      })
    })
    return map
  }, [mappingQueries])

  function invalidateAll() {
    poIds.forEach((poId) =>
      void queryClient.invalidateQueries({ queryKey: ['curriculum', 'peo-po-mappings', poId] }),
    )
  }

  async function handleSet(rowId: string, colId: string, levelId: string) {
    const existing = cells.get(`${rowId}:${colId}`)
    try {
      if (existing) {
        await apiClient.delete(`/curriculum/program-outcome-peo-mappings/${existing.mappingId}`)
      }
      await apiClient.post('/curriculum/program-outcome-peo-mappings', {
        program_outcome_id: rowId,
        peo_id: colId,
        mapping_scale_level_id: levelId,
      })
      invalidateAll()
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Unable to set mapping.')
    }
  }

  async function handleClear(_rowId: string, _colId: string, mappingId: string) {
    try {
      await apiClient.delete(`/curriculum/program-outcome-peo-mappings/${mappingId}`)
      invalidateAll()
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Unable to clear mapping.')
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="w-full max-w-sm">
        <Select value={programVersionId} onValueChange={setProgramVersionId}>
          <SelectTrigger>
            <SelectValue placeholder="Select a program version" />
          </SelectTrigger>
          <SelectContent>
            {pvOptions.map((o) => (
              <SelectItem key={o.value} value={o.value}>
                {o.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {!programVersionId ? (
        <p className="text-sm text-muted-foreground">
          Select a program version to build its PEO-PO mapping matrix.
        </p>
      ) : (
        <MappingMatrix
          rows={(pos ?? []).map((p) => ({ id: p.id, code: p.code, label: p.statement }))}
          cols={(peos ?? []).map((p) => ({ id: p.id, code: p.code, label: p.statement }))}
          rowHeader="Program Outcome"
          colHeader="PEO"
          scale={defaultScale}
          cells={cells}
          isLoading={posLoading || peosLoading || mappingsLoading}
          readOnly={!canEdit}
          onSetCell={handleSet}
          onClearCell={handleClear}
        />
      )}
    </div>
  )
}
