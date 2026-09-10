import * as React from 'react'
import { Plus, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { z } from 'zod'

import { useAuth } from '@/features/auth/useAuth'
import { useProgramVersionOptions } from '@/features/curriculum/useProgramVersionOptions'
import type { AcademicTerm, AcademicYear, TermEffectiveCurriculum } from '@/features/organization/types'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ConfirmAction } from '@/components/confirm-action'
import { DataTable, type DataTableColumn } from '@/components/data-table'
import { EntityFormDialog, type EntityField } from '@/components/entity-form-dialog'
import { RecordDetailSheet } from '@/components/record-detail-sheet'
import { useEntityAction, useEntityCreate, useEntityDelete, useEntityList } from '@/lib/crud-hooks'
import { ApiError } from '@/lib/api-client'

const yearSchema = z.object({
  label: z.string().min(1, 'Label is required').max(20),
  start_date: z.string().min(1, 'Start date is required'),
  end_date: z.string().min(1, 'End date is required'),
})

const yearFields: EntityField[] = [
  { name: 'label', label: 'Label', type: 'text', placeholder: 'e.g. 2025-2026' },
  { name: 'start_date', label: 'Start date', type: 'date' },
  { name: 'end_date', label: 'End date', type: 'date' },
]

const termSchema = z.object({
  academic_year_id: z.string().min(1, 'Academic year is required'),
  name: z.string().min(1, 'Name is required').max(50),
  term_type: z.string().min(1, 'Term type is required').max(30),
  start_date: z.string().min(1, 'Start date is required'),
  end_date: z.string().min(1, 'End date is required'),
  // spec §3: the rest of the academic calendar. All optional — a term is
  // normally created before every milestone date is known and filled in
  // over time; the backend enforces the chronological order once dates
  // are supplied (Class Start -> Add/Drop -> Midterm -> Final -> Result
  // Due -> Result Publication -> Term End), surfaced here as a plain
  // server-error message if violated.
  add_drop_last_date: z.string().optional(),
  midterm_start_date: z.string().optional(),
  midterm_end_date: z.string().optional(),
  final_exam_start_date: z.string().optional(),
  final_exam_end_date: z.string().optional(),
  result_due_date: z.string().optional(),
  result_publication_date: z.string().optional(),
})

/** Academic years + terms ("define semesters") — small enough to combine on
 * one tab rather than two near-empty pages. */
export function AcademicCalendarTab() {
  const { hasPermission } = useAuth()
  const canManage = hasPermission('academic_calendar.manage')
  const [yearDialogOpen, setYearDialogOpen] = React.useState(false)
  const [termDialogOpen, setTermDialogOpen] = React.useState(false)
  const [viewYear, setViewYear] = React.useState<AcademicYear | null>(null)
  const [viewTerm, setViewTerm] = React.useState<AcademicTerm | null>(null)
  const [effectiveCurriculumDialogOpen, setEffectiveCurriculumDialogOpen] = React.useState(false)
  const { options: pvOptions, versions: programVersions, programById } = useProgramVersionOptions()

  const { data: years, isLoading: yearsLoading, error: yearsError } = useEntityList<AcademicYear>(
    ['org', 'academic-years'],
    '/org/academic-years',
  )
  const { data: terms, isLoading: termsLoading, error: termsError } = useEntityList<AcademicTerm>(
    ['org', 'academic-terms'],
    '/org/academic-terms',
  )
  const createYear = useEntityCreate<Record<string, unknown>, AcademicYear>(
    '/org/academic-years',
    [['org', 'academic-years']],
  )
  const createTerm = useEntityCreate<Record<string, unknown>, AcademicTerm>(
    '/org/academic-terms',
    [['org', 'academic-terms']],
  )
  const activateTerm = useEntityAction<AcademicTerm>(
    (id) => `/org/academic-terms/${id}/activate`,
    [['org', 'academic-terms']],
  )

  const { data: effectiveCurricula, isLoading: effectiveCurriculaLoading } = useEntityList<
    TermEffectiveCurriculum
  >(
    ['org', 'term-effective-curricula', viewTerm?.id ?? ''],
    '/org/term-effective-curricula',
    { academic_term_id: viewTerm?.id },
    { enabled: Boolean(viewTerm) },
  )
  const createEffectiveCurriculum = useEntityCreate<Record<string, unknown>, TermEffectiveCurriculum>(
    '/org/term-effective-curricula',
    [['org', 'term-effective-curricula', viewTerm?.id ?? '']],
  )
  const deleteEffectiveCurriculum = useEntityDelete(
    (id) => `/org/term-effective-curricula/${id}`,
    [['org', 'term-effective-curricula', viewTerm?.id ?? '']],
  )

  const yearById = React.useMemo(() => new Map((years ?? []).map((y) => [y.id, y])), [years])

  const termFields: EntityField[] = [
    {
      name: 'academic_year_id',
      label: 'Academic year',
      type: 'select',
      options: (years ?? []).map((y) => ({ label: y.label, value: y.id })),
    },
    { name: 'name', label: 'Name', type: 'text', placeholder: 'e.g. Fall 2025' },
    { name: 'term_type', label: 'Term type', type: 'text', placeholder: 'e.g. semester, summer' },
    { name: 'start_date', label: 'Class start date', type: 'date' },
    { name: 'add_drop_last_date', label: 'Add/drop last date', type: 'date' },
    { name: 'midterm_start_date', label: 'Midterm start date', type: 'date' },
    { name: 'midterm_end_date', label: 'Midterm end date', type: 'date' },
    { name: 'final_exam_start_date', label: 'Final exam start date', type: 'date' },
    { name: 'final_exam_end_date', label: 'Final exam end date', type: 'date' },
    { name: 'result_due_date', label: 'Result due date', type: 'date' },
    { name: 'result_publication_date', label: 'Result publication date', type: 'date' },
    { name: 'end_date', label: 'Trimester end date', type: 'date' },
  ]

  const yearColumns: DataTableColumn<AcademicYear>[] = [
    { key: 'label', header: 'Label', render: (r) => r.label, searchValue: (r) => r.label },
    { key: 'start_date', header: 'Start', render: (r) => r.start_date },
    { key: 'end_date', header: 'End', render: (r) => r.end_date },
  ]

  const activeCount = (terms ?? []).filter((t) => t.is_active).length

  const termColumns: DataTableColumn<AcademicTerm>[] = [
    { key: 'name', header: 'Name', render: (r) => r.name, searchValue: (r) => r.name },
    { key: 'term_type', header: 'Type', render: (r) => r.term_type },
    { key: 'year', header: 'Academic year', render: (r) => yearById.get(r.academic_year_id)?.label ?? '—' },
    { key: 'start_date', header: 'Start', render: (r) => r.start_date },
    { key: 'end_date', header: 'End', render: (r) => r.end_date },
    {
      key: 'status',
      header: 'Status',
      render: (r) =>
        r.is_active ? (
          <Badge className="bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300">
            Current
          </Badge>
        ) : (
          <Badge variant="outline" className="font-normal">
            Previous
          </Badge>
        ),
    },
  ]

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-base">Academic years</CardTitle>
          {canManage && (
            <Button size="sm" onClick={() => setYearDialogOpen(true)}>
              <Plus className="size-4" /> New academic year
            </Button>
          )}
        </CardHeader>
        <CardContent>
          <DataTable
            data={years}
            columns={yearColumns}
            rowKey={(r) => r.id}
            isLoading={yearsLoading}
            error={yearsError}
            emptyMessage="No academic years yet."
            onRowClick={(r) => setViewYear(r)}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-base">Academic terms (semesters)</CardTitle>
          {canManage && (
            <Button size="sm" onClick={() => setTermDialogOpen(true)}>
              <Plus className="size-4" /> New term
            </Button>
          )}
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {activeCount > 1 && (
            <div className="rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-sm text-warning-foreground">
              {activeCount} terms are marked current at once — every "current semester" view in the
              app treats all of them as current. Activate the one term that should actually be
              current below to fix this.
            </div>
          )}
          {activeCount === 0 && (terms ?? []).length > 0 && (
            <div className="rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-sm text-warning-foreground">
              No term is marked current — every "current semester" view in the app will show
              nothing by default. Activate the current term below.
            </div>
          )}
          <DataTable
            data={terms}
            columns={termColumns}
            rowKey={(r) => r.id}
            isLoading={termsLoading}
            error={termsError}
            searchable
            searchPlaceholder="Search terms…"
            emptyMessage="No academic terms yet."
            onRowClick={(r) => setViewTerm(r)}
            actions={
              canManage
                ? (r) =>
                    r.is_active ? undefined : (
                      <ConfirmAction
                        trigger={
                          <Button size="sm" variant="outline">
                            Set as current
                          </Button>
                        }
                        title={`Set ${r.name} as the current term?`}
                        description="Every other term will be marked as a previous term. This changes what every 'current semester' view in the app shows by default."
                        onConfirm={async () => {
                          try {
                            await activateTerm.mutateAsync(r.id)
                            toast.success(`${r.name} is now the current term`)
                          } catch (err) {
                            toast.error(
                              err instanceof ApiError ? err.detail : 'Unable to activate term.',
                            )
                          }
                        }}
                      />
                    )
                : undefined
            }
          />
        </CardContent>
      </Card>

      {viewYear && (
        <RecordDetailSheet
          open={Boolean(viewYear)}
          onOpenChange={(open) => !open && setViewYear(null)}
          title={viewYear.label}
          fields={[
            { label: 'Start date', value: viewYear.start_date },
            { label: 'End date', value: viewYear.end_date },
          ]}
        />
      )}

      {viewTerm && (
        <RecordDetailSheet
          open={Boolean(viewTerm)}
          onOpenChange={(open) => !open && setViewTerm(null)}
          title={viewTerm.name}
          subtitle={yearById.get(viewTerm.academic_year_id)?.label}
          fields={[
            { label: 'Status', value: viewTerm.is_active ? 'Current' : 'Previous' },
            { label: 'Type', value: viewTerm.term_type },
            { label: 'Academic year', value: yearById.get(viewTerm.academic_year_id)?.label ?? '—' },
            { label: 'Class start date', value: viewTerm.start_date },
            { label: 'Add/drop last date', value: viewTerm.add_drop_last_date ?? '—' },
            { label: 'Midterm start date', value: viewTerm.midterm_start_date ?? '—' },
            { label: 'Midterm end date', value: viewTerm.midterm_end_date ?? '—' },
            { label: 'Final exam start date', value: viewTerm.final_exam_start_date ?? '—' },
            { label: 'Final exam end date', value: viewTerm.final_exam_end_date ?? '—' },
            { label: 'Result due date', value: viewTerm.result_due_date ?? '—' },
            { label: 'Result publication date', value: viewTerm.result_publication_date ?? '—' },
            { label: 'Trimester end date', value: viewTerm.end_date },
          ]}
        >
          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-medium">
                Effective curricula
                <span className="ml-1 font-normal text-muted-foreground">
                  (spec §4 — a term may have more than one, for different cohorts)
                </span>
              </h4>
              {canManage && (
                <Button size="sm" variant="outline" onClick={() => setEffectiveCurriculumDialogOpen(true)}>
                  <Plus className="size-4" /> Add
                </Button>
              )}
            </div>
            {effectiveCurriculaLoading ? (
              <p className="text-sm text-muted-foreground">Loading…</p>
            ) : (effectiveCurricula ?? []).length === 0 ? (
              <p className="text-sm text-muted-foreground">No effective curriculum assigned yet.</p>
            ) : (
              <ul className="flex flex-col gap-1">
                {(effectiveCurricula ?? []).map((ec) => {
                  const version = programVersions.find((v) => v.id === ec.program_version_id)
                  const label = version
                    ? `${programById.get(version.program_id)?.name ?? 'Unknown program'} — ${version.version_label}`
                    : 'Unknown curriculum'
                  return (
                    <li key={ec.id} className="flex items-center justify-between text-sm">
                      <span>{label}</span>
                      {canManage && (
                        <Button
                          size="icon"
                          variant="ghost"
                          aria-label="Remove effective curriculum"
                          onClick={async () => {
                            try {
                              await deleteEffectiveCurriculum.mutateAsync(ec.id)
                            } catch (err) {
                              toast.error(
                                err instanceof ApiError ? err.detail : 'Unable to remove.',
                              )
                            }
                          }}
                        >
                          <Trash2 className="size-3.5" />
                        </Button>
                      )}
                    </li>
                  )
                })}
              </ul>
            )}
          </div>
        </RecordDetailSheet>
      )}

      {viewTerm && (
        <EntityFormDialog
          open={effectiveCurriculumDialogOpen}
          onOpenChange={setEffectiveCurriculumDialogOpen}
          title={`Add effective curriculum — ${viewTerm.name}`}
          fields={[{ name: 'program_version_id', label: 'Curriculum', type: 'select', options: pvOptions }]}
          schema={z.object({ program_version_id: z.string().min(1, 'Required') })}
          defaultValues={{ program_version_id: '' }}
          onSubmit={async (values) => {
            try {
              await createEffectiveCurriculum.mutateAsync({
                academic_term_id: viewTerm.id,
                program_version_id: values.program_version_id,
              })
              toast.success('Effective curriculum added')
            } catch (err) {
              throw err instanceof ApiError ? err : new ApiError('Unable to add effective curriculum.')
            }
          }}
        />
      )}

      <EntityFormDialog
        open={yearDialogOpen}
        onOpenChange={setYearDialogOpen}
        title="New academic year"
        fields={yearFields}
        schema={yearSchema}
        defaultValues={{ label: '', start_date: '', end_date: '' }}
        onSubmit={async (values) => {
          try {
            await createYear.mutateAsync(values)
            toast.success('Academic year created')
          } catch (err) {
            throw err instanceof ApiError ? err : new ApiError('Unable to create academic year.')
          }
        }}
      />

      <EntityFormDialog
        open={termDialogOpen}
        onOpenChange={setTermDialogOpen}
        title="New academic term"
        description={(years ?? []).length === 0 ? 'Create an academic year first.' : undefined}
        fields={termFields}
        schema={termSchema}
        defaultValues={{
          academic_year_id: '',
          name: '',
          term_type: '',
          start_date: '',
          add_drop_last_date: '',
          midterm_start_date: '',
          midterm_end_date: '',
          final_exam_start_date: '',
          final_exam_end_date: '',
          result_due_date: '',
          result_publication_date: '',
          end_date: '',
        }}
        onSubmit={async (values) => {
          try {
            // Optional date fields: an empty string from the form must
            // become null, not "", before it reaches the API.
            const body = { ...values }
            for (const key of [
              'add_drop_last_date',
              'midterm_start_date',
              'midterm_end_date',
              'final_exam_start_date',
              'final_exam_end_date',
              'result_due_date',
              'result_publication_date',
            ] as const) {
              if (!body[key]) body[key] = null
            }
            await createTerm.mutateAsync(body)
            toast.success('Academic term created')
          } catch (err) {
            throw err instanceof ApiError ? err : new ApiError('Unable to create academic term.')
          }
        }}
      />
    </div>
  )
}
