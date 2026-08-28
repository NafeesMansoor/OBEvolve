import * as React from 'react'
import { Download, Plus, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { z } from 'zod'

import { useAuth } from '@/features/auth/useAuth'
import { useAcademicTermLookup, useCourseVersionLookup } from '@/features/academic-ops/useLookups'
import type { CourseOffering } from '@/features/academic-ops/types'
import { useProgramVersionOptions } from '@/features/curriculum/useProgramVersionOptions'
import { ApiError } from '@/lib/api-client'
import { useEntityCreate, useEntityDelete, useEntityList, useEntityUpdate } from '@/lib/crud-hooks'
import { Button } from '@/components/ui/button'
import { ConfirmAction } from '@/components/confirm-action'
import { DataTable, type DataTableColumn } from '@/components/data-table'
import { EntityFormDialog, type EntityField } from '@/components/entity-form-dialog'
import { RecordDetailSheet } from '@/components/record-detail-sheet'
import { ImportFromTermDialog } from '@/features/academic-ops/ImportFromTermDialog'

const schema = z.object({
  course_version_id: z.string().min(1, 'Course version is required'),
  academic_term_id: z.string().min(1, 'Academic term is required'),
  program_version_id: z.string().optional(),
})

export function OfferingsTab() {
  const { hasPermission } = useAuth()
  const canManage = hasPermission('section.manage')
  const [createOpen, setCreateOpen] = React.useState(false)
  const [importOpen, setImportOpen] = React.useState(false)
  const [editOffering, setEditOffering] = React.useState<CourseOffering | null>(null)
  const [viewOffering, setViewOffering] = React.useState<CourseOffering | null>(null)

  const { options: cvOptions, labelFor } = useCourseVersionLookup()
  const { options: termOptions, termById } = useAcademicTermLookup()
  const { options: pvOptions } = useProgramVersionOptions()
  const pvLabelById = React.useMemo(
    () => new Map(pvOptions.map((o) => [o.value, o.label])),
    [pvOptions],
  )

  const { data, isLoading, error } = useEntityList<CourseOffering>(
    ['academic', 'course-offerings'],
    '/academic/course-offerings',
  )
  const create = useEntityCreate<Record<string, unknown>, CourseOffering>(
    '/academic/course-offerings',
    [['academic', 'course-offerings']],
  )
  const update = useEntityUpdate<Record<string, unknown>, CourseOffering>(
    (id) => `/academic/course-offerings/${id}`,
    [['academic', 'course-offerings']],
  )
  const remove = useEntityDelete((id) => `/academic/course-offerings/${id}`, [
    ['academic', 'course-offerings'],
  ])

  const fields: EntityField[] = [
    { name: 'course_version_id', label: 'Course version', type: 'select', options: cvOptions },
    { name: 'academic_term_id', label: 'Academic term', type: 'select', options: termOptions },
    {
      name: 'program_version_id',
      label: 'Program version (optional)',
      type: 'select',
      options: pvOptions,
    },
  ]

  const columns: DataTableColumn<CourseOffering>[] = [
    { key: 'course', header: 'Course', render: (r) => labelFor(r.course_version_id) },
    { key: 'term', header: 'Term', render: (r) => termById.get(r.academic_term_id)?.name ?? '—' },
  ]

  return (
    <div className="flex flex-col gap-4">
      <div className="flex justify-end gap-2">
        {canManage && (
          <Button size="sm" variant="outline" onClick={() => setImportOpen(true)}>
            <Download className="size-4" /> Import from term
          </Button>
        )}
        {canManage && (
          <Button size="sm" onClick={() => setCreateOpen(true)}>
            <Plus className="size-4" /> New offering
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
        emptyMessage="No course offerings yet."
        onRowClick={(r) => setViewOffering(r)}
        actions={
          canManage
            ? (r) => (
                <ConfirmAction
                  trigger={
                    <Button size="sm" variant="ghost" aria-label="Delete offering">
                      <Trash2 className="size-4" />
                    </Button>
                  }
                  title="Delete this course offering?"
                  description="Sections and enrollments under it may also be affected."
                  onConfirm={async () => {
                    try {
                      await remove.mutateAsync(r.id)
                      toast.success('Offering deleted')
                    } catch (err) {
                      toast.error(err instanceof ApiError ? err.detail : 'Unable to delete offering.')
                    }
                  }}
                />
              )
            : undefined
        }
      />

      <EntityFormDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        title="New course offering"
        fields={fields}
        schema={schema}
        defaultValues={{ course_version_id: '', academic_term_id: '', program_version_id: '' }}
        onSubmit={async (values) => {
          try {
            await create.mutateAsync({
              course_version_id: values.course_version_id,
              academic_term_id: values.academic_term_id,
              program_version_id: values.program_version_id || null,
            })
            toast.success('Course offering created')
          } catch (err) {
            throw err instanceof ApiError ? err : new ApiError('Unable to create offering.')
          }
        }}
      />

      {viewOffering && (
        <RecordDetailSheet
          open={Boolean(viewOffering)}
          onOpenChange={(open) => !open && setViewOffering(null)}
          title={labelFor(viewOffering.course_version_id)}
          subtitle={termById.get(viewOffering.academic_term_id)?.name}
          fields={[
            { label: 'Course', value: labelFor(viewOffering.course_version_id) },
            { label: 'Term', value: termById.get(viewOffering.academic_term_id)?.name ?? '—' },
            {
              label: 'Program version',
              value: viewOffering.program_version_id
                ? (pvLabelById.get(viewOffering.program_version_id) ?? '—')
                : 'Institution-wide',
            },
          ]}
          onEdit={
            canManage
              ? () => {
                  setEditOffering(viewOffering)
                  setViewOffering(null)
                }
              : undefined
          }
        />
      )}

      {editOffering && (
        <EntityFormDialog
          open={Boolean(editOffering)}
          onOpenChange={(open) => !open && setEditOffering(null)}
          title="Edit course offering"
          fields={fields}
          schema={schema}
          defaultValues={{
            course_version_id: editOffering.course_version_id,
            academic_term_id: editOffering.academic_term_id,
            program_version_id: editOffering.program_version_id ?? '',
          }}
          onSubmit={async (values) => {
            try {
              await update.mutateAsync({
                id: editOffering.id,
                body: {
                  course_version_id: values.course_version_id,
                  academic_term_id: values.academic_term_id,
                  program_version_id: values.program_version_id || null,
                },
              })
              toast.success('Offering updated')
            } catch (err) {
              throw err instanceof ApiError ? err : new ApiError('Unable to update offering.')
            }
          }}
        />
      )}

      <ImportFromTermDialog
        open={importOpen}
        onOpenChange={setImportOpen}
        termOptions={termOptions}
        onImport={async (sourceTermId, targetTermId) => {
          const source = (data ?? []).filter((o) => o.academic_term_id === sourceTermId)
          const alreadyInTarget = new Set(
            (data ?? [])
              .filter((o) => o.academic_term_id === targetTermId)
              .map((o) => o.course_version_id),
          )
          const toImport = source.filter((o) => !alreadyInTarget.has(o.course_version_id))

          let imported = 0
          for (const offering of toImport) {
            try {
              await create.mutateAsync({
                course_version_id: offering.course_version_id,
                academic_term_id: targetTermId,
                program_version_id: offering.program_version_id ?? null,
              })
              imported += 1
            } catch {
              // Best-effort: one failure doesn't abort the rest of the batch.
            }
          }
          const skipped = source.length - toImport.length
          toast.success(
            `Imported ${imported} offering${imported === 1 ? '' : 's'}` +
              (skipped > 0 ? ` (${skipped} already existed in the target term)` : ''),
          )
        }}
      />
    </div>
  )
}
