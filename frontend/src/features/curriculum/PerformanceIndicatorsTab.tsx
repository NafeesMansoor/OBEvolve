import * as React from 'react'
import { ArrowRight, Plus } from 'lucide-react'
import { toast } from 'sonner'
import { z } from 'zod'

import { useAuth } from '@/features/auth/useAuth'
import type { PerformanceIndicator, ProgramOutcome } from '@/features/curriculum/types'
import { useProgramVersionOptions } from '@/features/curriculum/useProgramVersionOptions'
import { ApiError } from '@/lib/api-client'
import { useEntityAction, useEntityCreate, useEntityList } from '@/lib/crud-hooks'
import { Button } from '@/components/ui/button'
import { DataTable, type DataTableColumn } from '@/components/data-table'
import { EntityFormDialog, type EntityField } from '@/components/entity-form-dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { StatusBadge, WORKFLOW_NEXT, type WorkflowStatus } from '@/components/status-badge'

const createSchema = z.object({
  statement: z.string().min(1, 'Statement is required'),
  sequence: z.coerce.number().int(),
})

/** Performance Indicators — the Indicator-Based PO Definition Method's
 * sub-items (spec §18): PO(a) -> PI(a1), PI(a2). Only meaningful for a
 * curriculum whose po_definition_method is "indicator_based"; shown for
 * any program version but the create action is hidden (with an
 * explanatory note) when the selected version uses the Direct method. */
export function PerformanceIndicatorsTab() {
  const { hasPermission } = useAuth()
  const canManage = hasPermission('program_outcome_framework.manage')
  const { options: pvOptions, versions } = useProgramVersionOptions()
  const [programVersionId, setProgramVersionId] = React.useState('')
  const [programOutcomeId, setProgramOutcomeId] = React.useState('')
  const [createOpen, setCreateOpen] = React.useState(false)

  const selectedVersion = versions.find((v) => v.id === programVersionId)
  const isIndicatorBased = selectedVersion?.po_definition_method === 'indicator_based'

  const { data: outcomes } = useEntityList<ProgramOutcome>(
    ['curriculum', 'program-outcomes', programVersionId],
    '/curriculum/program-outcomes',
    { program_version_id: programVersionId || undefined },
    { enabled: Boolean(programVersionId) },
  )

  const {
    data: indicators,
    isLoading,
    error,
  } = useEntityList<PerformanceIndicator>(
    ['curriculum', 'performance-indicators', programOutcomeId],
    '/curriculum/performance-indicators',
    { program_outcome_id: programOutcomeId || undefined },
    { enabled: Boolean(programOutcomeId) },
  )
  const create = useEntityCreate<Record<string, unknown>, PerformanceIndicator>(
    '/curriculum/performance-indicators',
    [['curriculum', 'performance-indicators', programOutcomeId]],
  )
  const advance = useEntityAction<PerformanceIndicator>(
    (id) => `/curriculum/performance-indicators/${id}/advance`,
    [['curriculum', 'performance-indicators', programOutcomeId]],
  )

  const fields: EntityField[] = [
    { name: 'statement', label: 'Statement', type: 'textarea' },
    { name: 'sequence', label: 'Sequence', type: 'number' },
  ]

  const columns: DataTableColumn<PerformanceIndicator>[] = [
    { key: 'code', header: 'Code', render: (r) => r.code },
    { key: 'statement', header: 'Statement', render: (r) => r.statement, className: 'max-w-md' },
    { key: 'sequence', header: 'Seq', render: (r) => r.sequence },
    { key: 'status', header: 'Status', render: (r) => <StatusBadge status={r.status} /> },
  ]

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-2">
        <div className="w-full max-w-sm">
          <Select
            value={programVersionId}
            onValueChange={(v) => {
              setProgramVersionId(v)
              setProgramOutcomeId('')
            }}
          >
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
        {programVersionId && (
          <div className="w-full max-w-sm">
            <Select value={programOutcomeId} onValueChange={setProgramOutcomeId}>
              <SelectTrigger>
                <SelectValue placeholder="Select a program outcome" />
              </SelectTrigger>
              <SelectContent>
                {(outcomes ?? []).map((o) => (
                  <SelectItem key={o.id} value={o.id}>
                    {o.code}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}
        {canManage && programOutcomeId && isIndicatorBased && (
          <Button size="sm" onClick={() => setCreateOpen(true)}>
            <Plus className="size-4" /> New indicator
          </Button>
        )}
      </div>

      {programVersionId && !isIndicatorBased && (
        <p className="text-sm text-muted-foreground">
          This program version uses the Direct PO definition method — Performance Indicators only
          apply to Indicator-Based curricula. Change the method under Curriculum before adding
          indicators here.
        </p>
      )}

      {!programOutcomeId ? (
        <p className="text-sm text-muted-foreground">Select a program outcome to see its indicators.</p>
      ) : (
        <DataTable
          data={indicators}
          columns={columns}
          rowKey={(r) => r.id}
          isLoading={isLoading}
          error={error}
          emptyMessage="No performance indicators yet for this program outcome."
          actions={(r) => {
            const next = WORKFLOW_NEXT[r.status as WorkflowStatus]
            if (!canManage || !next) return null
            return (
              <Button
                size="sm"
                variant="outline"
                onClick={async () => {
                  try {
                    await advance.mutateAsync(r.id)
                    toast.success(`Advanced to ${next}`)
                  } catch (err) {
                    toast.error(err instanceof ApiError ? err.detail : 'Unable to advance.')
                  }
                }}
              >
                Advance to {next} <ArrowRight className="size-3.5" />
              </Button>
            )
          }}
        />
      )}

      <EntityFormDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        title="New performance indicator"
        description="The indicator's code is generated automatically from the parent outcome's code."
        fields={fields}
        schema={createSchema}
        defaultValues={{ statement: '', sequence: (indicators ?? []).length + 1 }}
        onSubmit={async (values) => {
          try {
            await create.mutateAsync({ program_outcome_id: programOutcomeId, ...values })
            toast.success('Performance indicator created')
          } catch (err) {
            throw err instanceof ApiError ? err : new ApiError('Unable to create indicator.')
          }
        }}
      />
    </div>
  )
}
