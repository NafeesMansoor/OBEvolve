import * as React from 'react'
import { Plus } from 'lucide-react'
import { toast } from 'sonner'
import { z } from 'zod'

import { useAuth } from '@/features/auth/useAuth'
import type { Campus, School } from '@/features/organization/types'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { DataTable, type DataTableColumn } from '@/components/data-table'
import { EntityFormDialog, type EntityField } from '@/components/entity-form-dialog'
import { RecordDetailSheet } from '@/components/record-detail-sheet'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useEntityCreate, useEntityList } from '@/lib/crud-hooks'
import { ApiError } from '@/lib/api-client'

const ALL_CAMPUSES = '__all__'

const schema = z.object({
  campus_id: z.string().min(1, 'Campus is required'),
  name: z.string().min(1, 'Name is required').max(255),
  code: z.string().min(1, 'Code is required').max(50),
})

export function SchoolsTab() {
  const { hasPermission } = useAuth()
  const canManage = hasPermission('org.manage')
  const [dialogOpen, setDialogOpen] = React.useState(false)
  const [campusFilter, setCampusFilter] = React.useState(ALL_CAMPUSES)
  const [viewSchool, setViewSchool] = React.useState<School | null>(null)

  const { data: campuses } = useEntityList<Campus>(['org', 'campuses'], '/org/campuses')
  const { data, isLoading, error } = useEntityList<School>(['org', 'schools'], '/org/schools')
  const filteredData = React.useMemo(
    () => (campusFilter === ALL_CAMPUSES ? data : data?.filter((s) => s.campus_id === campusFilter)),
    [data, campusFilter],
  )
  const create = useEntityCreate<Record<string, unknown>, School>('/org/schools', [
    ['org', 'schools'],
  ])

  const campusById = React.useMemo(
    () => new Map((campuses ?? []).map((c) => [c.id, c])),
    [campuses],
  )

  const fields: EntityField[] = [
    {
      name: 'campus_id',
      label: 'Campus',
      type: 'select',
      options: (campuses ?? []).map((c) => ({ label: `${c.name} (${c.code})`, value: c.id })),
    },
    { name: 'name', label: 'Name', type: 'text' },
    { name: 'code', label: 'Code', type: 'text' },
  ]

  const columns: DataTableColumn<School>[] = [
    { key: 'name', header: 'Name', render: (r) => r.name, searchValue: (r) => r.name },
    { key: 'code', header: 'Code', render: (r) => r.code, searchValue: (r) => r.code },
    { key: 'campus', header: 'Campus', render: (r) => campusById.get(r.campus_id)?.name ?? '—' },
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
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="w-full sm:w-64">
          <Select value={campusFilter} onValueChange={setCampusFilter}>
            <SelectTrigger>
              <SelectValue placeholder="Filter by campus" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={ALL_CAMPUSES}>All campuses</SelectItem>
              {(campuses ?? []).map((c) => (
                <SelectItem key={c.id} value={c.id}>
                  {c.name} ({c.code})
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        {canManage && (
          <Button size="sm" onClick={() => setDialogOpen(true)}>
            <Plus className="size-4" /> New school
          </Button>
        )}
      </div>

      <DataTable
        data={filteredData}
        columns={columns}
        rowKey={(r) => r.id}
        isLoading={isLoading}
        error={error}
        searchable
        searchPlaceholder="Search schools…"
        emptyMessage="No schools yet."
        onRowClick={(r) => setViewSchool(r)}
      />

      {viewSchool && (
        <RecordDetailSheet
          open={Boolean(viewSchool)}
          onOpenChange={(open) => !open && setViewSchool(null)}
          title={viewSchool.name}
          badge={
            <Badge variant={viewSchool.is_active ? 'secondary' : 'outline'} className="font-normal">
              {viewSchool.is_active ? 'Active' : 'Inactive'}
            </Badge>
          }
          fields={[
            { label: 'Code', value: viewSchool.code },
            { label: 'Campus', value: campusById.get(viewSchool.campus_id)?.name ?? '—' },
            { label: 'Status', value: viewSchool.is_active ? 'Active' : 'Inactive' },
          ]}
        />
      )}

      <EntityFormDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        title="New school"
        description={(campuses ?? []).length === 0 ? 'Create a campus first.' : undefined}
        fields={fields}
        schema={schema}
        defaultValues={{ campus_id: '', name: '', code: '' }}
        onSubmit={async (values) => {
          try {
            await create.mutateAsync(values)
            toast.success('School created')
          } catch (err) {
            throw err instanceof ApiError ? err : new ApiError('Unable to create school.')
          }
        }}
      />
    </div>
  )
}
