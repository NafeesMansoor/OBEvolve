import * as React from 'react'
import { Plus, Search, Trash2 } from 'lucide-react'
import { toast } from 'sonner'

import type { Student, StudentEnrollment } from '@/features/academic-ops/types'
import { useAuth } from '@/features/auth/useAuth'
import type { CourseChangeRequest } from '@/features/change-requests/types'
import { ChangeRequestRow } from '@/features/change-requests/ChangeRequestRow'
import { GreenEditButton } from '@/features/course-management/GreenEditButton'
import type { MyCourseCard } from '@/features/course-management/types'
import { ApiError, apiClient } from '@/lib/api-client'
import { useEntityCreate, useEntityDelete, useEntityGet, useEntityList } from '@/lib/crud-hooks'
import { useResetOnChange } from '@/lib/use-reset-on-change'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ConfirmAction } from '@/components/confirm-action'
import { DataTable, type DataTableColumn } from '@/components/data-table'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableHead, TableHeader, TableRow } from '@/components/ui/table'

interface EnrolledRow {
  enrollment: StudentEnrollment
  student: Student | undefined
}

/** Faculty Module spec §10-10.1 + Course-Level Settings spec §2/§4/§11: a
 * section authority (Program Coordinator, Program/Course Administrator —
 * `section.manage`) still adds/removes students directly, exactly as
 * before. A personally-assigned Course Teacher instead proposes the change
 * (single-stage — Course Administrator finalizes) once "Students" is
 * enabled for this course's type; the backend enforces this identically
 * via `ensure_direct_enrollment_write_allowed`, this is just the UI
 * consequence of that gate. */
export function SectionStudentsTab({ course }: { course: MyCourseCard }) {
  const { hasPermission } = useAuth()
  // Same signal the backend's `is_section_authority` check is built on
  // (see app.services.faculty_scope's module docstring) — a scoped-only
  // grant is the one edge case this can under-detect, which just means
  // such a caller sees the propose flow instead of direct-write (safe).
  const isAuthority = hasPermission('section.manage')
  const [addOpen, setAddOpen] = React.useState(false)
  const [proposeOpen, setProposeOpen] = React.useState(false)

  const { data: enrollments, isLoading } = useEntityList<StudentEnrollment>(
    ['academic', 'enrollments', course.course_section_id],
    '/academic/enrollments',
    { course_section_id: course.course_section_id },
  )
  const { data: sectionConfig } = useEntityGet<Record<string, boolean>>(
    ['course-types', 'resolve', course.course_section_id],
    `/course-types/resolve/${course.course_section_id}`,
  )
  const studentsEnabled = sectionConfig?.students ?? false

  const { data: requests, isLoading: requestsLoading } = useEntityList<CourseChangeRequest>(
    ['course-change-requests', course.course_section_id, 'students'],
    '/course-change-requests',
    { course_section_id: course.course_section_id },
  )
  const studentRequests = (requests ?? []).filter((r) => r.section_key === 'students')
  const proposeChange = useEntityCreate<Record<string, unknown>>('/course-change-requests', [
    ['course-change-requests', course.course_section_id],
  ])

  const studentIds = React.useMemo(
    () => (enrollments ?? []).map((e) => e.student_user_id),
    [enrollments],
  )
  const [students, setStudents] = React.useState<Record<string, Student>>({})
  React.useEffect(() => {
    let cancelled = false
    async function loadNames() {
      const missing = studentIds.filter((id) => !students[id])
      if (missing.length === 0) return
      const results = await Promise.all(
        missing.map((id) =>
          apiClient
            .get<Student>(`/academic/students/${id}`)
            .then((r) => r.data)
            .catch(() => null),
        ),
      )
      if (cancelled) return
      setStudents((prev) => {
        const next = { ...prev }
        for (const s of results) if (s) next[s.user_id] = s
        return next
      })
    }
    void loadNames()
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [studentIds.join(',')])

  const deleteEnrollment = useEntityDelete((id) => `/academic/enrollments/${id}`, [
    ['academic', 'enrollments', course.course_section_id],
  ])

  async function proposeDrop(enrollment: StudentEnrollment, studentName: string) {
    try {
      await proposeChange.mutateAsync({
        course_section_id: course.course_section_id,
        section_key: 'students',
        target_field: 'enrollment_drop',
        proposed_value_json: { action: 'drop', enrollment_id: enrollment.id, status: 'withdrawn' },
        reason: `Remove ${studentName} from the section`,
      })
      toast.success('Removal request submitted for approval')
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Failed to submit request')
    }
  }

  const rows: EnrolledRow[] = (enrollments ?? []).map((enrollment) => ({
    enrollment,
    student: students[enrollment.student_user_id],
  }))

  const columns: DataTableColumn<EnrolledRow>[] = [
    {
      key: 'student_code',
      header: 'Student ID',
      render: (r) => r.student?.student_code ?? '—',
      searchValue: (r) => r.student?.student_code ?? '',
    },
    {
      key: 'name',
      header: 'Student name',
      render: (r) => r.student?.full_name ?? r.enrollment.student_user_id,
      searchValue: (r) => r.student?.full_name ?? '',
    },
    {
      key: 'status',
      header: 'Enrollment status',
      render: (r) => <span className="capitalize">{r.enrollment.enrollment_status}</span>,
    },
  ]

  return (
    <div className="flex flex-col gap-4">
      <div className="flex justify-end">
        {isAuthority ? (
          <Button size="sm" onClick={() => setAddOpen(true)}>
            <Plus className="size-4" /> Add student
          </Button>
        ) : (
          <GreenEditButton
            enabled={studentsEnabled}
            onClick={() => setProposeOpen(true)}
            label="Propose enrollment change"
          />
        )}
      </div>

      <DataTable
        data={rows}
        columns={columns}
        rowKey={(r) => r.enrollment.id}
        isLoading={isLoading}
        searchable
        searchPlaceholder="Search enrolled students…"
        emptyMessage="No students enrolled in this section yet."
        actions={(r) =>
          isAuthority ? (
            <ConfirmAction
              trigger={
                <Button size="sm" variant="outline">
                  <Trash2 className="size-4" /> Remove
                </Button>
              }
              title="Remove student from section?"
              description={`${r.student?.full_name ?? 'This student'} will be unenrolled from this section.`}
              confirmLabel="Remove"
              onConfirm={async () => {
                try {
                  await deleteEnrollment.mutateAsync(r.enrollment.id)
                  toast.success('Student removed')
                } catch (err) {
                  toast.error(err instanceof ApiError ? err.detail : 'Failed to remove student')
                }
              }}
            />
          ) : studentsEnabled ? (
            <ConfirmAction
              trigger={
                <Button size="sm" variant="outline">
                  <Trash2 className="size-4" /> Propose removal
                </Button>
              }
              title="Propose removing this student?"
              description={`Your Course Administrator will review removing ${r.student?.full_name ?? 'this student'}.`}
              confirmLabel="Submit"
              onConfirm={() => proposeDrop(r.enrollment, r.student?.full_name ?? 'this student')}
            />
          ) : undefined
        }
      />

      {!isAuthority && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Enrollment change requests</CardTitle>
            <CardDescription>
              {studentsEnabled
                ? 'Submitted requests go to your Course Administrator for approval.'
                : 'Enrollment changes are not enabled for this course type.'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {requestsLoading ? (
              <p className="text-sm text-muted-foreground">Loading…</p>
            ) : studentRequests.length === 0 ? (
              <p className="text-sm text-muted-foreground">No change requests submitted yet.</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Field</TableHead>
                    <TableHead>Current</TableHead>
                    <TableHead>Proposed</TableHead>
                    <TableHead>Edited</TableHead>
                    <TableHead>Reason</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Submitted</TableHead>
                    <TableHead className="text-right">Review</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {studentRequests.map((r) => (
                    <ChangeRequestRow key={r.id} request={r} />
                  ))}
                </TableBody>
              </Table>
            )}
          </CardContent>
        </Card>
      )}

      <AddStudentDialog
        open={addOpen}
        onOpenChange={setAddOpen}
        courseSectionId={course.course_section_id}
        alreadyEnrolled={new Set(studentIds)}
      />
      <ProposeAddStudentDialog
        open={proposeOpen}
        onOpenChange={setProposeOpen}
        courseSectionId={course.course_section_id}
        alreadyEnrolled={new Set(studentIds)}
      />
    </div>
  )
}

function AddStudentDialog({
  open,
  onOpenChange,
  courseSectionId,
  alreadyEnrolled,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  courseSectionId: string
  alreadyEnrolled: Set<string>
}) {
  const create = useEntityCreate<Record<string, unknown>>('/academic/enrollments', [
    ['academic', 'enrollments', courseSectionId],
  ])
  async function handleEnroll(student: Student) {
    try {
      await create.mutateAsync({
        student_user_id: student.user_id,
        course_section_id: courseSectionId,
      })
      toast.success(`${student.full_name} enrolled`)
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Failed to enroll student')
    }
  }
  return (
    <StudentSearchDialog
      open={open}
      onOpenChange={onOpenChange}
      title="Add student to section"
      alreadyEnrolled={alreadyEnrolled}
      actionLabel="Add"
      onSelect={handleEnroll}
    />
  )
}

function ProposeAddStudentDialog({
  open,
  onOpenChange,
  courseSectionId,
  alreadyEnrolled,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  courseSectionId: string
  alreadyEnrolled: Set<string>
}) {
  const propose = useEntityCreate<Record<string, unknown>>('/course-change-requests', [
    ['course-change-requests', courseSectionId],
  ])
  async function handlePropose(student: Student) {
    try {
      await propose.mutateAsync({
        course_section_id: courseSectionId,
        section_key: 'students',
        target_field: 'enrollment_add',
        proposed_value_json: { action: 'add', student_user_id: student.user_id },
        reason: `Enroll ${student.full_name}`,
      })
      toast.success(`Enrollment request submitted for ${student.full_name}`)
      onOpenChange(false)
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Failed to submit request')
    }
  }
  return (
    <StudentSearchDialog
      open={open}
      onOpenChange={onOpenChange}
      title="Propose adding a student"
      alreadyEnrolled={alreadyEnrolled}
      actionLabel="Propose"
      onSelect={handlePropose}
    />
  )
}

function StudentSearchDialog({
  open,
  onOpenChange,
  title,
  alreadyEnrolled,
  actionLabel,
  onSelect,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  alreadyEnrolled: Set<string>
  actionLabel: string
  onSelect: (student: Student) => void | Promise<void>
}) {
  const [query, setQuery] = useResetOnChange(open, '')
  const [results, setResults] = React.useState<Student[]>([])
  const [isSearching, setIsSearching] = React.useState(false)

  const trimmedQuery = query.trim()
  React.useEffect(() => {
    if (trimmedQuery.length < 2) return
    let cancelled = false
    const handle = setTimeout(() => {
      if (cancelled) return
      setIsSearching(true)
      apiClient
        .get<Student[]>('/academic/students/search', { params: { q: trimmedQuery } })
        .then((res) => {
          if (!cancelled) setResults(res.data)
        })
        .catch(() => {
          if (!cancelled) setResults([])
        })
        .finally(() => {
          if (!cancelled) setIsSearching(false)
        })
    }, 300)
    return () => {
      cancelled = true
      clearTimeout(handle)
    }
  }, [trimmedQuery])
  const visibleResults = trimmedQuery.length < 2 ? [] : results

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
        </DialogHeader>
        <div className="relative">
          <Search className="absolute left-2.5 top-2.5 size-4 text-muted-foreground" />
          <Input
            className="pl-8"
            placeholder="Search by name, email, or student ID…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            autoFocus
          />
        </div>
        <div className="flex max-h-72 flex-col gap-1 overflow-y-auto">
          {isSearching && <p className="py-4 text-center text-sm text-muted-foreground">Searching…</p>}
          {!isSearching && trimmedQuery.length >= 2 && visibleResults.length === 0 && (
            <p className="py-4 text-center text-sm text-muted-foreground">No students found.</p>
          )}
          {visibleResults.map((s) => {
            const enrolled = alreadyEnrolled.has(s.user_id)
            return (
              <div
                key={s.user_id}
                className="flex items-center justify-between gap-2 rounded-md border p-2"
              >
                <div className="flex flex-col text-sm">
                  <span className="font-medium">{s.full_name}</span>
                  <span className="text-xs text-muted-foreground">
                    {s.student_code} · {s.email}
                  </span>
                </div>
                <Button size="sm" disabled={enrolled} onClick={() => void onSelect(s)}>
                  {enrolled ? 'Enrolled' : actionLabel}
                </Button>
              </div>
            )
          })}
        </div>
      </DialogContent>
    </Dialog>
  )
}
