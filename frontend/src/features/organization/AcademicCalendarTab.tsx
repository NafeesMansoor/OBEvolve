import * as React from 'react'
import { Plus } from 'lucide-react'
import { toast } from 'sonner'
import { z } from 'zod'

import { useAuth } from '@/features/auth/useAuth'
import type { AcademicTerm, AcademicYear } from '@/features/organization/types'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { DataTable, type DataTableColumn } from '@/components/data-table'
import { EntityFormDialog, type EntityField } from '@/components/entity-form-dialog'
import { RecordDetailSheet } from '@/components/record-detail-sheet'
import { useEntityCreate, useEntityList } from '@/lib/crud-hooks'
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
    { name: 'start_date', label: 'Start date', type: 'date' },
    { name: 'end_date', label: 'End date', type: 'date' },
  ]

  const yearColumns: DataTableColumn<AcademicYear>[] = [
    { key: 'label', header: 'Label', render: (r) => r.label, searchValue: (r) => r.label },
    { key: 'start_date', header: 'Start', render: (r) => r.start_date },
    { key: 'end_date', header: 'End', render: (r) => r.end_date },
  ]

  const termColumns: DataTableColumn<AcademicTerm>[] = [
    { key: 'name', header: 'Name', render: (r) => r.name, searchValue: (r) => r.name },
    { key: 'term_type', header: 'Type', render: (r) => r.term_type },
    { key: 'year', header: 'Academic year', render: (r) => yearById.get(r.academic_year_id)?.label ?? '—' },
    { key: 'start_date', header: 'Start', render: (r) => r.start_date },
    { key: 'end_date', header: 'End', render: (r) => r.end_date },
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
        <CardContent>
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
            { label: 'Type', value: viewTerm.term_type },
            { label: 'Academic year', value: yearById.get(viewTerm.academic_year_id)?.label ?? '—' },
            { label: 'Start date', value: viewTerm.start_date },
            { label: 'End date', value: viewTerm.end_date },
          ]}
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
          end_date: '',
        }}
        onSubmit={async (values) => {
          try {
            await createTerm.mutateAsync(values)
            toast.success('Academic term created')
          } catch (err) {
            throw err instanceof ApiError ? err : new ApiError('Unable to create academic term.')
          }
        }}
      />
    </div>
  )
}
