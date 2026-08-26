import * as React from 'react'
import { Plus } from 'lucide-react'
import { toast } from 'sonner'
import { z } from 'zod'

import { useAuth } from '@/features/auth/useAuth'
import type { Campus } from '@/features/organization/types'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { DataTable, type DataTableColumn } from '@/components/data-table'
import { EntityFormDialog, type EntityField } from '@/components/entity-form-dialog'
import { useEntityCreate, useEntityList } from '@/lib/crud-hooks'
import { ApiError } from '@/lib/api-client'

const schema = z.object({
  name: z.string().min(1, 'Name is required').max(255),
  code: z.string().min(1, 'Code is required').max(50),
  address: z.string().optional(),
})

const fields: EntityField[] = [
  { name: 'name', label: 'Name', type: 'text' },
  { name: 'code', label: 'Code', type: 'text' },
  { name: 'address', label: 'Address', type: 'textarea' },
]

export function CampusesTab() {
  const { hasPermission } = useAuth()
  const canManage = hasPermission('org.manage')
  const [dialogOpen, setDialogOpen] = React.useState(false)

  const { data, isLoading, error } = useEntityList<Campus>(['org', 'campuses'], '/org/campuses')
  const create = useEntityCreate<Record<string, unknown>, Campus>('/org/campuses', [
    ['org', 'campuses'],
  ])

  const columns: DataTableColumn<Campus>[] = [
    { key: 'name', header: 'Name', render: (r) => r.name, searchValue: (r) => r.name },
    { key: 'code', header: 'Code', render: (r) => r.code, searchValue: (r) => r.code },
    { key: 'address', header: 'Address', render: (r) => r.address ?? '—' },
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
            <Plus className="size-4" /> New campus
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
        searchPlaceholder="Search campuses…"
        emptyMessage="No campuses yet."
      />

      <EntityFormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        title="New campus"
        fields={fields}
        schema={schema}
        defaultValues={{ name: '', code: '', address: '' }}
        onSubmit={async (values) => {
          try {
            await create.mutateAsync({
              name: values.name,
              code: values.code,
              address: values.address || null,
            })
            toast.success('Campus created')
          } catch (err) {
            throw err instanceof ApiError ? err : new ApiError('Unable to create campus.')
          }
        }}
      />
    </div>
  )
}
