import * as React from 'react'
import { ArrowRight, Plus } from 'lucide-react'
import { toast } from 'sonner'
import { z } from 'zod'

import { useAuth } from '@/features/auth/useAuth'
import type { AcademicYear } from '@/features/organization/types'
import type { Course, CourseVersion } from '@/features/curriculum/types'
import { ApiError } from '@/lib/api-client'
import { useEntityAction, useEntityCreate, useEntityList } from '@/lib/crud-hooks'
import { Button } from '@/components/ui/button'
import { DataTable, type DataTableColumn } from '@/components/data-table'
import { EntityFormDialog, type EntityField } from '@/components/entity-form-dialog'
import { RecordDetailSheet } from '@/components/record-detail-sheet'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { StatusBadge, WORKFLOW_NEXT, type WorkflowStatus } from '@/components/status-badge'

export function CourseVersionsTab() {
  const { hasPermission } = useAuth()
  const canManage = hasPermission('outcome.create')
  const canApprove = hasPermission('outcome.approve')
  const [courseId, setCourseId] = React.useState<string>('')
  const [dialogOpen, setDialogOpen] = React.useState(false)
  const [viewVersion, setViewVersion] = React.useState<CourseVersion | null>(null)

  const { data: courses } = useEntityList<Course>(['curriculum', 'courses'], '/curriculum/courses')
  const { data: years } = useEntityList<AcademicYear>(
    ['org', 'academic-years'],
    '/org/academic-years',
  )
  const {
    data: versions,
    isLoading,
    error,
  } = useEntityList<CourseVersion>(
    ['curriculum', 'course-versions', courseId],
    '/curriculum/course-versions',
    { course_id: courseId || undefined },
    { enabled: Boolean(courseId) },
  )
  const create = useEntityCreate<Record<string, unknown>, CourseVersion>(
    '/curriculum/course-versions',
    [['curriculum', 'course-versions', courseId]],
  )
  const advance = useEntityAction<CourseVersion>(
    (id) => `/curriculum/course-versions/${id}/advance`,
    [['curriculum', 'course-versions', courseId]],
  )
  const yearById = React.useMemo(
    () => new Map((years ?? []).map((y) => [y.id, y])),
    [years],
  )
  const course = React.useMemo(() => (courses ?? []).find((c) => c.id === courseId), [courses, courseId])

  const fields: EntityField[] = [
    { name: 'version_label', label: 'Version label', type: 'text', placeholder: 'e.g. 2025-A' },
    {
      name: 'effective_academic_year_id',
      label: 'Effective academic year',
      type: 'select',
      options: (years ?? []).map((y) => ({ label: y.label, value: y.id })),
    },
  ]

  const columns: DataTableColumn<CourseVersion>[] = [
    { key: 'version_label', header: 'Version', render: (r) => r.version_label },
    { key: 'status', header: 'Status', render: (r) => <StatusBadge status={r.status} /> },
  ]

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="w-full max-w-xs">
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
        {canManage && courseId && (
          <Button size="sm" onClick={() => setDialogOpen(true)}>
            <Plus className="size-4" /> New version
          </Button>
        )}
      </div>

      {!courseId ? (
        <p className="text-sm text-muted-foreground">Select a course to see its versions.</p>
      ) : (
        <DataTable
          data={versions}
          columns={columns}
          rowKey={(r) => r.id}
          isLoading={isLoading}
          error={error}
          emptyMessage="No versions yet for this course."
          onRowClick={(r) => setViewVersion(r)}
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
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        title="New course version"
        fields={fields}
        schema={z.object({
          version_label: z.string().min(1, 'Version label is required').max(50),
          effective_academic_year_id: z.string().optional(),
        })}
        defaultValues={{ version_label: '', effective_academic_year_id: '' }}
        onSubmit={async (values) => {
          try {
            await create.mutateAsync({
              course_id: courseId,
              version_label: values.version_label,
              effective_academic_year_id: values.effective_academic_year_id || null,
            })
            toast.success('Course version created')
          } catch (err) {
            throw err instanceof ApiError ? err : new ApiError('Unable to create course version.')
          }
        }}
      />

      {viewVersion && (
        <RecordDetailSheet
          open={Boolean(viewVersion)}
          onOpenChange={(open) => !open && setViewVersion(null)}
          title={viewVersion.version_label}
          subtitle={course ? `${course.code} — ${course.title}` : undefined}
          badge={<StatusBadge status={viewVersion.status} />}
          fields={[
            {
              label: 'Effective academic year',
              value: viewVersion.effective_academic_year_id
                ? (yearById.get(viewVersion.effective_academic_year_id)?.label ?? '—')
                : '—',
            },
            { label: 'Status', value: viewVersion.status },
            { label: 'Created', value: new Date(viewVersion.created_at).toLocaleDateString() },
            { label: 'Last updated', value: new Date(viewVersion.updated_at).toLocaleDateString() },
          ]}
        />
      )}
    </div>
  )
}
