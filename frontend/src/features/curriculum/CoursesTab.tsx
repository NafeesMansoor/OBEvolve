import * as React from 'react'
import { Plus } from 'lucide-react'
import { toast } from 'sonner'
import { z } from 'zod'

import { useAuth } from '@/features/auth/useAuth'
import type { Department } from '@/features/organization/types'
import type { Course } from '@/features/curriculum/types'
import { ApiError } from '@/lib/api-client'
import { useEntityCreate, useEntityList, useEntityUpdate } from '@/lib/crud-hooks'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { DataTable, type DataTableColumn } from '@/components/data-table'
import { EntityFormDialog, type EntityField } from '@/components/entity-form-dialog'

const schema = z.object({
  department_id: z.string().min(1, 'Department is required'),
  code: z.string().min(1, 'Code is required').max(50),
  title: z.string().min(1, 'Title is required').max(255),
  description: z.string().optional(),
  credits: z.coerce.number().min(0, 'Credits must be 0 or more'),
  contact_hours: z.union([z.coerce.number().int(), z.literal('')]).optional(),
  course_type: z.string().optional(),
})

/** 127 real courses live in ulab-cse — DataTable's built-in search box keeps
 * this usable without server-side pagination (the backend list endpoint has
 * none — app/api/v1/endpoints/curriculum.py list_courses). */
export function CoursesTab() {
  const { hasPermission } = useAuth()
  const canManage = hasPermission('outcome.create')
  const [createOpen, setCreateOpen] = React.useState(false)
  const [editCourse, setEditCourse] = React.useState<Course | null>(null)

  const { data: departments } = useEntityList<Department>(
    ['org', 'departments'],
    '/org/departments',
  )
  const { data, isLoading, error } = useEntityList<Course>(
    ['curriculum', 'courses'],
    '/curriculum/courses',
  )
  const create = useEntityCreate<Record<string, unknown>, Course>('/curriculum/courses', [
    ['curriculum', 'courses'],
  ])
  const update = useEntityUpdate<Record<string, unknown>, Course>(
    (id) => `/curriculum/courses/${id}`,
    [['curriculum', 'courses']],
  )

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
    { name: 'code', label: 'Code', type: 'text' },
    { name: 'title', label: 'Title', type: 'text' },
    { name: 'description', label: 'Description', type: 'textarea' },
    { name: 'credits', label: 'Credits', type: 'number', step: '0.5' },
    { name: 'contact_hours', label: 'Contact hours', type: 'number' },
    { name: 'course_type', label: 'Course type', type: 'text', placeholder: 'e.g. core, elective' },
  ]

  const editFields: EntityField[] = fields.filter((f) => f.name !== 'department_id')

  const columns: DataTableColumn<Course>[] = [
    { key: 'code', header: 'Code', render: (r) => r.code, searchValue: (r) => r.code },
    { key: 'title', header: 'Title', render: (r) => r.title, searchValue: (r) => r.title },
    {
      key: 'department',
      header: 'Department',
      render: (r) => deptById.get(r.department_id)?.code ?? '—',
    },
    { key: 'credits', header: 'Credits', render: (r) => r.credits },
    { key: 'course_type', header: 'Type', render: (r) => r.course_type ?? '—' },
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
          <Button size="sm" onClick={() => setCreateOpen(true)}>
            <Plus className="size-4" /> New course
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
        searchPlaceholder="Search by code or title…"
        emptyMessage="No courses yet."
        pageSize={20}
        onRowClick={canManage ? (r) => setEditCourse(r) : undefined}
      />

      <EntityFormDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        title="New course"
        fields={fields}
        schema={schema}
        defaultValues={{
          department_id: '',
          code: '',
          title: '',
          description: '',
          credits: '',
          contact_hours: '',
          course_type: '',
        }}
        onSubmit={async (values) => {
          try {
            await create.mutateAsync({
              department_id: values.department_id,
              code: values.code,
              title: values.title,
              description: values.description || null,
              credits: values.credits,
              contact_hours: values.contact_hours === '' ? null : values.contact_hours,
              course_type: values.course_type || null,
            })
            toast.success('Course created')
          } catch (err) {
            throw err instanceof ApiError ? err : new ApiError('Unable to create course.')
          }
        }}
      />

      {editCourse && (
        <EntityFormDialog
          open={Boolean(editCourse)}
          onOpenChange={(open) => !open && setEditCourse(null)}
          title={`Edit ${editCourse.code}`}
          fields={editFields}
          schema={schema.omit({ department_id: true })}
          defaultValues={{
            code: editCourse.code,
            title: editCourse.title,
            description: editCourse.description ?? '',
            credits: editCourse.credits,
            contact_hours: editCourse.contact_hours ?? '',
            course_type: editCourse.course_type ?? '',
          }}
          onSubmit={async (values) => {
            try {
              await update.mutateAsync({
                id: editCourse.id,
                body: {
                  code: values.code,
                  title: values.title,
                  description: values.description || null,
                  credits: values.credits,
                  contact_hours: values.contact_hours === '' ? null : values.contact_hours,
                  course_type: values.course_type || null,
                },
              })
              toast.success('Course updated')
            } catch (err) {
              throw err instanceof ApiError ? err : new ApiError('Unable to update course.')
            }
          }}
        />
      )}
    </div>
  )
}
