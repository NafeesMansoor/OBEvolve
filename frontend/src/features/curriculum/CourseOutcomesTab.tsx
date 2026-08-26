import * as React from 'react'
import { ArrowRight, Plus } from 'lucide-react'
import { toast } from 'sonner'
import { z } from 'zod'

import { useAuth } from '@/features/auth/useAuth'
import type { Course, CourseOutcome, CourseVersion } from '@/features/curriculum/types'
import { ApiError } from '@/lib/api-client'
import { useEntityAction, useEntityCreate, useEntityList, useEntityUpdate } from '@/lib/crud-hooks'
import { useResetOnChange } from '@/lib/use-reset-on-change'
import { Button } from '@/components/ui/button'
import { DataTable, type DataTableColumn } from '@/components/data-table'
import { EntityFormDialog, type EntityField } from '@/components/entity-form-dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { StatusBadge, WORKFLOW_NEXT, type WorkflowStatus } from '@/components/status-badge'

const schema = z.object({
  code: z.string().min(1, 'Code is required').max(20),
  statement: z.string().min(1, 'Statement is required'),
  sequence: z.coerce.number().int(),
  bloom_target_level_id: z.string().optional(),
})

/** Course Outcomes, scoped to course -> course version. bloom_target_level_id
 * has no seeded options yet (Bloom levels table exists but nothing seeds
 * default rows into it — out of scope here per the task brief), so that
 * field gracefully shows "None available yet" via EntityFormDialog's empty
 * select state rather than crashing. */
export function CourseOutcomesTab() {
  const { hasPermission } = useAuth()
  const canManage = hasPermission('outcome.create')
  const canApprove = hasPermission('outcome.approve')
  const [courseId, setCourseId] = React.useState('')
  const [createOpen, setCreateOpen] = React.useState(false)
  const [editCO, setEditCO] = React.useState<CourseOutcome | null>(null)

  const { data: courses } = useEntityList<Course>(['curriculum', 'courses'], '/curriculum/courses')
  const { data: versions } = useEntityList<CourseVersion>(
    ['curriculum', 'course-versions', courseId],
    '/curriculum/course-versions',
    { course_id: courseId || undefined },
    { enabled: Boolean(courseId) },
  )

  const [courseVersionId, setCourseVersionId] = useResetOnChange(courseId, '')

  const {
    data: outcomes,
    isLoading,
    error,
  } = useEntityList<CourseOutcome>(
    ['curriculum', 'course-outcomes', courseVersionId],
    '/curriculum/course-outcomes',
    { course_version_id: courseVersionId || undefined },
    { enabled: Boolean(courseVersionId) },
  )
  const create = useEntityCreate<Record<string, unknown>, CourseOutcome>(
    '/curriculum/course-outcomes',
    [['curriculum', 'course-outcomes', courseVersionId]],
  )
  const update = useEntityUpdate<Record<string, unknown>, CourseOutcome>(
    (id) => `/curriculum/course-outcomes/${id}`,
    [['curriculum', 'course-outcomes', courseVersionId]],
  )
  const advance = useEntityAction<CourseOutcome>(
    (id) => `/curriculum/course-outcomes/${id}/advance`,
    [['curriculum', 'course-outcomes', courseVersionId]],
  )

  const fields: EntityField[] = [
    { name: 'code', label: 'Code', type: 'text', placeholder: 'e.g. CO1' },
    { name: 'statement', label: 'Statement', type: 'textarea' },
    { name: 'sequence', label: 'Sequence', type: 'number' },
    { name: 'bloom_target_level_id', label: 'Target Bloom level', type: 'select', options: [] },
  ]

  const columns: DataTableColumn<CourseOutcome>[] = [
    { key: 'code', header: 'Code', render: (r) => r.code },
    { key: 'statement', header: 'Statement', render: (r) => r.statement, className: 'max-w-md' },
    { key: 'sequence', header: 'Seq', render: (r) => r.sequence },
    { key: 'status', header: 'Status', render: (r) => <StatusBadge status={r.status} /> },
  ]

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap gap-2">
          <div className="w-64">
            <Select value={courseId} onValueChange={setCourseId}>
              <SelectTrigger>
                <SelectValue placeholder="Select a course" />
              </SelectTrigger>
              <SelectContent>
                {(courses ?? []).map((c) => (
                  <SelectItem key={c.id} value={c.id}>
                    {c.code} — {c.title}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="w-48">
            <Select value={courseVersionId} onValueChange={setCourseVersionId} disabled={!courseId}>
              <SelectTrigger>
                <SelectValue placeholder="Select a version" />
              </SelectTrigger>
              <SelectContent>
                {(versions ?? []).map((v) => (
                  <SelectItem key={v.id} value={v.id}>
                    {v.version_label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
        {canManage && courseVersionId && (
          <Button size="sm" onClick={() => setCreateOpen(true)}>
            <Plus className="size-4" /> New course outcome
          </Button>
        )}
      </div>

      {!courseVersionId ? (
        <p className="text-sm text-muted-foreground">
          Select a course and version to see its course outcomes.
        </p>
      ) : (
        <DataTable
          data={outcomes}
          columns={columns}
          rowKey={(r) => r.id}
          isLoading={isLoading}
          error={error}
          emptyMessage="No course outcomes yet for this version."
          onRowClick={canManage ? (r) => setEditCO(r) : undefined}
          actions={(r) => {
            const next = WORKFLOW_NEXT[r.status as WorkflowStatus]
            if (!canApprove || !next) return null
            return (
              <Button
                size="sm"
                variant="outline"
                onClick={async () => {
                  try {
                    await advance.mutateAsync(r.id)
                    toast.success(`Advanced to ${next}`)
                  } catch (err) {
                    toast.error(err instanceof ApiError ? err.detail : 'Unable to advance.')
                  }
                }}
              >
                Advance to {next} <ArrowRight className="size-3.5" />
              </Button>
            )
          }}
        />
      )}

      <EntityFormDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        title="New course outcome"
        fields={fields}
        schema={schema}
        defaultValues={{ code: '', statement: '', sequence: 1, bloom_target_level_id: '' }}
        onSubmit={async (values) => {
          try {
            await create.mutateAsync({
              course_version_id: courseVersionId,
              code: values.code,
              statement: values.statement,
              sequence: values.sequence,
              bloom_target_level_id: values.bloom_target_level_id || null,
            })
            toast.success('Course outcome created')
          } catch (err) {
            throw err instanceof ApiError ? err : new ApiError('Unable to create course outcome.')
          }
        }}
      />

      {editCO && (
        <EntityFormDialog
          open={Boolean(editCO)}
          onOpenChange={(open) => !open && setEditCO(null)}
          title={`Edit ${editCO.code}`}
          fields={fields}
          schema={schema}
          defaultValues={{
            code: editCO.code,
            statement: editCO.statement,
            sequence: editCO.sequence,
            bloom_target_level_id: editCO.bloom_target_level_id ?? '',
          }}
          onSubmit={async (values) => {
            try {
              await update.mutateAsync({
                id: editCO.id,
                body: {
                  code: values.code,
                  statement: values.statement,
                  sequence: values.sequence,
                  bloom_target_level_id: values.bloom_target_level_id || null,
                },
              })
              toast.success('Course outcome updated')
            } catch (err) {
              throw err instanceof ApiError ? err : new ApiError('Unable to update course outcome.')
            }
          }}
        />
      )}
    </div>
  )
}
