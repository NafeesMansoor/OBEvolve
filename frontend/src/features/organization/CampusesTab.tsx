import * as React from 'react'
import { Pencil, Plus } from 'lucide-react'
import { toast } from 'sonner'
import { z } from 'zod'

import { useAuth } from '@/features/auth/useAuth'
import type { Campus } from '@/features/organization/types'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { DataTable, type DataTableColumn } from '@/components/data-table'
import { EntityFormDialog, type EntityField } from '@/components/entity-form-dialog'
import { RecordDetailSheet } from '@/components/record-detail-sheet'
import { Switch } from '@/components/ui/switch'
import { useEntityCreate, useEntityList, useEntityUpdate } from '@/lib/crud-hooks'
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
  const [editCampus, setEditCampus] = React.useState<Campus | null>(null)
  const [viewCampus, setViewCampus] = React.useState<Campus | null>(null)

  const { data, isLoading, error } = useEntityList<Campus>(['org', 'campuses'], '/org/campuses')
  const create = useEntityCreate<Record<string, unknown>, Campus>('/org/campuses', [
    ['org', 'campuses'],
  ])
  const update = useEntityUpdate<Record<string, unknown>, Campus>((id) => `/org/campuses/${id}`, [
    ['org', 'campuses'],
  ])

  const toggleActive = async (campus: Campus) => {
    try {
      await update.mutateAsync({ id: campus.id, body: { is_active: !campus.is_active } })
      toast.success(campus.is_active ? 'Campus deactivated' : 'Campus activated')
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Unable to update campus status.')
    }
  }

  const columns: DataTableColumn<Campus>[] = [
    { key: 'name', header: 'Name', render: (r) => r.name, searchValue: (r) => r.name },
    { key: 'code', header: 'Code', render: (r) => r.code, searchValue: (r) => r.code },
    { key: 'address', header: 'Address', render: (r) => r.address ?? '—' },
    {
      key: 'is_active',
      header: 'Status',
      render: (r) =>
        canManage ? (
          <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
            <Switch checked={r.is_active} onCheckedChange={() => toggleActive(r)} />
            <span className="text-xs text-muted-foreground">
              {r.is_active ? 'Active' : 'Inactive'}
            </span>
          </div>
        ) : (
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
        onRowClick={(r) => setViewCampus(r)}
        actions={
          canManage
            ? (r) => (
                <Button
                  size="sm"
                  variant="ghost"
                  aria-label={`Edit ${r.name}`}
                  onClick={() => setEditCampus(r)}
                >
                  <Pencil className="size-4" />
                </Button>
              )
            : undefined
        }
      />

      {viewCampus && (
        <RecordDetailSheet
          open={Boolean(viewCampus)}
          onOpenChange={(open) => !open && setViewCampus(null)}
          title={viewCampus.name}
          badge={
            <Badge variant={viewCampus.is_active ? 'secondary' : 'outline'} className="font-normal">
              {viewCampus.is_active ? 'Active' : 'Inactive'}
            </Badge>
          }
          fields={[
            { label: 'Code', value: viewCampus.code },
            { label: 'Status', value: viewCampus.is_active ? 'Active' : 'Inactive' },
            { label: 'Address', value: viewCampus.address ?? '—', full: true },
          ]}
        />
      )}

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

      {editCampus && (
        <EntityFormDialog
          open={Boolean(editCampus)}
          onOpenChange={(open) => !open && setEditCampus(null)}
          title={`Edit ${editCampus.name}`}
          fields={fields}
          schema={schema}
          defaultValues={{
            name: editCampus.name,
            code: editCampus.code,
            address: editCampus.address ?? '',
          }}
          onSubmit={async (values) => {
            try {
              await update.mutateAsync({
                id: editCampus.id,
                body: {
                  name: values.name,
                  code: values.code,
                  address: values.address || null,
                },
              })
              toast.success('Campus updated')
              setEditCampus(null)
            } catch (err) {
              throw err instanceof ApiError ? err : new ApiError('Unable to update campus.')
            }
          }}
        />
      )}
    </div>
  )
}
