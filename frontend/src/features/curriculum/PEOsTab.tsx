import * as React from 'react'
import { ArrowRight, Plus } from 'lucide-react'
import { toast } from 'sonner'
import { z } from 'zod'

import { useAuth } from '@/features/auth/useAuth'
import type { PEO } from '@/features/curriculum/types'
import { useProgramVersionOptions } from '@/features/curriculum/useProgramVersionOptions'
import { ApiError } from '@/lib/api-client'
import { useEntityAction, useEntityCreate, useEntityList, useEntityUpdate } from '@/lib/crud-hooks'
import { Button } from '@/components/ui/button'
import { DataTable, type DataTableColumn } from '@/components/data-table'
import { EntityFormDialog, type EntityField } from '@/components/entity-form-dialog'
import { RecordDetailSheet } from '@/components/record-detail-sheet'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { StatusBadge, WORKFLOW_NEXT, type WorkflowStatus } from '@/components/status-badge'

const createSchema = z.object({
  code: z.string().min(1, 'Code is required').max(20),
  statement: z.string().min(1, 'Statement is required'),
  description: z.string().optional(),
  sequence: z.coerce.number().int(),
})

/** Program Educational Objectives, scoped to a selected program version. */
export function PEOsTab() {
  const { hasPermission } = useAuth()
  const canManage = hasPermission('outcome.create')
  const canApprove = hasPermission('outcome.approve')
  const { options: pvOptions } = useProgramVersionOptions()
  const [programVersionId, setProgramVersionId] = React.useState('')
  const [createOpen, setCreateOpen] = React.useState(false)
  const [editPeo, setEditPeo] = React.useState<PEO | null>(null)
  const [viewPeo, setViewPeo] = React.useState<PEO | null>(null)

  const {
    data: peos,
    isLoading,
    error,
  } = useEntityList<PEO>(
    ['curriculum', 'peos', programVersionId],
    '/curriculum/peos',
    { program_version_id: programVersionId || undefined },
    { enabled: Boolean(programVersionId) },
  )
  const create = useEntityCreate<Record<string, unknown>, PEO>('/curriculum/peos', [
    ['curriculum', 'peos', programVersionId],
  ])
  const update = useEntityUpdate<Record<string, unknown>, PEO>((id) => `/curriculum/peos/${id}`, [
    ['curriculum', 'peos', programVersionId],
  ])
  const advance = useEntityAction<PEO>((id) => `/curriculum/peos/${id}/advance`, [
    ['curriculum', 'peos', programVersionId],
  ])

  const fields: EntityField[] = [
    { name: 'code', label: 'Code', type: 'text', placeholder: 'e.g. PEO1' },
    { name: 'statement', label: 'Statement', type: 'textarea' },
    { name: 'description', label: 'Description', type: 'textarea' },
    { name: 'sequence', label: 'Sequence', type: 'number' },
  ]

  const columns: DataTableColumn<PEO>[] = [
    { key: 'code', header: 'Code', render: (r) => r.code },
    { key: 'statement', header: 'Statement', render: (r) => r.statement, className: 'max-w-md' },
    { key: 'sequence', header: 'Seq', render: (r) => r.sequence },
    { key: 'status', header: 'Status', render: (r) => <StatusBadge status={r.status} /> },
  ]

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
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
        {canManage && programVersionId && (
          <Button size="sm" onClick={() => setCreateOpen(true)}>
            <Plus className="size-4" /> New PEO
          </Button>
        )}
      </div>

      {!programVersionId ? (
        <p className="text-sm text-muted-foreground">Select a program version to see its PEOs.</p>
      ) : (
        <DataTable
          data={peos}
          columns={columns}
          rowKey={(r) => r.id}
          isLoading={isLoading}
          error={error}
          emptyMessage="No PEOs yet for this program version."
          onRowClick={(r) => setViewPeo(r)}
          actions={(r) => {
            const next = WORKFLOW_NEXT[r.status as WorkflowStatus]
            if (!canApprove || !next) return null
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
        title="New PEO"
        fields={fields}
        schema={createSchema}
        defaultValues={{ code: '', statement: '', description: '', sequence: 1 }}
        onSubmit={async (values) => {
          try {
            await create.mutateAsync({
              program_version_id: programVersionId,
              code: values.code,
              statement: values.statement,
              description: values.description || null,
              sequence: values.sequence,
            })
            toast.success('PEO created')
          } catch (err) {
            throw err instanceof ApiError ? err : new ApiError('Unable to create PEO.')
          }
        }}
      />

      {viewPeo && (
        <RecordDetailSheet
          open={Boolean(viewPeo)}
          onOpenChange={(open) => !open && setViewPeo(null)}
          title={viewPeo.code}
          badge={<StatusBadge status={viewPeo.status} />}
          fields={[
            { label: 'Sequence', value: viewPeo.sequence },
            { label: 'Status', value: viewPeo.status },
            { label: 'Statement', value: viewPeo.statement, full: true },
            { label: 'Description', value: viewPeo.description ?? '—', full: true },
          ]}
          onEdit={
            canManage
              ? () => {
                  setEditPeo(viewPeo)
                  setViewPeo(null)
                }
              : undefined
          }
        />
      )}

      {editPeo && (
        <EntityFormDialog
          open={Boolean(editPeo)}
          onOpenChange={(open) => !open && setEditPeo(null)}
          title={`Edit ${editPeo.code}`}
          fields={fields}
          schema={createSchema}
          defaultValues={{
            code: editPeo.code,
            statement: editPeo.statement,
            description: editPeo.description ?? '',
            sequence: editPeo.sequence,
          }}
          onSubmit={async (values) => {
            try {
              await update.mutateAsync({ id: editPeo.id, body: values })
              toast.success('PEO updated')
            } catch (err) {
              throw err instanceof ApiError ? err : new ApiError('Unable to update PEO.')
            }
          }}
        />
      )}
    </div>
  )
}
