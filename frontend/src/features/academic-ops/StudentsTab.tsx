import * as React from 'react'
import { GraduationCap, Plus } from 'lucide-react'
import { toast } from 'sonner'
import { z } from 'zod'

import { useAuth } from '@/features/auth/useAuth'
import type { Student } from '@/features/academic-ops/types'
import type { Program, ProgramVersion } from '@/features/organization/types'
import { ApiError } from '@/lib/api-client'
import { useEntityCreate, useEntityList, useEntityUpdate } from '@/lib/crud-hooks'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { DataTable, type DataTableColumn } from '@/components/data-table'
import { EntityFormDialog, type EntityField } from '@/components/entity-form-dialog'

const createSchema = z.object({
  full_name: z.string().min(1, 'Name is required').max(255),
  email: z.string().min(1, 'Email is required').email('Enter a valid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
  student_code: z.string().min(1, 'Student code is required').max(50),
  program_id: z.string().optional(),
  program_version_id: z.string().optional(),
  batch_year: z.union([z.coerce.number().int(), z.literal('')]).optional(),
})

const alignSchema = z.object({
  program_id: z.string().optional(),
  program_version_id: z.string().optional(),
  batch_year: z.union([z.coerce.number().int(), z.literal('')]).optional(),
  status: z.string().optional(),
})

const STATUS_OPTIONS = ['active', 'graduated', 'suspended', 'withdrawn']

/** "Add students" (StudentCreate = a full user + student profile in one
 * step) plus "curriculum alignment" — re-pointing a student at a different
 * program_version_id, called out explicitly in the task brief as something
 * that must be easy to find, not buried. */
export function StudentsTab() {
  const { hasPermission } = useAuth()
  const canManage = hasPermission('student.manage')
  const [createOpen, setCreateOpen] = React.useState(false)
  const [alignStudent, setAlignStudent] = React.useState<Student | null>(null)

  const { data: programs } = useEntityList<Program>(['org', 'programs'], '/org/programs')
  const { data: versions } = useEntityList<ProgramVersion>(
    ['org', 'program-versions'],
    '/org/program-versions',
  )
  const { data, isLoading, error } = useEntityList<Student>(
    ['academic', 'students'],
    '/academic/students',
  )
  const create = useEntityCreate<Record<string, unknown>, Student>('/academic/students', [
    ['academic', 'students'],
  ])
  const update = useEntityUpdate<Record<string, unknown>, Student>(
    (id) => `/academic/students/${id}`,
    [['academic', 'students']],
  )

  const programById = React.useMemo(() => new Map((programs ?? []).map((p) => [p.id, p])), [programs])
  const versionById = React.useMemo(() => new Map((versions ?? []).map((v) => [v.id, v])), [versions])

  const createFields: EntityField[] = [
    { name: 'full_name', label: 'Full name', type: 'text' },
    { name: 'email', label: 'Email', type: 'text' },
    { name: 'password', label: 'Temporary password', type: 'text' },
    { name: 'student_code', label: 'Student code', type: 'text' },
    {
      name: 'program_id',
      label: 'Program',
      type: 'select',
      options: (programs ?? []).map((p) => ({ label: p.name, value: p.id })),
    },
    {
      name: 'program_version_id',
      label: 'Program version',
      type: 'select',
      options: (versions ?? []).map((v) => ({
        label: `${programById.get(v.program_id)?.name ?? '?'} — ${v.version_label}`,
        value: v.id,
      })),
    },
    { name: 'batch_year', label: 'Batch year', type: 'number' },
  ]

  const alignFields: EntityField[] = [
    {
      name: 'program_id',
      label: 'Program',
      type: 'select',
      options: (programs ?? []).map((p) => ({ label: p.name, value: p.id })),
    },
    {
      name: 'program_version_id',
      label: 'Program version (curriculum)',
      type: 'select',
      options: (versions ?? []).map((v) => ({
        label: `${programById.get(v.program_id)?.name ?? '?'} — ${v.version_label}`,
        value: v.id,
      })),
    },
    { name: 'batch_year', label: 'Batch year', type: 'number' },
    {
      name: 'status',
      label: 'Status',
      type: 'select',
      options: STATUS_OPTIONS.map((s) => ({ label: s, value: s })),
    },
  ]

  const columns: DataTableColumn<Student>[] = [
    { key: 'full_name', header: 'Name', render: (r) => r.full_name, searchValue: (r) => r.full_name },
    {
      key: 'student_code',
      header: 'Student code',
      render: (r) => r.student_code,
      searchValue: (r) => r.student_code,
    },
    { key: 'email', header: 'Email', render: (r) => r.email, searchValue: (r) => r.email },
    {
      key: 'program',
      header: 'Program',
      render: (r) => (r.program_id ? programById.get(r.program_id)?.name ?? '—' : '—'),
    },
    {
      key: 'version',
      header: 'Curriculum (version)',
      render: (r) => (r.program_version_id ? versionById.get(r.program_version_id)?.version_label ?? '—' : '—'),
    },
    { key: 'batch_year', header: 'Batch', render: (r) => r.batch_year ?? '—' },
    {
      key: 'status',
      header: 'Status',
      render: (r) => (
        <Badge variant="secondary" className="font-normal capitalize">
          {r.status}
        </Badge>
      ),
    },
  ]

  return (
    <div className="flex flex-col gap-4">
      <div className="flex justify-end">
        {canManage && (
          <Button size="sm" onClick={() => setCreateOpen(true)}>
            <Plus className="size-4" /> Add student
          </Button>
        )}
      </div>

      <DataTable
        data={data}
        columns={columns}
        rowKey={(r) => r.user_id}
        isLoading={isLoading}
        error={error}
        searchable
        searchPlaceholder="Search students…"
        emptyMessage="No students yet."
        actions={
          canManage
            ? (r) => (
                <Button size="sm" variant="outline" onClick={() => setAlignStudent(r)}>
                  <GraduationCap className="size-4" /> Align curriculum
                </Button>
              )
            : undefined
        }
      />

      <EntityFormDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        title="Add student"
        description="Creates a full student account (user + profile) in one step."
        fields={createFields}
        schema={createSchema}
        defaultValues={{
          full_name: '',
          email: '',
          password: '',
          student_code: '',
          program_id: '',
          program_version_id: '',
          batch_year: '',
        }}
        onSubmit={async (values) => {
          try {
            await create.mutateAsync({
              full_name: values.full_name,
              email: values.email,
              password: values.password,
              student_code: values.student_code,
              program_id: values.program_id || null,
              program_version_id: values.program_version_id || null,
              batch_year: values.batch_year === '' ? null : values.batch_year,
            })
            toast.success('Student created')
          } catch (err) {
            throw err instanceof ApiError ? err : new ApiError('Unable to create student.')
          }
        }}
      />

      {alignStudent && (
        <EntityFormDialog
          open={Boolean(alignStudent)}
          onOpenChange={(open) => !open && setAlignStudent(null)}
          title={`Align curriculum — ${alignStudent.full_name}`}
          description="Re-point this student at a different program or program version (curriculum), update batch year, or change status."
          fields={alignFields}
          schema={alignSchema}
          defaultValues={{
            program_id: alignStudent.program_id ?? '',
            program_version_id: alignStudent.program_version_id ?? '',
            batch_year: alignStudent.batch_year ?? '',
            status: alignStudent.status,
          }}
          submitLabel="Save alignment"
          onSubmit={async (values) => {
            try {
              await update.mutateAsync({
                id: alignStudent.user_id,
                body: {
                  program_id: values.program_id || null,
                  program_version_id: values.program_version_id || null,
                  batch_year: values.batch_year === '' ? null : values.batch_year,
                  status: values.status || null,
                },
              })
              toast.success('Curriculum alignment updated')
            } catch (err) {
              throw err instanceof ApiError ? err : new ApiError('Unable to update alignment.')
            }
          }}
        />
      )}
    </div>
  )
}
