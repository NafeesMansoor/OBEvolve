import * as React from 'react'
import { ArrowRight, Plus } from 'lucide-react'
import { useQueries } from '@tanstack/react-query'
import { toast } from 'sonner'
import { z } from 'zod'

import { useAuth } from '@/features/auth/useAuth'
import type { AccreditationFramework, FrameworkDetail, ProgramOutcome } from '@/features/curriculum/types'
import { useProgramVersionOptions } from '@/features/curriculum/useProgramVersionOptions'
import { apiClient, ApiError } from '@/lib/api-client'
import { useEntityAction, useEntityCreate, useEntityList, useEntityUpdate } from '@/lib/crud-hooks'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { DataTable, type DataTableColumn } from '@/components/data-table'
import { EntityFormDialog, type EntityField } from '@/components/entity-form-dialog'
import { RecordDetailSheet } from '@/components/record-detail-sheet'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { StatusBadge, WORKFLOW_NEXT, type WorkflowStatus } from '@/components/status-badge'

/** Program Outcomes, scoped to a selected program version. Linking a PO to a
 * framework PO is always an explicit, deliberate dropdown choice — never
 * auto-suggested by text similarity (see docs/adr/0002-framework-aware-outcomes.md). */
export function ProgramOutcomesTab() {
  const { hasPermission } = useAuth()
  const canManage = hasPermission('outcome.create')
  const canApprove = hasPermission('outcome.approve')
  const { options: pvOptions } = useProgramVersionOptions()
  const [programVersionId, setProgramVersionId] = React.useState('')
  const [createOpen, setCreateOpen] = React.useState(false)
  const [editPO, setEditPO] = React.useState<ProgramOutcome | null>(null)
  const [viewPO, setViewPO] = React.useState<ProgramOutcome | null>(null)

  const { data: frameworks } = useEntityList<AccreditationFramework>(
    ['curriculum', 'frameworks'],
    '/curriculum/frameworks',
  )
  const frameworkPoOptions = useAllFrameworkPOOptions(frameworks ?? [])
  const frameworkPoLabelById = React.useMemo(
    () => new Map(frameworkPoOptions.map((o) => [o.value, o.label])),
    [frameworkPoOptions],
  )

  const {
    data: pos,
    isLoading,
    error,
  } = useEntityList<ProgramOutcome>(
    ['curriculum', 'program-outcomes', programVersionId],
    '/curriculum/program-outcomes',
    { program_version_id: programVersionId || undefined },
    { enabled: Boolean(programVersionId) },
  )
  const create = useEntityCreate<Record<string, unknown>, ProgramOutcome>(
    '/curriculum/program-outcomes',
    [['curriculum', 'program-outcomes', programVersionId]],
  )
  const update = useEntityUpdate<Record<string, unknown>, ProgramOutcome>(
    (id) => `/curriculum/program-outcomes/${id}`,
    [['curriculum', 'program-outcomes', programVersionId]],
  )
  const advance = useEntityAction<ProgramOutcome>(
    (id) => `/curriculum/program-outcomes/${id}/advance`,
    [['curriculum', 'program-outcomes', programVersionId]],
  )

  const columns: DataTableColumn<ProgramOutcome>[] = [
    { key: 'code', header: 'Code', render: (r) => r.code },
    { key: 'statement', header: 'Statement', render: (r) => r.statement, className: 'max-w-md' },
    {
      key: 'framework',
      header: 'Framework PO link',
      render: (r) =>
        r.framework_po_id ? (
          <Badge variant="outline" className="font-normal">
            Linked
          </Badge>
        ) : (
          <span className="text-xs text-muted-foreground">Unlinked</span>
        ),
    },
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
            <Plus className="size-4" /> New program outcome
          </Button>
        )}
      </div>

      {!programVersionId ? (
        <p className="text-sm text-muted-foreground">
          Select a program version to see its program outcomes.
        </p>
      ) : (
        <DataTable
          data={pos}
          columns={columns}
          rowKey={(r) => r.id}
          isLoading={isLoading}
          error={error}
          emptyMessage="No program outcomes yet for this program version."
          onRowClick={(r) => setViewPO(r)}
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

      {createOpen && (
        <ProgramOutcomeFormDialog
          open={createOpen}
          onOpenChange={setCreateOpen}
          title="New program outcome"
          frameworks={frameworks ?? []}
          initial={null}
          onSubmit={async (body) => {
            try {
              await create.mutateAsync({ ...body, program_version_id: programVersionId })
              toast.success('Program outcome created')
            } catch (err) {
              throw err instanceof ApiError ? err : new ApiError('Unable to create program outcome.')
            }
          }}
        />
      )}

      {viewPO && (
        <RecordDetailSheet
          open={Boolean(viewPO)}
          onOpenChange={(open) => !open && setViewPO(null)}
          title={viewPO.title ? `${viewPO.code} — ${viewPO.title}` : viewPO.code}
          badge={<StatusBadge status={viewPO.status} />}
          fields={[
            { label: 'Sequence', value: viewPO.sequence },
            { label: 'Status', value: viewPO.status },
            {
              label: 'Linked framework PO',
              value: viewPO.framework_po_id
                ? (frameworkPoLabelById.get(viewPO.framework_po_id) ?? 'Linked')
                : 'Unlinked',
            },
            { label: 'Statement', value: viewPO.statement, full: true },
          ]}
          onEdit={
            canManage
              ? () => {
                  setEditPO(viewPO)
                  setViewPO(null)
                }
              : undefined
          }
        />
      )}

      {editPO && (
        <ProgramOutcomeFormDialog
          open={Boolean(editPO)}
          onOpenChange={(open) => !open && setEditPO(null)}
          title={`Edit ${editPO.code}`}
          frameworks={frameworks ?? []}
          initial={editPO}
          onSubmit={async (body) => {
            try {
              await update.mutateAsync({ id: editPO.id, body })
              toast.success('Program outcome updated')
            } catch (err) {
              throw err instanceof ApiError ? err : new ApiError('Unable to update program outcome.')
            }
          }}
        />
      )}
    </div>
  )
}

/** All frameworks are typically just one (e.g. BAETE v3.0), so rather than a
 * cascading framework->PO picker (which would need live cross-field state
 * the generic EntityFormDialog doesn't expose), every framework PO across
 * every framework is fetched up front and shown in one flat dropdown,
 * labeled with its framework so the choice stays legible if there's ever
 * more than one. Still a plain, explicit dropdown — never auto-matched. */
function useAllFrameworkPOOptions(frameworks: AccreditationFramework[]) {
  const results = useQueries({
    queries: frameworks.map((f) => ({
      queryKey: ['curriculum', 'frameworks', f.id],
      queryFn: async () => (await apiClient.get<FrameworkDetail>(`/curriculum/frameworks/${f.id}`)).data,
      enabled: frameworks.length > 0,
    })),
  })

  return React.useMemo(() => {
    const options: { label: string; value: string }[] = []
    results.forEach((r, i) => {
      const framework = frameworks[i]
      const detail = r.data
      detail?.framework_pos.forEach((fp) => {
        options.push({ label: `[${framework?.name}] ${fp.code} — ${fp.statement}`, value: fp.id })
      })
    })
    return options
  }, [results, frameworks])
}

function ProgramOutcomeFormDialog({
  open,
  onOpenChange,
  title,
  frameworks,
  initial,
  onSubmit,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  frameworks: AccreditationFramework[]
  initial: ProgramOutcome | null
  onSubmit: (body: Record<string, unknown>) => Promise<void>
}) {
  const frameworkPoOptions = useAllFrameworkPOOptions(frameworks)

  const fields: EntityField[] = [
    { name: 'code', label: 'Code', type: 'text', placeholder: 'e.g. PO1' },
    { name: 'title', label: 'Title', type: 'text' },
    { name: 'statement', label: 'Statement', type: 'textarea' },
    { name: 'sequence', label: 'Sequence', type: 'number' },
    {
      name: 'framework_po_id',
      label: 'Linked framework PO (optional)',
      type: 'select',
      description:
        'Explicitly link this program outcome to a framework outcome slot, or leave unlinked. Never auto-matched by wording.',
      options: frameworkPoOptions,
    },
  ]

  return (
    <EntityFormDialog
      open={open}
      onOpenChange={onOpenChange}
      title={title}
      fields={fields}
      schema={z.object({
        code: z.string().min(1, 'Code is required').max(20),
        title: z.string().optional(),
        statement: z.string().min(1, 'Statement is required'),
        sequence: z.coerce.number().int(),
        framework_po_id: z.string().optional(),
      })}
      defaultValues={{
        code: initial?.code ?? '',
        title: initial?.title ?? '',
        statement: initial?.statement ?? '',
        sequence: initial?.sequence ?? 1,
        framework_po_id: initial?.framework_po_id ?? '',
      }}
      onSubmit={async (values) => {
        await onSubmit({
          code: values.code,
          title: values.title || null,
          statement: values.statement,
          sequence: values.sequence,
          framework_po_id: values.framework_po_id || null,
        })
      }}
    />
  )
}
