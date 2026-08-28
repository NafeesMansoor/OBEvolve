import * as React from 'react'
import { Plus } from 'lucide-react'
import { toast } from 'sonner'
import { z } from 'zod'

import { useAuth } from '@/features/auth/useAuth'
import type { Campus, Department, School } from '@/features/organization/types'
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
const ALL_SCHOOLS = '__all__'

const schema = z.object({
  school_id: z.string().min(1, 'School is required'),
  name: z.string().min(1, 'Name is required').max(255),
  code: z.string().min(1, 'Code is required').max(50),
})

export function DepartmentsTab() {
  const { hasPermission } = useAuth()
  const canManage = hasPermission('org.manage')
  const [dialogOpen, setDialogOpen] = React.useState(false)
  const [viewDept, setViewDept] = React.useState<Department | null>(null)
  const [campusFilter, setCampusFilter] = React.useState(ALL_CAMPUSES)
  const [schoolFilter, setSchoolFilter] = React.useState(ALL_SCHOOLS)

  const { data: campuses } = useEntityList<Campus>(['org', 'campuses'], '/org/campuses')
  const { data: schools } = useEntityList<School>(['org', 'schools'], '/org/schools')
  const { data, isLoading, error } = useEntityList<Department>(
    ['org', 'departments'],
    '/org/departments',
  )
  const create = useEntityCreate<Record<string, unknown>, Department>('/org/departments', [
    ['org', 'departments'],
  ])

  const schoolById = React.useMemo(() => new Map((schools ?? []).map((s) => [s.id, s])), [schools])
  const campusById = React.useMemo(() => new Map((campuses ?? []).map((c) => [c.id, c])), [campuses])

  // School filter options narrow to the selected campus — cascading, but
  // switching campus doesn't reset an already-chosen school unless it no
  // longer belongs there (falls back to "All schools" instead of silently
  // showing a school from a different campus).
  const schoolsInCampus = React.useMemo(
    () =>
      campusFilter === ALL_CAMPUSES
        ? (schools ?? [])
        : (schools ?? []).filter((s) => s.campus_id === campusFilter),
    [schools, campusFilter],
  )
  if (schoolFilter !== ALL_SCHOOLS && !schoolsInCampus.some((s) => s.id === schoolFilter)) {
    setSchoolFilter(ALL_SCHOOLS)
  }

  const filteredData = React.useMemo(() => {
    let rows = data ?? []
    if (schoolFilter !== ALL_SCHOOLS) {
      rows = rows.filter((d) => d.school_id === schoolFilter)
    } else if (campusFilter !== ALL_CAMPUSES) {
      const schoolIdsInCampus = new Set(schoolsInCampus.map((s) => s.id))
      rows = rows.filter((d) => schoolIdsInCampus.has(d.school_id))
    }
    return rows
  }, [data, schoolFilter, campusFilter, schoolsInCampus])

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
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap gap-2">
          <div className="w-full sm:w-56">
            <Select
              value={campusFilter}
              onValueChange={(v) => {
                setCampusFilter(v)
                setSchoolFilter(ALL_SCHOOLS)
              }}
            >
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
          <div className="w-full sm:w-56">
            <Select value={schoolFilter} onValueChange={setSchoolFilter}>
              <SelectTrigger>
                <SelectValue placeholder="Filter by school" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL_SCHOOLS}>All schools</SelectItem>
                {schoolsInCampus.map((s) => (
                  <SelectItem key={s.id} value={s.id}>
                    {s.name} ({s.code})
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
        {canManage && (
          <Button size="sm" onClick={() => setDialogOpen(true)}>
            <Plus className="size-4" /> New department
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
        searchPlaceholder="Search departments…"
        emptyMessage="No departments yet."
        onRowClick={(r) => setViewDept(r)}
      />

      {viewDept && (
        <RecordDetailSheet
          open={Boolean(viewDept)}
          onOpenChange={(open) => !open && setViewDept(null)}
          title={viewDept.name}
          badge={
            <Badge variant={viewDept.is_active ? 'secondary' : 'outline'} className="font-normal">
              {viewDept.is_active ? 'Active' : 'Inactive'}
            </Badge>
          }
          fields={[
            { label: 'Code', value: viewDept.code },
            { label: 'School', value: schoolById.get(viewDept.school_id)?.name ?? '—' },
            {
              label: 'Campus',
              value: (() => {
                const school = schoolById.get(viewDept.school_id)
                return school ? (campusById.get(school.campus_id)?.name ?? '—') : '—'
              })(),
            },
            { label: 'Status', value: viewDept.is_active ? 'Active' : 'Inactive' },
          ]}
        />
      )}

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
