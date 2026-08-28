import * as React from 'react'
import { Plus } from 'lucide-react'
import { toast } from 'sonner'
import { z } from 'zod'

import { useAuth } from '@/features/auth/useAuth'
import type { Department, Program } from '@/features/organization/types'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { DataTable, type DataTableColumn } from '@/components/data-table'
import { EntityFormDialog, type EntityField } from '@/components/entity-form-dialog'
import { RecordDetailSheet } from '@/components/record-detail-sheet'
import { useEntityCreate, useEntityList } from '@/lib/crud-hooks'
import { ApiError } from '@/lib/api-client'

const schema = z.object({
  department_id: z.string().min(1, 'Department is required'),
  name: z.string().min(1, 'Name is required').max(255),
  code: z.string().min(1, 'Code is required').max(50),
  degree_level: z.string().optional(),
})

/** "Admin creates a program" — surfaced prominently since the product spec
 * calls this out explicitly as a required flow. */
export function ProgramsTab() {
  const { hasPermission } = useAuth()
  const canManage = hasPermission('program.manage')
  const [dialogOpen, setDialogOpen] = React.useState(false)
  const [viewProgram, setViewProgram] = React.useState<Program | null>(null)

  const { data: departments } = useEntityList<Department>(
    ['org', 'departments'],
    '/org/departments',
  )
  const { data, isLoading, error } = useEntityList<Program>(
    ['org', 'programs'],
    '/org/programs',
  )
  const create = useEntityCreate<Record<string, unknown>, Program>('/org/programs', [
    ['org', 'programs'],
  ])

  const deptById = React.useMemo(
    () => new Map((departments ?? []).map((d) => [d.id, d])),
    [departments],
  )

  const fields: EntityField[] = [
    {
      name: 'department_id',
      label: 'Department',
      type: 'select',
      options: (departments ?? []).map((d) => ({ label: `${d.name} (${d.code})`, value: d.id })),
    },
    { name: 'name', label: 'Name', type: 'text' },
    { name: 'code', label: 'Code', type: 'text' },
    { name: 'degree_level', label: 'Degree level', type: 'text', placeholder: 'e.g. BSc, MSc' },
  ]

  const columns: DataTableColumn<Program>[] = [
    { key: 'name', header: 'Name', render: (r) => r.name, searchValue: (r) => r.name },
    { key: 'code', header: 'Code', render: (r) => r.code, searchValue: (r) => r.code },
    { key: 'degree_level', header: 'Degree level', render: (r) => r.degree_level ?? '—' },
    {
      key: 'department',
      header: 'Department',
      render: (r) => deptById.get(r.department_id)?.name ?? '—',
    },
    {
      key: 'is_active',
      header: 'Status',
      render: (r) => (
        <Badge variant={r.is_active ? 'secondary' : 'outline'} className="font-normal">
          {r.is_active ? 'Active' : 'Inactive'}
        </Badge>
      ),
    },
  ]

  return (
    <div className="flex flex-col gap-4">
      <div className="flex justify-end">
        {canManage && (
          <Button size="sm" onClick={() => setDialogOpen(true)}>
            <Plus className="size-4" /> New program
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
        searchPlaceholder="Search programs…"
        emptyMessage="No programs yet."
        onRowClick={(r) => setViewProgram(r)}
      />

      {viewProgram && (
        <RecordDetailSheet
          open={Boolean(viewProgram)}
          onOpenChange={(open) => !open && setViewProgram(null)}
          title={viewProgram.name}
          badge={
            <Badge variant={viewProgram.is_active ? 'secondary' : 'outline'} className="font-normal">
              {viewProgram.is_active ? 'Active' : 'Inactive'}
            </Badge>
          }
          fields={[
            { label: 'Code', value: viewProgram.code },
            { label: 'Degree level', value: viewProgram.degree_level ?? '—' },
            { label: 'Department', value: deptById.get(viewProgram.department_id)?.name ?? '—' },
            { label: 'Status', value: viewProgram.is_active ? 'Active' : 'Inactive' },
          ]}
        />
      )}

      <EntityFormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        title="New program"
        description={(departments ?? []).length === 0 ? 'Create a department first.' : undefined}
        fields={fields}
        schema={schema}
        defaultValues={{ department_id: '', name: '', code: '', degree_level: '' }}
        onSubmit={async (values) => {
          try {
            await create.mutateAsync({
              department_id: values.department_id,
              name: values.name,
              code: values.code,
              degree_level: values.degree_level || null,
            })
            toast.success('Program created')
          } catch (err) {
            throw err instanceof ApiError ? err : new ApiError('Unable to create program.')
          }
        }}
      />
    </div>
  )
}
