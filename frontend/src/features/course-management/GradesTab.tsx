import { AlertTriangle, CheckCircle2, Lock } from 'lucide-react'
import { toast } from 'sonner'

import type { GradeSheetReport } from '@/features/course-management/types'
import type { MyCourseCard } from '@/features/course-management/types'
import { ApiError, apiClient } from '@/lib/api-client'
import { useEntityGet } from '@/lib/crud-hooks'
import { useQueryClient } from '@tanstack/react-query'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ConfirmAction } from '@/components/confirm-action'
import { Skeleton } from '@/components/ui/skeleton'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

/** Faculty Module spec §21-24: consolidated grade sheet, Save happens
 * implicitly via Marks Entry (this tab is a computed view), and Submit
 * Final Grades locks the section and triggers the CO attainment snapshot. */
export function GradesTab({ course }: { course: MyCourseCard }) {
  const queryClient = useQueryClient()
  const queryKey = ['marks', 'grade-sheet', course.course_section_id]
  const { data: sheet, isLoading } = useEntityGet<GradeSheetReport>(
    queryKey,
    `/marks/grade-sheet?course_section_id=${course.course_section_id}`,
  )

  if (isLoading || !sheet) return <Skeleton className="h-64 w-full" />

  const isSubmitted = sheet.submission_status === 'submitted'
  const canSubmit =
    sheet.weight_complete && sheet.marks_complete && !isSubmitted && course.is_current_term

  async function handleSubmit() {
    try {
      await apiClient.post(`/marks/sections/${course.course_section_id}/grades/submit`)
      toast.success('Final grades submitted — CO attainment has been calculated.')
      await queryClient.invalidateQueries({ queryKey })
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Submission failed')
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <Card
        className={
          isSubmitted
            ? 'border-emerald-500/30 bg-emerald-500/5'
            : canSubmit
              ? 'border-primary/30 bg-primary/5'
              : 'border-warning/30 bg-warning/5'
        }
      >
        <CardContent className="flex flex-wrap items-center justify-between gap-3 py-4">
          <div className="flex items-center gap-3">
            {isSubmitted ? (
              <Lock className="size-5 text-emerald-600" />
            ) : canSubmit ? (
              <CheckCircle2 className="size-5 text-primary" />
            ) : (
              <AlertTriangle className="size-5 text-warning" />
            )}
            <div>
              <p className="text-sm font-medium">
                {isSubmitted
                  ? `Final grades submitted ${sheet.submitted_at ? new Date(sheet.submitted_at).toLocaleString() : ''}`
                  : !course.is_current_term
                    ? 'Read-only — this course is from a previous semester.'
                    : canSubmit
                      ? 'All assessments recorded — ready to submit.'
                      : !sheet.weight_complete
                        ? `Assessment weights total ${sheet.weight_recorded_percent}%, not 100%.`
                        : `Marks missing for: ${sheet.incomplete_assessment_titles.join(', ')}`}
              </p>
              {!isSubmitted && course.is_current_term && (
                <p className="text-xs text-muted-foreground">
                  Once submitted, marks and grades for this section can no longer be modified.
                </p>
              )}
            </div>
          </div>
          {!isSubmitted && (
            <ConfirmAction
              trigger={<Button disabled={!canSubmit}>Submit Final Grades</Button>}
              title="Submit final grades?"
              description="This locks marks entry for this section and calculates CO attainment. This cannot be undone."
              confirmLabel="Submit"
              variant="default"
              onConfirm={handleSubmit}
            />
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Grade sheet</CardTitle>
          <CardDescription>
            Weighted totals computed from recorded marks and the applicable grading policy.
          </CardDescription>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Student</TableHead>
                {sheet.rows[0]?.assessments.map((a) => (
                  <TableHead key={a.assessment_id} className="text-right">
                    {a.title}
                  </TableHead>
                ))}
                <TableHead className="text-right">Total %</TableHead>
                <TableHead className="text-right">Grade</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {sheet.rows.map((row) => (
                <TableRow key={row.student_enrollment_id}>
                  <TableCell className="font-medium">{row.student_name}</TableCell>
                  {row.assessments.map((a) => (
                    <TableCell key={a.assessment_id} className="text-right tabular-nums">
                      {a.marks_obtained}/{a.max_marks}
                    </TableCell>
                  ))}
                  <TableCell className="text-right tabular-nums">
                    {row.overall_percent ?? '—'}
                  </TableCell>
                  <TableCell className="text-right">
                    {row.letter_grade ? (
                      <Badge variant="secondary" className="font-normal">
                        {row.letter_grade}
                      </Badge>
                    ) : (
                      '—'
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}
