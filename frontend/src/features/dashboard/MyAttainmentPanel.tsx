import { AlertCircle, Inbox } from 'lucide-react'

import type { StudentAttainmentSummary } from '@/features/assessment/types'
import { ApiError } from '@/lib/api-client'
import { useEntityGet } from '@/lib/crud-hooks'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'

/** Student self-service dashboard (spec §14): marks, per-CO score/threshold/
 * status, and PO status — every value scoped to the signed-in student's own
 * enrollments via /marks/my-attainment (never takes a student id from the
 * client, so there's nothing here that could leak another student's data). */
export function MyAttainmentPanel() {
  const { data: programVersionId, isLoading: pvLoading } = useEntityGet<{
    program_version_id: string | null
  }>(['marks', 'my-program-version'], '/marks/my-program-version')

  const pvId = programVersionId?.program_version_id ?? null

  const {
    data: summary,
    isLoading,
    error,
  } = useEntityGet<StudentAttainmentSummary>(
    ['marks', 'my-attainment', pvId ?? ''],
    `/marks/my-attainment?program_version_id=${pvId ?? ''}`,
    { enabled: Boolean(pvId) },
  )

  if (pvLoading) {
    return (
      <div className="flex flex-col gap-4">
        <h2 className="text-lg font-semibold tracking-tight">My attainment</h2>
        <Skeleton className="h-40 w-full" />
      </div>
    )
  }
  if (!pvId) {
    return (
      <Card className="border-dashed">
        <CardContent className="flex flex-col items-center gap-3 py-12 text-center">
          <div className="flex size-12 items-center justify-center rounded-full bg-muted">
            <Inbox className="size-6 text-muted-foreground" />
          </div>
          <p className="max-w-sm text-sm text-muted-foreground">
            No program enrollment found on your student profile yet.
          </p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      <h2 className="text-lg font-semibold tracking-tight">My attainment</h2>

      {isLoading ? (
        <div className="flex flex-col gap-4">
          <Skeleton className="h-40 w-full" />
          <Skeleton className="h-32 w-full" />
        </div>
      ) : error ? (
        <div className="flex items-center gap-2 rounded-md border border-destructive/30 bg-destructive/5 px-4 py-3 text-sm text-destructive">
          <AlertCircle className="size-4 shrink-0" />
          {error instanceof ApiError ? error.detail : 'Unable to load your attainment.'}
        </div>
      ) : summary ? (
        <>
          <Card>
            <CardHeader>
              <CardTitle className="text-base">My program outcomes</CardTitle>
              <CardDescription>
                Based on the COs you've attained across your enrolled courses.
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>PO</TableHead>
                      <TableHead>Statement</TableHead>
                      <TableHead>COs attained</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {summary.po_status.map((po) => (
                      <TableRow key={po.program_outcome_id}>
                        <TableCell className="font-medium whitespace-nowrap">{po.code}</TableCell>
                        <TableCell>{po.statement}</TableCell>
                        <TableCell className="whitespace-nowrap">
                          {po.contributing_cos_total > 0
                            ? `${po.contributing_cos_attained} / ${po.contributing_cos_total}`
                            : '—'}
                        </TableCell>
                        <TableCell>
                          {po.attained === null ? (
                            <Badge variant="outline" className="font-normal">
                              Not assessed
                            </Badge>
                          ) : (
                            <Badge variant={po.attained ? 'secondary' : 'destructive'} className="font-normal">
                              {po.attained ? 'On track' : 'Below threshold'}
                            </Badge>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>

          {summary.enrollments.map((e) => (
            <Card key={e.course_section_id}>
              <CardHeader className="flex-row items-start justify-between gap-3 space-y-0">
                <div>
                  <CardTitle className="text-base">
                    {e.course_code} — {e.course_title}
                  </CardTitle>
                  <CardDescription>
                    {e.term_name} · Section {e.section_code} · {e.enrollment_status} · Total:{' '}
                    {e.total_obtained} / {e.total_max}
                  </CardDescription>
                </div>
                {e.letter_grade ? (
                  <div className="flex shrink-0 flex-col items-end">
                    <span className="font-display text-2xl font-bold leading-none tracking-tight tabular-nums">
                      {e.letter_grade}
                    </span>
                    {e.grade_point ? (
                      <span className="mt-1 text-xs text-muted-foreground tabular-nums">
                        {Number(e.grade_point).toFixed(2)} GP
                      </span>
                    ) : null}
                  </div>
                ) : (
                  <Badge variant="outline" className="shrink-0 font-normal">
                    Not yet graded
                  </Badge>
                )}
              </CardHeader>
              <CardContent className="flex flex-col gap-3">
                <div>
                  <p className="mb-1 text-xs font-medium text-muted-foreground">Assessments</p>
                  <div className="flex flex-wrap gap-2">
                    {e.assessments.map((a) => (
                      <Badge key={a.assessment_id} variant="outline" className="font-normal">
                        {a.title}: {a.obtained ?? '—'} / {a.max_marks}
                      </Badge>
                    ))}
                  </div>
                </div>
                <div>
                  <p className="mb-1 text-xs font-medium text-muted-foreground">Course outcomes</p>
                  <div className="overflow-x-auto rounded-md border">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>CO</TableHead>
                          <TableHead>Score</TableHead>
                          <TableHead>Threshold</TableHead>
                          <TableHead>Status</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {e.course_outcomes.map((co) => (
                          <TableRow key={co.course_outcome_id}>
                            <TableCell className="font-medium whitespace-nowrap">{co.code}</TableCell>
                            <TableCell>
                              {co.score_percent === null ? '—' : `${co.score_percent}%`}
                            </TableCell>
                            <TableCell>{co.threshold_percent}%</TableCell>
                            <TableCell>
                              {co.attained === null ? (
                                <Badge variant="outline" className="font-normal">
                                  —
                                </Badge>
                              ) : (
                                <Badge
                                  variant={co.attained ? 'secondary' : 'destructive'}
                                  className="font-normal"
                                >
                                  {co.attained ? 'Attained' : 'Not attained'}
                                </Badge>
                              )}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </>
      ) : null}
    </div>
  )
}
