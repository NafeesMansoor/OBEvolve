import * as React from 'react'
import { Plus, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { z } from 'zod'

import { useAuth } from '@/features/auth/useAuth'
import { useAcademicTermLookup, useCourseVersionLookup } from '@/features/academic-ops/useLookups'
import type { CourseOffering, CourseSection } from '@/features/academic-ops/types'
import { ApiError } from '@/lib/api-client'
import { useEntityCreate, useEntityDelete, useEntityList, useEntityUpdate } from '@/lib/crud-hooks'
import { Button } from '@/components/ui/button'
import { ConfirmAction } from '@/components/confirm-action'
import { DataTable, type DataTableColumn } from '@/components/data-table'
import { EntityFormDialog, type EntityField } from '@/components/entity-form-dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

export function SectionsTab() {
  const { hasPermission } = useAuth()
  const canManage = hasPermission('section.manage')
  const { labelFor } = useCourseVersionLookup()
  const { termById } = useAcademicTermLookup()
  const { data: offerings } = useEntityList<CourseOffering>(
    ['academic', 'course-offerings'],
    '/academic/course-offerings',
  )
  const [offeringId, setOfferingId] = React.useState('')
  const [createOpen, setCreateOpen] = React.useState(false)
  const [editSection, setEditSection] = React.useState<CourseSection | null>(null)

  const offeringOptions = React.useMemo(
    () =>
      (offerings ?? []).map((o) => ({
        label: `${labelFor(o.course_version_id)} · ${termById.get(o.academic_term_id)?.name ?? ''}`,
        value: o.id,
      })),
    [offerings, labelFor, termById],
  )

  const {
    data: sections,
    isLoading,
    error,
  } = useEntityList<CourseSection>(
    ['academic', 'sections', offeringId],
    '/academic/sections',
    { course_offering_id: offeringId || undefined },
    { enabled: Boolean(offeringId) },
  )
  const create = useEntityCreate<Record<string, unknown>, CourseSection>('/academic/sections', [
    ['academic', 'sections', offeringId],
  ])
  const update = useEntityUpdate<Record<string, unknown>, CourseSection>(
    (id) => `/academic/sections/${id}`,
    [['academic', 'sections', offeringId]],
  )
  const remove = useEntityDelete((id) => `/academic/sections/${id}`, [
    ['academic', 'sections', offeringId],
  ])

  const schema = z.object({
    section_code: z.string().min(1, 'Section code is required').max(20),
    max_students: z.union([z.coerce.number().int(), z.literal('')]).optional(),
  })
  const fields: EntityField[] = [
    { name: 'section_code', label: 'Section code', type: 'text', placeholder: 'e.g. A' },
    { name: 'max_students', label: 'Max students', type: 'number' },
  ]

  const columns: DataTableColumn<CourseSection>[] = [
    { key: 'section_code', header: 'Section', render: (r) => r.section_code },
    { key: 'max_students', header: 'Max students', render: (r) => r.max_students ?? '—' },
  ]

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="w-full max-w-md">
          <Select value={offeringId} onValueChange={setOfferingId}>
            <SelectTrigger>
              <SelectValue placeholder="Select a course offering" />
            </SelectTrigger>
            <SelectContent>
              {offeringOptions.map((o) => (
                <SelectItem key={o.value} value={o.value}>
                  {o.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        {canManage && offeringId && (
          <Button size="sm" onClick={() => setCreateOpen(true)}>
            <Plus className="size-4" /> New section
          </Button>
        )}
      </div>

      {!offeringId ? (
        <p className="text-sm text-muted-foreground">Select a course offering to see its sections.</p>
      ) : (
        <DataTable
          data={sections}
          columns={columns}
          rowKey={(r) => r.id}
          isLoading={isLoading}
          error={error}
          emptyMessage="No sections yet for this offering."
          onRowClick={canManage ? (r) => setEditSection(r) : undefined}
          actions={
            canManage
              ? (r) => (
                  <ConfirmAction
                    trigger={
                      <Button size="sm" variant="ghost">
                        <Trash2 className="size-4" />
                      </Button>
                    }
                    title={`Delete section ${r.section_code}?`}
                    onConfirm={async () => {
                      try {
                        await remove.mutateAsync(r.id)
                        toast.success('Section deleted')
                      } catch (err) {
                        toast.error(err instanceof ApiError ? err.detail : 'Unable to delete section.')
                      }
                    }}
                  />
                )
              : undefined
          }
        />
      )}

      <EntityFormDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        title="New section"
        fields={fields}
        schema={schema}
        defaultValues={{ section_code: '', max_students: '' }}
        onSubmit={async (values) => {
          try {
            await create.mutateAsync({
              course_offering_id: offeringId,
              section_code: values.section_code,
              max_students: values.max_students === '' ? null : values.max_students,
            })
            toast.success('Section created')
          } catch (err) {
            throw err instanceof ApiError ? err : new ApiError('Unable to create section.')
          }
        }}
      />

      {editSection && (
        <EntityFormDialog
          open={Boolean(editSection)}
          onOpenChange={(open) => !open && setEditSection(null)}
          title={`Edit section ${editSection.section_code}`}
          fields={fields}
          schema={schema}
          defaultValues={{
            section_code: editSection.section_code,
            max_students: editSection.max_students ?? '',
          }}
          onSubmit={async (values) => {
            try {
              await update.mutateAsync({
                id: editSection.id,
                body: {
                  course_offering_id: offeringId,
                  section_code: values.section_code,
                  max_students: values.max_students === '' ? null : values.max_students,
                },
              })
              toast.success('Section updated')
            } catch (err) {
              throw err instanceof ApiError ? err : new ApiError('Unable to update section.')
            }
          }}
        />
      )}
    </div>
  )
}
