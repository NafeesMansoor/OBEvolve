import * as React from 'react'
import { Copy, Plus } from 'lucide-react'
import { toast } from 'sonner'
import { z } from 'zod'

import { useAuth } from '@/features/auth/useAuth'
import type { Department } from '@/features/organization/types'
import { COURSE_TYPE_CATEGORIES, categorizeCourseType } from '@/features/curriculum/course-type-taxonomy'
import type { Course } from '@/features/curriculum/types'
import { ApiError } from '@/lib/api-client'
import { useEntityCreate, useEntityList, useEntityUpdate } from '@/lib/crud-hooks'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { DataTable, type DataTableColumn } from '@/components/data-table'
import { EntityFormDialog, type EntityField } from '@/components/entity-form-dialog'
import { RecordDetailSheet } from '@/components/record-detail-sheet'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

const ALL_TYPES = 'All'

const NO_CO_OFFERED = '__none__'

const schema = z.object({
  department_id: z.string().min(1, 'Department is required'),
  code: z.string().min(1, 'Code is required').max(50),
  title: z.string().min(1, 'Title is required').max(255),
  description: z.string().optional(),
  credits: z.coerce.number().min(0, 'Credits must be 0 or more'),
  contact_hours: z.union([z.coerce.number().int(), z.literal('')]).optional(),
  course_type: z.string().optional(),
  co_offered_with_id: z.string().optional(),
})

type CourseFormDefaults = {
  department_id: string
  code: string
  title: string
  description: string
  credits: string | number
  contact_hours: string | number
  course_type: string
  co_offered_with_id: string
}

const BLANK_DEFAULTS: CourseFormDefaults = {
  department_id: '',
  code: '',
  title: '',
  description: '',
  credits: '',
  contact_hours: '',
  course_type: '',
  co_offered_with_id: NO_CO_OFFERED,
}

/** 127 real courses live in ulab-cse — DataTable's built-in search box keeps
 * this usable without server-side pagination (the backend list endpoint has
 * none — app/api/v1/endpoints/curriculum.py list_courses). */
export function CoursesTab() {
  const { hasPermission } = useAuth()
  const canManage = hasPermission('outcome.create')
  const [createOpen, setCreateOpen] = React.useState(false)
  const [createDefaults, setCreateDefaults] = React.useState<CourseFormDefaults>(BLANK_DEFAULTS)
  const [editCourse, setEditCourse] = React.useState<Course | null>(null)
  const [viewCourse, setViewCourse] = React.useState<Course | null>(null)

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
  const courseById = React.useMemo(
    () => new Map((data ?? []).map((c) => [c.id, c])),
    [data],
  )

  const [typeTab, setTypeTab] = React.useState(ALL_TYPES)
  const countByCategory = React.useMemo(() => {
    const counts = new Map<string, number>()
    for (const c of data ?? []) {
      const cat = categorizeCourseType(c.course_type)
      counts.set(cat, (counts.get(cat) ?? 0) + 1)
    }
    return counts
  }, [data])
  const visibleCategories = COURSE_TYPE_CATEGORIES.filter((cat) => (countByCategory.get(cat) ?? 0) > 0)
  const filteredByType = React.useMemo(
    () =>
      typeTab === ALL_TYPES
        ? data
        : data?.filter((c) => categorizeCourseType(c.course_type) === typeTab),
    [data, typeTab],
  )

  function courseOptions(excludeId?: string) {
    return [
      { label: 'None', value: NO_CO_OFFERED },
      ...(data ?? [])
        .filter((c) => c.id !== excludeId)
        .map((c) => ({ label: `${c.code} — ${c.title}`, value: c.id })),
    ]
  }

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
    {
      name: 'co_offered_with_id',
      label: 'Co-offered with',
      type: 'select',
      options: courseOptions(),
      description: 'Link this to another course it’s jointly taught/listed with, if any.',
    },
  ]

  const editFields: EntityField[] = fields
    .filter((f) => f.name !== 'department_id')
    .map((f) =>
      f.name === 'co_offered_with_id'
        ? { ...f, options: courseOptions(editCourse?.id) }
        : f,
    )

  function openDuplicate(source: Course) {
    setCreateDefaults({
      department_id: source.department_id,
      code: '',
      title: `${source.title} (copy)`,
      description: source.description ?? '',
      credits: source.credits,
      contact_hours: source.contact_hours ?? '',
      course_type: source.course_type ?? '',
      co_offered_with_id: NO_CO_OFFERED,
    })
    setCreateOpen(true)
  }

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
      key: 'co_offered',
      header: 'Co-offered with',
      render: (r) =>
        r.co_offered_with_id ? (courseById.get(r.co_offered_with_id)?.code ?? '—') : '—',
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
          <Button
            size="sm"
            onClick={() => {
              setCreateDefaults(BLANK_DEFAULTS)
              setCreateOpen(true)
            }}
          >
            <Plus className="size-4" /> New course
          </Button>
        )}
      </div>

      <Tabs value={typeTab} onValueChange={setTypeTab}>
        <TabsList className="flex-wrap">
          <TabsTrigger value={ALL_TYPES}>All ({data?.length ?? 0})</TabsTrigger>
          {visibleCategories.map((cat) => (
            <TabsTrigger key={cat} value={cat}>
              {cat} ({countByCategory.get(cat)})
            </TabsTrigger>
          ))}
        </TabsList>
        <TabsContent value={typeTab}>
          <DataTable
            data={filteredByType}
            columns={columns}
            rowKey={(r) => r.id}
            isLoading={isLoading}
            error={error}
            searchable
            searchPlaceholder="Search by code or title…"
            emptyMessage="No courses in this category."
            pageSize={20}
            onRowClick={(r) => setViewCourse(r)}
            actions={
              canManage
                ? (r) => (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation()
                        openDuplicate(r)
                      }}
                      title="Duplicate this course as a starting point for a new one"
                    >
                      <Copy className="size-3.5" /> Duplicate
                    </Button>
                  )
                : undefined
            }
          />
        </TabsContent>
      </Tabs>

      <EntityFormDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        title="New course"
        fields={fields}
        schema={schema}
        defaultValues={createDefaults}
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
              co_offered_with_id:
                values.co_offered_with_id === NO_CO_OFFERED ? null : values.co_offered_with_id,
            })
            toast.success('Course created')
          } catch (err) {
            throw err instanceof ApiError ? err : new ApiError('Unable to create course.')
          }
        }}
      />

      {viewCourse && (
        <RecordDetailSheet
          open={Boolean(viewCourse)}
          onOpenChange={(open) => !open && setViewCourse(null)}
          title={`${viewCourse.code} — ${viewCourse.title}`}
          subtitle={deptById.get(viewCourse.department_id)?.name}
          badge={
            <Badge variant={viewCourse.is_active ? 'secondary' : 'outline'} className="font-normal">
              {viewCourse.is_active ? 'Active' : 'Inactive'}
            </Badge>
          }
          fields={[
            { label: 'Code', value: viewCourse.code },
            { label: 'Credits', value: viewCourse.credits },
            { label: 'Department', value: deptById.get(viewCourse.department_id)?.name ?? '—' },
            { label: 'Contact hours', value: viewCourse.contact_hours ?? '—' },
            { label: 'Course type', value: viewCourse.course_type ?? '—' },
            {
              label: 'Co-offered with',
              value: viewCourse.co_offered_with_id
                ? (courseById.get(viewCourse.co_offered_with_id)?.code ?? '—')
                : '—',
            },
            { label: 'Description', value: viewCourse.description ?? '—', full: true },
          ]}
          onEdit={
            canManage
              ? () => {
                  setEditCourse(viewCourse)
                  setViewCourse(null)
                }
              : undefined
          }
        />
      )}

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
            co_offered_with_id: editCourse.co_offered_with_id ?? NO_CO_OFFERED,
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
                  co_offered_with_id:
                    values.co_offered_with_id === NO_CO_OFFERED ? null : values.co_offered_with_id,
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
