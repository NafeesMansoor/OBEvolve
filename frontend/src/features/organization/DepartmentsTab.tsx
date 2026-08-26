import * as React from 'react'
import { Plus } from 'lucide-react'
import { toast } from 'sonner'
import { z } from 'zod'

import { useAuth } from '@/features/auth/useAuth'
import type { Department, School } from '@/features/organization/types'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { DataTable, type DataTableColumn } from '@/components/data-table'
import { EntityFormDialog, type EntityField } from '@/components/entity-form-dialog'
import { useEntityCreate, useEntityList } from '@/lib/crud-hooks'
import { ApiError } from '@/lib/api-client'

const schema = z.object({
  school_id: z.string().min(1, 'School is required'),
  name: z.string().min(1, 'Name is required').max(255),
  code: z.string().min(1, 'Code is required').max(50),
})

export function DepartmentsTab() {
  const { hasPermission } = useAuth()
  const canManage = hasPermission('org.manage')
  const [dialogOpen, setDialogOpen] = React.useState(false)

  const { data: schools } = useEntityList<School>(['org', 'schools'], '/org/schools')
  const { data, isLoading, error } = useEntityList<Department>(
    ['org', 'departments'],
    '/org/departments',
  )
  const create = useEntityCreate<Record<string, unknown>, Department>('/org/departments', [
    ['org', 'departments'],
  ])

  const schoolById = React.useMemo(() => new Map((schools ?? []).map((s) => [s.id, s])), [schools])

  const fields: EntityField[] = [
    {
      name: 'school_id',
      label: 'School',
      type: 'select',
      options: (schools ?? []).map((s) => ({ label: `${s.name} (${s.code})`, value: s.id })),
    },
    { name: 'name', label: 'Name', type: 'text' },
    { name: 'code', label: 'Code', type: 'text' },
  ]

  const columns: DataTableColumn<Department>[] = [
    { key: 'name', header: 'Name', render: (r) => r.name, searchValue: (r) => r.name },
    { key: 'code', header: 'Code', render: (r) => r.code, searchValue: (r) => r.code },
    { key: 'school', header: 'School', render: (r) => schoolById.get(r.school_id)?.name ?? '—' },
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
            <Plus className="size-4" /> New department
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
        searchPlaceholder="Search departments…"
        emptyMessage="No departments yet."
      />

      <EntityFormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        title="New department"
        description={(schools ?? []).length === 0 ? 'Create a school first.' : undefined}
        fields={fields}
        schema={schema}
        defaultValues={{ school_id: '', name: '', code: '' }}
        onSubmit={async (values) => {
          try {
            await create.mutateAsync(values)
            toast.success('Department created')
          } catch (err) {
            throw err instanceof ApiError ? err : new ApiError('Unable to create department.')
          }
        }}
      />
    </div>
  )
}
