import * as React from 'react'
import { Plus, Users } from 'lucide-react'
import { toast } from 'sonner'
import { z } from 'zod'

import { useAuth } from '@/features/auth/useAuth'
import { useAcademicTermLookup } from '@/features/academic-ops/useLookups'
import { useProgramVersionOptions } from '@/features/curriculum/useProgramVersionOptions'
import { ApiError } from '@/lib/api-client'
import { useEntityCreate, useEntityList } from '@/lib/crud-hooks'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { DataTable, type DataTableColumn } from '@/components/data-table'
import { EntityFormDialog, type EntityField } from '@/components/entity-form-dialog'
import { RecordDetailSheet } from '@/components/record-detail-sheet'

interface Cohort {
  id: string
  code: string
  intake_term_id: string
  intake_year: number
  program_version_id: string
  status: string
  created_at: string
  updated_at: string
}

interface CohortStudent {
  user_id: string
  email: string
  full_name: string
  is_active: boolean
  student_code: string
  status: string
}

const createSchema = z.object({
  code: z.string().min(1, 'Code is required').max(50),
  intake_term_id: z.string().min(1, 'Intake term is required'),
  intake_year: z.coerce.number().int(),
  program_version_id: z.string().min(1, 'Program version is required'),
})

/** Student cohorts / batches (spec §5, §35-36) — "loading" an existing
 * cohort surfaces its roster (View students); changing which curriculum a
 * cohort follows is a separate, explicitly-audited admin action, not
 * available here (spec §5: "not a routine operation") — use the raw-data
 * console or a future dedicated action for that. */
export function CohortsTab() {
  const { hasPermission } = useAuth()
  const canManage = hasPermission('section.manage')
  const { options: termOptions, termById } = useAcademicTermLookup()
  const { options: pvOptions, programById, versions } = useProgramVersionOptions()
  const [createOpen, setCreateOpen] = React.useState(false)
  const [rosterCohort, setRosterCohort] = React.useState<Cohort | null>(null)

  const { data: cohorts, isLoading, error } = useEntityList<Cohort>(
    ['org', 'cohorts'],
    '/org/cohorts',
  )
  const create = useEntityCreate<Record<string, unknown>, Cohort>('/org/cohorts', [
    ['org', 'cohorts'],
  ])

  const { data: roster, isLoading: rosterLoading } = useEntityList<CohortStudent>(
    ['org', 'cohorts', rosterCohort?.id ?? '', 'students'],
    `/org/cohorts/${rosterCohort?.id}/students`,
    undefined,
    { enabled: Boolean(rosterCohort) },
  )

  const versionLabel = (id: string) => {
    const v = versions.find((pv) => pv.id === id)
    if (!v) return '—'
    return `${programById.get(v.program_id)?.name ?? 'Unknown program'} — ${v.version_label}`
  }

  const fields: EntityField[] = [
    { name: 'code', label: 'Cohort code', type: 'text', placeholder: 'e.g. BSCSE-2026' },
    { name: 'intake_term_id', label: 'Intake term', type: 'select', options: termOptions },
    { name: 'intake_year', label: 'Intake year', type: 'number' },
    { name: 'program_version_id', label: 'Assigned curriculum', type: 'select', options: pvOptions },
  ]

  const columns: DataTableColumn<Cohort>[] = [
    { key: 'code', header: 'Code', render: (r) => r.code },
    { key: 'intake_year', header: 'Intake year', render: (r) => r.intake_year },
    {
      key: 'intake_term',
      header: 'Intake term',
      render: (r) => termById.get(r.intake_term_id)?.name ?? '—',
    },
    { key: 'curriculum', header: 'Curriculum', render: (r) => versionLabel(r.program_version_id) },
    {
      key: 'status',
      header: 'Status',
      render: (r) => (
        <Badge variant={r.status === 'active' ? 'default' : 'outline'} className="font-normal capitalize">
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
            <Plus className="size-4" /> New cohort
          </Button>
        )}
      </div>

      <DataTable
        data={cohorts}
        columns={columns}
        rowKey={(r) => r.id}
        isLoading={isLoading}
        error={error}
        emptyMessage="No cohorts yet."
        actions={(r) => (
          <Button size="sm" variant="outline" onClick={() => setRosterCohort(r)}>
            <Users className="size-3.5" /> View students
          </Button>
        )}
      />

      <EntityFormDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        title="New cohort"
        fields={fields}
        schema={createSchema}
        defaultValues={{
          code: '',
          intake_term_id: '',
          intake_year: new Date().getFullYear(),
          program_version_id: '',
        }}
        onSubmit={async (values) => {
          try {
            await create.mutateAsync(values)
            toast.success('Cohort created')
          } catch (err) {
            throw err instanceof ApiError ? err : new ApiError('Unable to create cohort.')
          }
        }}
      />

      {rosterCohort && (
        <RecordDetailSheet
          open={Boolean(rosterCohort)}
          onOpenChange={(open) => !open && setRosterCohort(null)}
          title={`${rosterCohort.code} — students`}
          fields={
            rosterLoading
              ? [{ label: 'Loading', value: '…' }]
              : (roster ?? []).length === 0
                ? [{ label: 'Students', value: 'No students in this cohort yet.' }]
                : (roster ?? []).map((s) => ({
                    label: s.student_code,
                    value: `${s.full_name} — ${s.status}${s.is_active ? '' : ' (inactive)'}`,
                  }))
          }
        />
      )}
    </div>
  )
}
