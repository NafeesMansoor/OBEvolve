import * as React from 'react'
import { Pencil, Plus } from 'lucide-react'
import { toast } from 'sonner'
import { z } from 'zod'

import { useAuth } from '@/features/auth/useAuth'
import type { Department, Program } from '@/features/organization/types'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { DataTable, type DataTableColumn } from '@/components/data-table'
import { EntityFormDialog, type EntityField } from '@/components/entity-form-dialog'
import { NestedTabs } from '@/components/nested-tabs'
import { CourseSettingsPage } from '@/features/curriculum/CourseSettingsPage'
import { MyCoursesPage } from '@/features/course-management/MyCoursesPage'
import { OutcomeMappingPage } from '@/features/curriculum/OutcomeMappingPage'
import { ProgramSessionsPanel } from '@/features/organization/ProgramSessionsPanel'
import { ProgramSettingsPage } from '@/features/curriculum/ProgramSettingsPage'
import { RecordDetailSheet } from '@/components/record-detail-sheet'
import { Switch } from '@/components/ui/switch'
import { useEntityCreate, useEntityList, useEntityUpdate } from '@/lib/crud-hooks'
import { ApiError } from '@/lib/api-client'

// The code is lowercased and used to derive the program's own database
// schema name (`<institution_schema>__<code>`, see
// tenancy.provision_program_schema) — it can only contain lowercase
// letters, digits, and hyphens, not spaces or punctuation.
const CODE_PATTERN = /^[a-z0-9-]+$/i

const schema = z.object({
  department_id: z.string().min(1, 'Department is required'),
  name: z.string().min(1, 'Name is required').max(255),
  code: z
    .string()
    .min(1, 'Code is required')
    .max(50)
    .regex(CODE_PATTERN, 'Only letters, digits, and hyphens are allowed (no spaces).'),
  degree_level: z.string().optional(),
  session_names: z.string().optional(),
})

// No `code` — it's baked into the program's own database schema name at
// creation time and can't be changed by a field edit (see ProgramUpdate).
const editSchema = z.object({
  department_id: z.string().min(1, 'Department is required'),
  name: z.string().min(1, 'Name is required').max(255),
  degree_level: z.string().optional(),
})

/** "Admin creates a program" — surfaced prominently since the product spec
 * calls this out explicitly as a required flow. */
function ProgramsListPanel() {
  const { hasPermission } = useAuth()
  const canManage = hasPermission('program.manage')
  const [dialogOpen, setDialogOpen] = React.useState(false)
  const [editProgram, setEditProgram] = React.useState<Program | null>(null)
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
  const update = useEntityUpdate<Record<string, unknown>, Program>(
    (id) => `/org/programs/${id}`,
    [['org', 'programs']],
  )

  const toggleActive = async (program: Program) => {
    try {
      await update.mutateAsync({ id: program.id, body: { is_active: !program.is_active } })
      toast.success(program.is_active ? 'Program deactivated' : 'Program activated')
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Unable to update program status.')
    }
  }

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
    {
      name: 'code',
      label: 'Code',
      type: 'text',
      placeholder: 'e.g. bscse (letters, digits, hyphens only)',
    },
    { name: 'degree_level', label: 'Degree level', type: 'text', placeholder: 'e.g. BSc, MSc' },
    {
      name: 'session_names',
      label: 'Sessions per year (optional)',
      type: 'text',
      placeholder: 'e.g. Fall, Spring, Summer — leave blank to set up later',
    },
  ]

  const editFields: EntityField[] = [
    {
      name: 'department_id',
      label: 'Department',
      type: 'select',
      options: (departments ?? []).map((d) => ({ label: `${d.name} (${d.code})`, value: d.id })),
    },
    { name: 'name', label: 'Name', type: 'text' },
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
        actions={
          canManage
            ? (r) => (
                <Button
                  size="sm"
                  variant="ghost"
                  aria-label={`Edit ${r.name}`}
                  onClick={() => setEditProgram(r)}
                >
                  <Pencil className="size-4" />
                </Button>
              )
            : undefined
        }
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
        defaultValues={{
          department_id: '',
          name: '',
          code: '',
          degree_level: '',
          session_names: '',
        }}
        onSubmit={async (values) => {
          try {
            await create.mutateAsync({
              department_id: values.department_id,
              name: values.name,
              code: values.code,
              degree_level: values.degree_level || null,
              session_names: String(values.session_names ?? '')
                .split(',')
                .map((s) => s.trim())
                .filter(Boolean),
            })
            toast.success('Program created')
          } catch (err) {
            throw err instanceof ApiError ? err : new ApiError('Unable to create program.')
          }
        }}
      />

      {editProgram && (
        <EntityFormDialog
          open={Boolean(editProgram)}
          onOpenChange={(open) => !open && setEditProgram(null)}
          title={`Edit ${editProgram.name}`}
          description={`Code: ${editProgram.code} (fixed — a program's code can't be changed after creation)`}
          fields={editFields}
          schema={editSchema}
          defaultValues={{
            department_id: editProgram.department_id,
            name: editProgram.name,
            degree_level: editProgram.degree_level ?? '',
          }}
          onSubmit={async (values) => {
            try {
              await update.mutateAsync({
                id: editProgram.id,
                body: {
                  department_id: values.department_id,
                  name: values.name,
                  degree_level: values.degree_level || null,
                },
              })
              toast.success('Program updated')
              setEditProgram(null)
            } catch (err) {
              throw err instanceof ApiError ? err : new ApiError('Unable to update program.')
            }
          }}
        />
      )}
    </div>
  )
}

/** Programs list + per-program Sessions config, as nested tabs — the outer
 * Institute Settings tab strip already owns "Programs"; this is the next
 * tier down, one visual step quieter (see NestedTabs).
 *
 * For Institution Administrator specifically (detected the same way the
 * rest of this codebase gates any nav/page — by permission code, never
 * role name: `institution.manage` is unique to that role among tenant
 * roles today), four more tabs fold in what's otherwise its own top-level
 * nav item (layout.tsx filters those out of the sidebar for exactly this
 * permission so they don't appear twice) — Question Bank deliberately
 * stays top-level only, per the ask that prompted this. Every other role
 * keeps seeing Programs/Sessions only, and keeps those four as ordinary
 * top-level pages. */
export function ProgramsTab() {
  const { hasPermission } = useAuth()
  const isInstitutionAdmin = hasPermission('institution.manage')

  return (
    <NestedTabs
      items={[
        { value: 'list', label: 'Programs', content: <ProgramsListPanel /> },
        { value: 'sessions', label: 'Sessions', content: <ProgramSessionsPanel /> },
        {
          value: 'curriculum',
          label: 'Program & Curriculum',
          show: isInstitutionAdmin,
          content: <ProgramSettingsPage embedded />,
        },
        {
          value: 'outcome-mapping',
          label: 'Outcome Mapping',
          show: isInstitutionAdmin,
          content: <OutcomeMappingPage embedded />,
        },
        {
          value: 'course-settings',
          label: 'Course Level Settings',
          show: isInstitutionAdmin,
          content: <CourseSettingsPage embedded />,
        },
        {
          value: 'courses',
          label: 'Courses',
          show: isInstitutionAdmin,
          content: <MyCoursesPage embedded />,
        },
      ]}
    />
  )
}
