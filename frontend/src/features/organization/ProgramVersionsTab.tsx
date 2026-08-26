import * as React from 'react'
import { ArrowRight, Plus } from 'lucide-react'
import { toast } from 'sonner'
import { z } from 'zod'

import { useAuth } from '@/features/auth/useAuth'
import type { AcademicYear, Program, ProgramVersion } from '@/features/organization/types'
import { Button } from '@/components/ui/button'
import { DataTable, type DataTableColumn } from '@/components/data-table'
import { EntityFormDialog, type EntityField } from '@/components/entity-form-dialog'
import { StatusBadge, WORKFLOW_NEXT, type WorkflowStatus } from '@/components/status-badge'
import { useEntityAction, useEntityCreate, useEntityList } from '@/lib/crud-hooks'
import { ApiError } from '@/lib/api-client'

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
    </div>
  )
}
