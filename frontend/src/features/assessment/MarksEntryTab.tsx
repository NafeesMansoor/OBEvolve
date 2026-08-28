import * as React from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { Filter, Save } from 'lucide-react'
import { toast } from 'sonner'

import { useAuth } from '@/features/auth/useAuth'
import { useAcademicTermLookup, useCourseVersionLookup } from '@/features/academic-ops/useLookups'
import type { CourseOffering, CourseSection, Student, StudentEnrollment } from '@/features/academic-ops/types'
import type { Assessment, AssessmentQuestion, StudentMark } from '@/features/assessment/types'
import { ApiError, apiClient } from '@/lib/api-client'
import { useEntityList } from '@/lib/crud-hooks'
import { useResetOnChange } from '@/lib/use-reset-on-change'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'

function cellKey(enrollmentId: string, aqId: string) {
  return `${enrollmentId}::${aqId}`
}

/** Students × attached-questions grid for one assessment. Loads existing
 * `student_marks` (if any), lets Faculty/Course Coordinator (marks.enter)
 * type into cells, and submits every touched cell as one bulk upsert
 * (unique constraint on (assessment_question_id, student_enrollment_id)
 * makes each row an insert-or-update). */
export function MarksEntryTab() {
  const { hasPermission } = useAuth()
  const canEnter = hasPermission('marks.enter')

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

  const { data: assessments } = useEntityList<Assessment>(
    ['assessment', 'assessments', sectionId],
    '/assessment/assessments',
    { course_section_id: sectionId || undefined },
    { enabled: Boolean(sectionId) },
  )
  const [assessmentId, setAssessmentId] = useResetOnChange(sectionId, '')

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

  const { data: enrollments } = useEntityList<StudentEnrollment>(
    ['academic', 'enrollments', sectionId],
    '/academic/enrollments',
    { course_section_id: sectionId || undefined },
    { enabled: Boolean(sectionId) },
  )
  const { data: students } = useEntityList<Student>(['academic', 'students'], '/academic/students')
  const studentById = React.useMemo(
    () => new Map((students ?? []).map((s) => [s.user_id, s])),
    [students],
  )

  const { data: existingMarks } = useEntityList<StudentMark>(
    ['marks', 'student-marks', assessmentId],
    '/marks/student-marks',
    { assessment_id: assessmentId || undefined },
    { enabled: Boolean(assessmentId) },
  )

  const offeringOptions = React.useMemo(
    () =>
      (offerings ?? []).map((o) => ({
        label: `${labelFor(o.course_version_id)} · ${termById.get(o.academic_term_id)?.name ?? ''}`,
        value: o.id,
      })),
    [offerings, labelFor, termById],
  )

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
        <div className="w-64">
          <Select value={assessmentId} onValueChange={setAssessmentId} disabled={!sectionId}>
            <SelectTrigger>
              <SelectValue placeholder="Assessment" />
            </SelectTrigger>
            <SelectContent>
              {(assessments ?? []).map((a) => (
                <SelectItem key={a.id} value={a.id}>
                  {a.title}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {!assessmentId ? (
        <div className="flex flex-col items-center gap-2 rounded-md border border-dashed py-10 text-center text-muted-foreground">
          <Filter className="size-6 opacity-50" />
          <p className="text-sm">Select an offering, section, and assessment to enter marks.</p>
        </div>
      ) : sortedQuestions.length === 0 ? (
        <div className="flex flex-col items-center gap-2 rounded-md border border-dashed py-10 text-center text-muted-foreground">
          <Filter className="size-6 opacity-50" />
          <p className="text-sm">
            This assessment has no questions attached yet — attach questions from the Assessments tab first.
          </p>
        </div>
      ) : !enrollments?.length ? (
        <div className="flex flex-col items-center gap-2 rounded-md border border-dashed py-10 text-center text-muted-foreground">
          <Filter className="size-6 opacity-50" />
          <p className="text-sm">No students enrolled in this section yet.</p>
        </div>
      ) : existingMarks === undefined ? (
        <Skeleton className="h-64 w-full" />
      ) : (
        <MarksGrid
          key={assessmentId}
          assessmentId={assessmentId}
          questions={sortedQuestions}
          enrollments={enrollments}
          studentById={studentById}
          initialMarks={existingMarks}
          canEnter={canEnter}
        />
      )}
    </div>
  )
}

function buildInitialCells(marks: StudentMark[]): Record<string, string> {
  const cells: Record<string, string> = {}
  for (const mark of marks) {
    cells[cellKey(mark.student_enrollment_id, mark.assessment_question_id)] = mark.marks_obtained
  }
  return cells
}

function MarksGrid({
  assessmentId,
  questions,
  enrollments,
  studentById,
  initialMarks,
  canEnter,
}: {
  assessmentId: string
  questions: AssessmentQuestion[]
  enrollments: StudentEnrollment[]
  studentById: Map<string, Student>
  initialMarks: StudentMark[]
  canEnter: boolean
}) {
  const queryClient = useQueryClient()
  const [cells, setCells] = React.useState(() => buildInitialCells(initialMarks))
  const [saving, setSaving] = React.useState(false)

  async function save() {
    const entries = Object.entries(cells)
      .filter(([, v]) => v.trim() !== '')
      .map(([key, marks_obtained]) => {
        const [student_enrollment_id, assessment_question_id] = key.split('::')
        return { student_enrollment_id, assessment_question_id, marks_obtained }
      })
    if (entries.length === 0) {
      toast.error('Enter at least one mark before saving.')
      return
    }
    setSaving(true)
    try {
      await apiClient.post('/marks/student-marks/bulk', { entries })
      await queryClient.invalidateQueries({ queryKey: ['marks', 'student-marks', assessmentId] })
      toast.success(`Saved ${entries.length} mark${entries.length === 1 ? '' : 's'}`)
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Unable to save marks.')
    } finally {
      setSaving(false)
    }
  }

  const enteredCount = Object.values(cells).filter((v) => v.trim() !== '').length
  const totalCells = enrollments.length * questions.length

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-xs text-muted-foreground tabular-nums">
          {enteredCount} of {totalCells} cell{totalCells === 1 ? '' : 's'} entered
        </p>
        {canEnter && (
          <Button size="sm" onClick={() => void save()} disabled={saving}>
            <Save className="size-4" /> {saving ? 'Saving…' : 'Save marks'}
          </Button>
        )}
      </div>
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="sticky left-0 z-10 bg-muted/50">Student</TableHead>
              {questions.map((q) => (
                <TableHead key={q.id} className="whitespace-nowrap text-right">
                  Q{q.sequence} <span className="tabular-nums">({q.marks_allocated})</span>
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {enrollments.map((enrollment) => (
              <TableRow key={enrollment.id}>
                <TableCell className="sticky left-0 z-10 whitespace-nowrap bg-background py-1.5 font-medium">
                  {studentById.get(enrollment.student_user_id)?.full_name ?? enrollment.student_user_id}
                  {enrollment.enrollment_status !== 'enrolled' && (
                    <span className="ml-1 text-xs font-normal text-muted-foreground">
                      ({enrollment.enrollment_status})
                    </span>
                  )}
                </TableCell>
                {questions.map((q) => {
                  const key = cellKey(enrollment.id, q.id)
                  const value = cells[key] ?? ''
                  const hasValue = value.trim() !== ''
                  return (
                    <TableCell key={q.id} className="py-1.5">
                      <Input
                        type="number"
                        step="0.5"
                        min={0}
                        max={Number(q.marks_allocated)}
                        value={value}
                        onChange={(e) => setCells((prev) => ({ ...prev, [key]: e.target.value }))}
                        disabled={!canEnter}
                        aria-label={`Marks for ${studentById.get(enrollment.student_user_id)?.full_name ?? enrollment.student_user_id}, Q${q.sequence}`}
                        className={cn(
                          'ml-auto h-8 w-20 text-right tabular-nums',
                          hasValue
                            ? 'border-primary/40 bg-primary/5 font-medium'
                            : 'text-muted-foreground',
                        )}
                      />
                    </TableCell>
                  )
                })}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
