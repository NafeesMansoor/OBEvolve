import type { CourseAttainmentReport } from '@/features/assessment/types'
import type { MyCourseCard } from '@/features/course-management/types'
import { useEntityGet } from '@/lib/crud-hooks'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

/** Faculty Module spec §25-29: course-level CO attainment for this section.
 * (Assessment-wise/grade-wise stats and PO attainment live in the
 * institution-wide Analytics module — this tab is the section-scoped slice
 * that's actually new here.) */
export function SectionAnalyticsTab({ course }: { course: MyCourseCard }) {
  const { data: report, isLoading } = useEntityGet<CourseAttainmentReport>(
    ['marks', 'attainment-report', course.course_section_id],
    `/marks/attainment-report?course_section_id=${course.course_section_id}`,
  )

  if (isLoading) return <Skeleton className="h-64 w-full" />
  if (!report) return null

  return (
    <div className="flex flex-col gap-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Course Outcome attainment</CardTitle>
          <CardDescription>
            {report.eligible_students} eligible students · threshold {report.min_marks_percent}%
            marks, {report.min_students_percent}% of students
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>CO</TableHead>
                <TableHead>Statement</TableHead>
                <TableHead className="text-right">Attainment</TableHead>
                <TableHead className="text-right">Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {report.outcomes.map((o) => (
                <TableRow key={o.course_outcome_id}>
                  <TableCell className="font-medium">{o.code}</TableCell>
                  <TableCell className="max-w-md truncate text-muted-foreground">
                    {o.statement}
                  </TableCell>
                  <TableCell className="text-right tabular-nums">
                    {o.attainment_percent ?? '—'}
                    {o.attainment_percent ? '%' : ''}
                  </TableCell>
                  <TableCell className="text-right">
                    {o.is_attained === null ? (
                      '—'
                    ) : (
                      <Badge
                        variant="outline"
                        className={
                          o.is_attained
                            ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300'
                            : 'bg-destructive/10 text-destructive'
                        }
                      >
                        {o.is_attained ? 'Achieved' : 'Not Achieved'}
                      </Badge>
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
