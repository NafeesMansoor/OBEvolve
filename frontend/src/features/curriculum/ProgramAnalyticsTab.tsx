import * as React from 'react'
import { Inbox } from 'lucide-react'

import type { ProgramAnalyticsSummary } from '@/features/assessment/types'
import type { ProgramVersion } from '@/features/organization/types'
import { ApiError } from '@/lib/api-client'
import { useEntityGet, useEntityList } from '@/lib/crud-hooks'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'

const ALL_COHORTS = '__all__'

/** Program-level OBE dashboard (spec §15): PO performance, course-level CO
 * performance (weak/strong courses, COs below threshold), and continuous-
 * improvement counters, filterable by cohort (batch year — see
 * app.services.attainment's docstring for why batch_year stands in for a
 * dedicated Cohort entity). */
export function ProgramAnalyticsTab() {
  const { data: versions } = useEntityList<ProgramVersion>(
    ['org', 'program-versions'],
    '/org/program-versions',
  )
  const [versionId, setVersionId] = React.useState('')
  const activeVersionId = versionId || versions?.[0]?.id || ''

  const [cohort, setCohort] = React.useState(ALL_COHORTS)
  const batchYearParam = cohort === ALL_COHORTS ? '' : `&batch_year=${cohort}`

  const versionOptions = React.useMemo(
    () => (versions ?? []).map((v) => ({ label: `${v.version_label} (${v.status})`, value: v.id })),
    [versions],
  )

  const {
    data: summary,
    isLoading,
    error,
  } = useEntityGet<ProgramAnalyticsSummary>(
    ['marks', 'program-analytics-summary', activeVersionId, cohort],
    `/marks/program-analytics-summary?program_version_id=${activeVersionId}${batchYearParam}`,
    { enabled: Boolean(activeVersionId) },
  )

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap gap-2">
        <div className="w-full max-w-md">
          <Select value={activeVersionId} onValueChange={setVersionId}>
            <SelectTrigger>
              <SelectValue placeholder="Select a curriculum version" />
            </SelectTrigger>
            <SelectContent>
              {versionOptions.map((o) => (
                <SelectItem key={o.value} value={o.value}>
                  {o.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="w-48">
          <Select value={cohort} onValueChange={setCohort}>
            <SelectTrigger>
              <SelectValue placeholder="Cohort" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={ALL_COHORTS}>All cohorts</SelectItem>
              {Array.from({ length: 10 }, (_, i) => new Date().getFullYear() - i).map((year) => (
                <SelectItem key={year} value={String(year)}>
                  Batch {year}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {!activeVersionId ? (
        <p className="text-sm text-muted-foreground">Select a curriculum version to see analytics.</p>
      ) : isLoading ? (
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-20 w-full" />
            <Skeleton className="h-20 w-full" />
          </div>
          <Skeleton className="h-48 w-full" />
          <Skeleton className="h-48 w-full" />
        </div>
      ) : error ? (
        <p className="text-sm text-destructive">
          {error instanceof ApiError ? error.detail : 'Unable to load analytics.'}
        </p>
      ) : summary ? (
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            <StatCard
              label="POs attained"
              value={`${summary.po_outcomes.filter((p) => p.is_attained).length} / ${summary.po_outcomes.length}`}
            />
            <StatCard
              label="Courses with COs below threshold"
              value={String(summary.course_summaries.filter((c) => c.cos_below_threshold > 0).length)}
            />
            <StatCard
              label="Improvement plans"
              value={`${summary.improvement_plan_counts.total} total`}
              detail={`${summary.improvement_plan_counts.proposed} proposed · ${summary.improvement_plan_counts.approved} approved · ${summary.improvement_plan_counts.implemented} implemented · ${summary.improvement_plan_counts.rejected} rejected`}
            />
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">PO performance</CardTitle>
              <CardDescription>Program outcome attainment for this curriculum version.</CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-muted">
                    <tr>
                      <th className="px-4 py-2 text-left font-semibold">PO</th>
                      <th className="px-4 py-2 text-left font-semibold">Statement</th>
                      <th className="px-4 py-2 text-left font-semibold">Attainment %</th>
                      <th className="px-4 py-2 text-left font-semibold">Result</th>
                    </tr>
                  </thead>
                  <tbody>
                    {summary.po_outcomes.map((po) => (
                      <tr key={po.program_outcome_id} className="border-t">
                        <td className="px-4 py-2 font-medium whitespace-nowrap">{po.code}</td>
                        <td className="px-4 py-2">{po.statement}</td>
                        <td className="px-4 py-2 whitespace-nowrap font-medium tabular-nums">
                          {po.assessed ? `${Number(po.attainment_percent).toFixed(1)}%` : '—'}
                        </td>
                        <td className="px-4 py-2">
                          {!po.assessed ? (
                            <Badge variant="outline" className="font-normal">
                              Not assessed
                            </Badge>
                          ) : (
                            <Badge
                              variant={po.is_attained ? 'secondary' : 'destructive'}
                              className="font-normal"
                            >
                              {po.is_attained ? 'Attained' : 'Not attained'}
                            </Badge>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Course performance</CardTitle>
              <CardDescription>
                Ranked weakest-first — average CO attainment across every currently-offered section.
              </CardDescription>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-muted">
                    <tr>
                      <th className="px-4 py-2 text-left font-semibold">Course</th>
                      <th className="px-4 py-2 text-left font-semibold">COs assessed</th>
                      <th className="px-4 py-2 text-left font-semibold">COs below threshold</th>
                      <th className="px-4 py-2 text-left font-semibold">Average CO attainment</th>
                    </tr>
                  </thead>
                  <tbody>
                    {summary.course_summaries.map((c) => (
                      <tr key={c.course_version_id} className="border-t">
                        <td className="px-4 py-2 whitespace-nowrap">
                          <span className="font-medium">{c.course_code}</span>{' '}
                          <span className="text-muted-foreground">{c.course_title}</span>
                        </td>
                        <td className="px-4 py-2 tabular-nums">{c.cos_assessed}</td>
                        <td className="px-4 py-2">
                          {c.cos_below_threshold > 0 ? (
                            <Badge variant="destructive" className="font-normal tabular-nums">
                              {c.cos_below_threshold}
                            </Badge>
                          ) : (
                            <span className="tabular-nums">0</span>
                          )}
                        </td>
                        <td className="px-4 py-2 whitespace-nowrap font-medium tabular-nums">
                          {c.average_co_attainment_percent === null
                            ? '—'
                            : `${Number(c.average_co_attainment_percent).toFixed(1)}%`}
                        </td>
                      </tr>
                    ))}
                    {summary.course_summaries.length === 0 && (
                      <tr>
                        <td colSpan={4} className="px-4 py-10">
                          <div className="flex flex-col items-center gap-2 text-center text-muted-foreground">
                            <Inbox className="size-6 opacity-50" />
                            <span className="text-sm">
                              No assessed courses under this curriculum version yet.
                            </span>
                          </div>
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </div>
      ) : null}
    </div>
  )
}

function StatCard({ label, value, detail }: { label: string; value: string; detail?: string }) {
  return (
    <Card>
      <CardContent className="py-4">
        <p className="text-xs font-medium text-muted-foreground">{label}</p>
        <p className="mt-1 font-display text-2xl font-semibold tracking-tight tabular-nums">{value}</p>
        {detail && <p className="mt-1 text-xs text-muted-foreground">{detail}</p>}
      </CardContent>
    </Card>
  )
}
