import * as React from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { Plus, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { z } from 'zod'

import { useAuth } from '@/features/auth/useAuth'
import { useAcademicTermLookup, useCourseVersionLookup } from '@/features/academic-ops/useLookups'
import type { CourseOffering, CourseSection, Student, StudentEnrollment } from '@/features/academic-ops/types'
import { ApiError, apiClient } from '@/lib/api-client'
import { useEntityCreate, useEntityDelete, useEntityList } from '@/lib/crud-hooks'
import { useResetOnChange } from '@/lib/use-reset-on-change'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ConfirmAction } from '@/components/confirm-action'
import { DataTable, type DataTableColumn } from '@/components/data-table'
import { EntityFormDialog, type EntityField } from '@/components/entity-form-dialog'
import { RecordDetailSheet } from '@/components/record-detail-sheet'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

const ENROLLMENT_STATUSES = ['enrolled', 'completed', 'withdrawn', 'incomplete', 'failed']

const schema = z.object({
  student_user_id: z.string().min(1, 'Student is required'),
  enrollment_status: z.string().min(1),
})

export function EnrollmentsTab() {
  const { hasPermission } = useAuth()
  const canManage = hasPermission('student.manage')
  const queryClient = useQueryClient()
  const { labelFor } = useCourseVersionLookup()
  const { termById } = useAcademicTermLookup()

  const { data: offerings } = useEntityList<CourseOffering>(
    ['academic', 'course-offerings'],
    '/academic/course-offerings',
  )
  const [offeringId, setOfferingId] = React.useState('')
  const { data: sections } = useEntityList<CourseSection>(
    ['academic', 'sections', offeringId],
    '/academic/sections',
    { course_offering_id: offeringId || undefined },
    { enabled: Boolean(offeringId) },
  )
  const [sectionId, setSectionId] = useResetOnChange(offeringId, '')

  const { data: students } = useEntityList<Student>(['academic', 'students'], '/academic/students')
  const studentById = React.useMemo(
    () => new Map((students ?? []).map((s) => [s.user_id, s])),
    [students],
  )

  const [createOpen, setCreateOpen] = React.useState(false)
  const [viewEnrollment, setViewEnrollment] = React.useState<StudentEnrollment | null>(null)

  const {
    data: enrollments,
    isLoading,
    error,
  } = useEntityList<StudentEnrollment>(
    ['academic', 'enrollments', sectionId],
    '/academic/enrollments',
    { course_section_id: sectionId || undefined },
    { enabled: Boolean(sectionId) },
  )
  const create = useEntityCreate<Record<string, unknown>, StudentEnrollment>(
    '/academic/enrollments',
    [['academic', 'enrollments', sectionId]],
  )
  const remove = useEntityDelete((id) => `/academic/enrollments/${id}`, [
    ['academic', 'enrollments', sectionId],
  ])

  async function updateStatus(enrollmentId: string, status: string) {
    try {
      // Note: this endpoint takes enrollment_status as a query param, not a
      // JSON body (app/api/v1/endpoints/academic_ops.py update_enrollment_status
      // declares it as a plain str param, which FastAPI binds from the query
      // string since there's no request-body model here).
      await apiClient.patch(`/academic/enrollments/${enrollmentId}`, null, {
        params: { enrollment_status: status },
      })
      void queryClient.invalidateQueries({ queryKey: ['academic', 'enrollments', sectionId] })
      toast.success('Enrollment status updated')
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Unable to update status.')
    }
  }

  const offeringOptions = React.useMemo(
    () =>
      (offerings ?? []).map((o) => ({
        label: `${labelFor(o.course_version_id)} · ${termById.get(o.academic_term_id)?.name ?? ''}`,
        value: o.id,
      })),
    [offerings, labelFor, termById],
  )

  const fields: EntityField[] = [
    {
      name: 'student_user_id',
      label: 'Student',
      type: 'select',
      options: (students ?? []).map((s) => ({
        label: `${s.full_name} (${s.student_code})`,
        value: s.user_id,
      })),
    },
    {
      name: 'enrollment_status',
      label: 'Status',
      type: 'select',
      options: ENROLLMENT_STATUSES.map((s) => ({ label: s, value: s })),
    },
  ]

  const columns: DataTableColumn<StudentEnrollment>[] = [
    {
      key: 'student',
      header: 'Student',
      render: (r) => studentById.get(r.student_user_id)?.full_name ?? r.student_user_id,
    },
    {
      key: 'status',
      header: 'Status',
      render: (r) => (
        <div onClick={(e) => e.stopPropagation()}>
          <Select
            value={r.enrollment_status}
            onValueChange={(v) => updateStatus(r.id, v)}
            disabled={!canManage}
          >
            <SelectTrigger className="h-7 w-36">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {ENROLLMENT_STATUSES.map((s) => (
                <SelectItem key={s} value={s}>
                  {s}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      ),
    },
    {
      key: 'enrolled_at',
      header: 'Enrolled',
      render: (r) => <Badge variant="outline">{new Date(r.enrolled_at).toLocaleDateString()}</Badge>,
    },
  ]

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap gap-2">
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
        <div className="w-40">
          <Select value={sectionId} onValueChange={setSectionId} disabled={!offeringId}>
            <SelectTrigger>
              <SelectValue placeholder="Section" />
            </SelectTrigger>
            <SelectContent>
              {(sections ?? []).map((s) => (
                <SelectItem key={s.id} value={s.id}>
                  {s.section_code}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        {canManage && sectionId && (
          <Button size="sm" onClick={() => setCreateOpen(true)}>
            <Plus className="size-4" /> Enroll student
          </Button>
        )}
      </div>

      {!sectionId ? (
        <p className="text-sm text-muted-foreground">Select an offering and section to see enrollments.</p>
      ) : (
        <DataTable
          data={enrollments}
          columns={columns}
          rowKey={(r) => r.id}
          isLoading={isLoading}
          error={error}
          emptyMessage="No enrollments yet for this section."
          onRowClick={(r) => setViewEnrollment(r)}
          actions={
            canManage
              ? (r) => (
                  <ConfirmAction
                    trigger={
                      <Button size="sm" variant="ghost" aria-label="Remove enrollment">
                        <Trash2 className="size-4" />
                      </Button>
                    }
                    title="Remove this enrollment?"
                    onConfirm={async () => {
                      try {
                        await remove.mutateAsync(r.id)
                        toast.success('Enrollment removed')
                      } catch (err) {
                        toast.error(err instanceof ApiError ? err.detail : 'Unable to remove enrollment.')
                      }
                    }}
                  />
                )
              : undefined
          }
        />
      )}

      {viewEnrollment && (
        <RecordDetailSheet
          open={Boolean(viewEnrollment)}
          onOpenChange={(open) => !open && setViewEnrollment(null)}
          title={studentById.get(viewEnrollment.student_user_id)?.full_name ?? viewEnrollment.student_user_id}
          badge={
            <Badge variant="outline" className="font-normal capitalize">
              {viewEnrollment.enrollment_status}
            </Badge>
          }
          fields={[
            {
              label: 'Student code',
              value: studentById.get(viewEnrollment.student_user_id)?.student_code ?? '—',
            },
            { label: 'Status', value: <span className="capitalize">{viewEnrollment.enrollment_status}</span> },
            { label: 'Enrolled', value: new Date(viewEnrollment.enrolled_at).toLocaleDateString() },
          ]}
        />
      )}

      <EntityFormDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        title="Enroll student"
        fields={fields}
        schema={schema}
        defaultValues={{ student_user_id: '', enrollment_status: 'enrolled' }}
        onSubmit={async (values) => {
          try {
            await create.mutateAsync({
              student_user_id: values.student_user_id,
              course_section_id: sectionId,
              enrollment_status: values.enrollment_status,
            })
            toast.success('Student enrolled')
          } catch (err) {
            throw err instanceof ApiError ? err : new ApiError('Unable to enroll student.')
          }
        }}
      />
    </div>
  )
}
