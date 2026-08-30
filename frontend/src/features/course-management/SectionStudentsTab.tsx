import * as React from 'react'
import { Plus, Search, Trash2 } from 'lucide-react'
import { toast } from 'sonner'

import type { Student, StudentEnrollment } from '@/features/academic-ops/types'
import type { MyCourseCard } from '@/features/course-management/types'
import { ApiError, apiClient } from '@/lib/api-client'
import { useEntityCreate, useEntityDelete, useEntityList } from '@/lib/crud-hooks'
import { useResetOnChange } from '@/lib/use-reset-on-change'
import { Button } from '@/components/ui/button'
import { ConfirmAction } from '@/components/confirm-action'
import { DataTable, type DataTableColumn } from '@/components/data-table'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'

interface EnrolledRow {
  enrollment: StudentEnrollment
  student: Student | undefined
}

/** Faculty Module spec §10-10.1: course/section-scoped enrollment — the
 * faculty-facing replacement for the institution-wide Academic Operations
 * module, which they don't have access to. */
export function SectionStudentsTab({ course }: { course: MyCourseCard }) {
  const [addOpen, setAddOpen] = React.useState(false)

  const { data: enrollments, isLoading } = useEntityList<StudentEnrollment>(
    ['academic', 'enrollments', course.course_section_id],
    '/academic/enrollments',
    { course_section_id: course.course_section_id },
  )
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
        <Button size="sm" onClick={() => setAddOpen(true)}>
          <Plus className="size-4" /> Add student
        </Button>
      </div>

      <DataTable
        data={rows}
        columns={columns}
        rowKey={(r) => r.enrollment.id}
        isLoading={isLoading}
        searchable
        searchPlaceholder="Search enrolled students…"
        emptyMessage="No students enrolled in this section yet."
        actions={(r) => (
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
        )}
      />

      <AddStudentDialog
        open={addOpen}
        onOpenChange={setAddOpen}
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
  const [query, setQuery] = useResetOnChange(open, '')
  const [results, setResults] = React.useState<Student[]>([])
  const [isSearching, setIsSearching] = React.useState(false)
  const create = useEntityCreate<Record<string, unknown>>('/academic/enrollments', [
    ['academic', 'enrollments', courseSectionId],
  ])

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
  // Rendered instead of `results` directly so clearing the search box hides
  // stale matches without needing a setState call in the effect above.
  const visibleResults = trimmedQuery.length < 2 ? [] : results

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
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Add student to section</DialogTitle>
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
                <Button size="sm" disabled={enrolled} onClick={() => void handleEnroll(s)}>
                  {enrolled ? 'Enrolled' : 'Add'}
                </Button>
              </div>
            )
          })}
        </div>
      </DialogContent>
    </Dialog>
  )
}
