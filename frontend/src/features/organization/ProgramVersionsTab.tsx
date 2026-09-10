import * as React from 'react'
import { ArrowRight, Plus, Settings2, Undo2 } from 'lucide-react'
import { toast } from 'sonner'
import { z } from 'zod'

import { useAuth } from '@/features/auth/useAuth'
import type { AcademicYear, Program, ProgramVersion } from '@/features/organization/types'
import { Button } from '@/components/ui/button'
import { ConfirmAction } from '@/components/confirm-action'
import { DataTable, type DataTableColumn } from '@/components/data-table'
import { EntityFormDialog, type EntityField } from '@/components/entity-form-dialog'
import { RecordDetailSheet } from '@/components/record-detail-sheet'
import { StatusBadge, WORKFLOW_NEXT, type WorkflowStatus } from '@/components/status-badge'
import { useEntityAction, useEntityCreate, useEntityList, useEntityUpdate } from '@/lib/crud-hooks'
import { ApiError } from '@/lib/api-client'

const configSchema = z.object({
  po_definition_method: z.enum(['direct', 'indicator_based']),
  peo_numbering_style: z.string().min(1).max(20),
  po_numbering_style: z.string().min(1).max(20),
})

const schema = z.object({
  program_id: z.string().min(1, 'Program is required'),
  version_label: z.string().min(1, 'Version label is required').max(50),
  effective_academic_year_id: z.string().min(1, 'Academic year is required'),
})

export function ProgramVersionsTab() {
  const { hasPermission } = useAuth()
  const canManage = hasPermission('program.manage')
  const canApprove = hasPermission('program.approve')
  const [dialogOpen, setDialogOpen] = React.useState(false)
  const [viewVersion, setViewVersion] = React.useState<ProgramVersion | null>(null)
  const [configVersion, setConfigVersion] = React.useState<ProgramVersion | null>(null)

  const { data: programs } = useEntityList<Program>(['org', 'programs'], '/org/programs')
  const { data: years } = useEntityList<AcademicYear>(
    ['org', 'academic-years'],
    '/org/academic-years',
  )
  const { data, isLoading, error } = useEntityList<ProgramVersion>(
    ['org', 'program-versions'],
    '/org/program-versions',
  )
  const create = useEntityCreate<Record<string, unknown>, ProgramVersion>(
    '/org/program-versions',
    [['org', 'program-versions']],
  )
  const advance = useEntityAction<ProgramVersion>(
    (id) => `/org/program-versions/${id}/advance`,
    [['org', 'program-versions']],
  )
  const unpublish = useEntityAction<ProgramVersion>(
    (id) => `/org/program-versions/${id}/unpublish`,
    [['org', 'program-versions']],
  )
  const updateConfig = useEntityUpdate<Record<string, unknown>, ProgramVersion>(
    (id) => `/curriculum/program-versions/${id}/framework-config`,
    [['org', 'program-versions']],
  )

  const programById = React.useMemo(() => new Map((programs ?? []).map((p) => [p.id, p])), [programs])
  const yearById = React.useMemo(() => new Map((years ?? []).map((y) => [y.id, y])), [years])

  const fields: EntityField[] = [
    {
      name: 'program_id',
      label: 'Program',
      type: 'select',
      options: (programs ?? []).map((p) => ({ label: `${p.name} (${p.code})`, value: p.id })),
    },
    { name: 'version_label', label: 'Version label', type: 'text', placeholder: 'e.g. 2024-A' },
    {
      name: 'effective_academic_year_id',
      label: 'Effective academic year',
      type: 'select',
      options: (years ?? []).map((y) => ({ label: y.label, value: y.id })),
    },
  ]

  const columns: DataTableColumn<ProgramVersion>[] = [
    {
      key: 'program',
      header: 'Program',
      render: (r) => programById.get(r.program_id)?.name ?? '—',
    },
    { key: 'version_label', header: 'Version', render: (r) => r.version_label },
    {
      key: 'year',
      header: 'Effective year',
      render: (r) => yearById.get(r.effective_academic_year_id)?.label ?? '—',
    },
    { key: 'status', header: 'Status', render: (r) => <StatusBadge status={r.status} /> },
  ]

  return (
    <div className="flex flex-col gap-4">
      <div className="flex justify-end">
        {canManage && (
          <Button size="sm" onClick={() => setDialogOpen(true)}>
            <Plus className="size-4" /> New program version
          </Button>
        )}
      </div>

      <DataTable
        data={data}
        columns={columns}
        rowKey={(r) => r.id}
        isLoading={isLoading}
        error={error}
        searchable
        searchPlaceholder="Search versions…"
        emptyMessage="No program versions yet."
        onRowClick={(r) => setViewVersion(r)}
        actions={(r) => {
          const next = WORKFLOW_NEXT[r.status as WorkflowStatus]
          return (
            <div className="flex items-center justify-end gap-1.5">
              {canManage && (
                <Button
                  size="icon"
                  variant="ghost"
                  aria-label="Edit framework configuration"
                  onClick={(e) => {
                    e.stopPropagation()
                    setConfigVersion(r)
                  }}
                >
                  <Settings2 className="size-3.5" />
                </Button>
              )}
              {canApprove && r.status === 'published' && (
                <ConfirmAction
                  trigger={
                    <Button size="sm" variant="outline" onClick={(e) => e.stopPropagation()}>
                      <Undo2 className="size-3.5" /> Unpublish
                    </Button>
                  }
                  title={`Unpublish ${r.version_label}?`}
                  description="Moves this curriculum back to draft. It stops being the officially published version until republished — spec §23: never a silent edit of a published curriculum."
                  confirmLabel="Unpublish"
                  variant="destructive"
                  onConfirm={async () => {
                    try {
                      await unpublish.mutateAsync(r.id)
                      toast.success(`${r.version_label} unpublished`)
                    } catch (err) {
                      toast.error(err instanceof ApiError ? err.detail : 'Unable to unpublish.')
                    }
                  }}
                />
              )}
              {canApprove && next && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={async (e) => {
                    e.stopPropagation()
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
              )}
            </div>
          )
        }}
      />

      {viewVersion && (
        <RecordDetailSheet
          open={Boolean(viewVersion)}
          onOpenChange={(open) => !open && setViewVersion(null)}
          title={viewVersion.version_label}
          subtitle={programById.get(viewVersion.program_id)?.name}
          badge={<StatusBadge status={viewVersion.status} />}
          fields={[
            { label: 'Program', value: programById.get(viewVersion.program_id)?.name ?? '—' },
            {
              label: 'Effective year',
              value: yearById.get(viewVersion.effective_academic_year_id)?.label ?? '—',
            },
            { label: 'Status', value: viewVersion.status },
            {
              label: 'PO definition method',
              value: viewVersion.po_definition_method === 'indicator_based' ? 'Indicator-Based' : 'Direct',
            },
            { label: 'PEO numbering style', value: viewVersion.peo_numbering_style },
            { label: 'PO numbering style', value: viewVersion.po_numbering_style },
          ]}
        />
      )}

      <EntityFormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        title="New program version"
        description={(programs ?? []).length === 0 ? 'Create a program first.' : undefined}
        fields={fields}
        schema={schema}
        defaultValues={{ program_id: '', version_label: '', effective_academic_year_id: '' }}
        onSubmit={async (values) => {
          try {
            await create.mutateAsync(values)
            toast.success('Program version created')
          } catch (err) {
            throw err instanceof ApiError ? err : new ApiError('Unable to create program version.')
          }
        }}
      />

      {configVersion && (
        <EntityFormDialog
          open={Boolean(configVersion)}
          onOpenChange={(open) => !open && setConfigVersion(null)}
          title={`Framework configuration — ${configVersion.version_label}`}
          description="Direct vs Indicator-Based drives whether course outcomes map to Program Outcomes or Performance Indicators (spec §21)."
          fields={[
            {
              name: 'po_definition_method',
              label: 'PO definition method',
              type: 'select',
              options: [
                { label: 'Direct', value: 'direct' },
                { label: 'Indicator-Based', value: 'indicator_based' },
              ],
            },
            { name: 'peo_numbering_style', label: 'PEO numbering style', type: 'text', placeholder: 'e.g. numeric' },
            { name: 'po_numbering_style', label: 'PO numbering style', type: 'text', placeholder: 'e.g. numeric' },
          ]}
          schema={configSchema}
          defaultValues={{
            po_definition_method: configVersion.po_definition_method,
            peo_numbering_style: configVersion.peo_numbering_style,
            po_numbering_style: configVersion.po_numbering_style,
          }}
          onSubmit={async (values) => {
            try {
              await updateConfig.mutateAsync({ id: configVersion.id, body: values })
              toast.success('Framework configuration updated')
            } catch (err) {
              throw err instanceof ApiError ? err : new ApiError('Unable to update configuration.')
            }
          }}
        />
      )}
    </div>
  )
}
