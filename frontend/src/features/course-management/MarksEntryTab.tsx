import * as React from 'react'
import { Save } from 'lucide-react'
import { toast } from 'sonner'

import type { Student, StudentEnrollment } from '@/features/academic-ops/types'
import type { Assessment, AssessmentQuestion, StudentMark } from '@/features/assessment/types'
import type { MyCourseCard } from '@/features/course-management/types'
import { ApiError, apiClient } from '@/lib/api-client'
import { useEntityList } from '@/lib/crud-hooks'
import { useResetOnChange } from '@/lib/use-reset-on-change'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

function cellKey(enrollmentId: string, aqId: string) {
  return `${enrollmentId}::${aqId}`
}

/** Faculty Module spec §20: current-semester-only marks entry, one
 * assessment at a time, saved as a single bulk upsert. */
export function MarksEntryTab({ course }: { course: MyCourseCard }) {
  const { data: assessments } = useEntityList<Assessment>(
    ['assessment', 'assessments', course.course_section_id],
    '/assessment/assessments',
    { course_section_id: course.course_section_id },
  )
  const [assessmentId, setAssessmentId] = useResetOnChange(course.course_section_id, '')

  const { data: enrollments } = useEntityList<StudentEnrollment>(
    ['academic', 'enrollments', course.course_section_id],
    '/academic/enrollments',
    { course_section_id: course.course_section_id },
  )
  const { data: questions } = useEntityList<AssessmentQuestion>(
    ['assessment', 'assessment-questions', assessmentId],
    '/assessment/assessment-questions',
    { assessment_id: assessmentId || undefined },
    { enabled: Boolean(assessmentId) },
  )
  const sortedQuestions = React.useMemo(
    () => (questions ?? []).slice().sort((a, b) => a.sequence - b.sequence),
    [questions],
  )
  const { data: marks, refetch: refetchMarks } = useEntityList<StudentMark>(
    ['assessment', 'student-marks', assessmentId],
    '/marks/student-marks',
    { assessment_id: assessmentId || undefined },
    { enabled: Boolean(assessmentId) },
  )

  const [names, setNames] = React.useState<Record<string, string>>({})
  React.useEffect(() => {
    let cancelled = false
    const ids = (enrollments ?? []).map((e) => e.student_user_id).filter((id) => !names[id])
    if (ids.length === 0) return
    void Promise.all(
      ids.map((id) =>
        apiClient
          .get<Student>(`/academic/students/${id}`)
          .then((r) => [id, r.data.full_name] as const)
          .catch(() => [id, id] as const),
      ),
    ).then((pairs) => {
      if (cancelled) return
      setNames((prev) => ({ ...prev, ...Object.fromEntries(pairs) }))
    })
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enrollments])

  const savedByKey = React.useMemo(() => {
    const map: Record<string, string> = {}
    for (const m of marks ?? []) {
      map[cellKey(m.student_enrollment_id, m.assessment_question_id)] = m.marks_obtained
    }
    return map
  }, [marks])
  // Local edits overlay the fetched marks rather than mirroring them into a
  // synced copy — resets automatically per-assessment since the key is
  // scoped to assessmentId (see useResetOnChange's doc comment on why an
  // effect+setState here would be the wrong pattern).
  const [edits, setEdits] = useResetOnChange<Record<string, string>>(assessmentId, {})
  const values = { ...savedByKey, ...edits }
  function setValue(key: string, value: string) {
    setEdits((prev) => ({ ...prev, [key]: value }))
  }

  const [isSaving, setIsSaving] = React.useState(false)

  async function handleSave() {
    if (!enrollments || !sortedQuestions.length) return
    const entries = enrollments.flatMap((enrollment) =>
      sortedQuestions
        .map((q) => {
          const raw = values[cellKey(enrollment.id, q.id)]
          if (raw === undefined || raw === '') return null
          return {
            assessment_question_id: q.id,
            student_enrollment_id: enrollment.id,
            marks_obtained: Number(raw),
          }
        })
        .filter((e): e is NonNullable<typeof e> => e !== null),
    )
    setIsSaving(true)
    try {
      await apiClient.post('/marks/student-marks/bulk', { entries })
      toast.success('Marks saved')
      await refetchMarks()
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Failed to save marks')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2">
        <Select value={assessmentId} onValueChange={setAssessmentId}>
          <SelectTrigger className="w-64">
            <SelectValue placeholder="Select an assessment" />
          </SelectTrigger>
          <SelectContent>
            {(assessments ?? []).map((a) => (
              <SelectItem key={a.id} value={a.id}>
                {a.title}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {assessmentId && sortedQuestions.length > 0 && course.is_current_term && (
          <Button onClick={handleSave} disabled={isSaving}>
            <Save className="size-4" /> {isSaving ? 'Saving…' : 'Save'}
          </Button>
        )}
        {assessmentId && !course.is_current_term && (
          <p className="text-sm text-muted-foreground">
            Read-only — this course is from a previous semester.
          </p>
        )}
      </div>

      {!assessmentId ? (
        <p className="text-sm text-muted-foreground">Select an assessment to enter marks.</p>
      ) : !questions ? (
        <Skeleton className="h-48 w-full" />
      ) : sortedQuestions.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          This assessment has no questions/tasks yet — add them under Assessments → Questions.
        </p>
      ) : (
        <div className="overflow-x-auto rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Student</TableHead>
                {sortedQuestions.map((q, i) => (
                  <TableHead key={q.id} className="text-right">
                    Q{i + 1} ({q.marks_allocated})
                  </TableHead>
                ))}
                <TableHead className="text-right">Total</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(enrollments ?? []).map((enrollment) => {
                const total = sortedQuestions.reduce(
                  (sum, q) => sum + Number(values[cellKey(enrollment.id, q.id)] || 0),
                  0,
                )
                return (
                  <TableRow key={enrollment.id}>
                    <TableCell className="font-medium">
                      {names[enrollment.student_user_id] ?? enrollment.student_user_id}
                    </TableCell>
                    {sortedQuestions.map((q) => {
                      const key = cellKey(enrollment.id, q.id)
                      return (
                        <TableCell key={q.id} className="text-right">
                          <Input
                            type="number"
                            className="h-8 w-16 text-right"
                            value={values[key] ?? ''}
                            onChange={(e) =>
                              setValue(key, e.target.value)
                            }
                          />
                        </TableCell>
                      )
                    })}
                    <TableCell className="text-right font-medium tabular-nums">{total}</TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  )
}
