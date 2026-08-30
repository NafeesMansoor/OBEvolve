import * as React from 'react'
import { useQueries } from '@tanstack/react-query'

import { useMyCourses } from '@/features/course-management/useMyCourses'
import type { GradeSheetReport } from '@/features/course-management/types'
import type { CourseAttainmentReport, ProgramAttainmentReport } from '@/features/assessment/types'
import { apiClient } from '@/lib/api-client'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'

const GRADE_ORDER = ['A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'D', 'F', 'I', 'W', 'AW']

function gradeColor(grade: string): string {
  if (grade.startsWith('A')) return 'hsl(var(--success))'
  if (grade.startsWith('B') || grade.startsWith('C')) return 'hsl(var(--primary))'
  if (grade === 'D') return 'hsl(var(--warning))'
  return 'hsl(var(--destructive))'
}

function HorizontalBars({
  rows,
  emptyMessage,
}: {
  rows: { label: string; sublabel?: string; percent: number | null; achieved: boolean | null }[]
  emptyMessage: string
}) {
  if (rows.length === 0) {
    return <p className="text-sm text-muted-foreground">{emptyMessage}</p>
  }
  return (
    <div className="flex flex-col gap-2.5">
      {rows.map((row, i) => (
        <div key={i} className="flex items-center gap-3">
          <div className="w-16 shrink-0 text-xs font-medium">{row.label}</div>
          <div className="h-3 flex-1 overflow-hidden rounded-full bg-muted">
            <div
              className="h-full rounded-full transition-all"
              style={{
                width: `${Math.min(100, Math.max(0, row.percent ?? 0))}%`,
                backgroundColor:
                  row.achieved === null
                    ? 'hsl(var(--muted-foreground))'
                    : row.achieved
                      ? 'hsl(var(--success))'
                      : 'hsl(var(--destructive))',
              }}
            />
          </div>
          <div className="w-24 shrink-0 text-right text-xs tabular-nums text-muted-foreground">
            {row.percent === null ? 'Not assessed' : `${row.percent}%`}
          </div>
        </div>
      ))}
    </div>
  )
}

function GradeBarChart({ counts }: { counts: Record<string, number> }) {
  const max = Math.max(1, ...Object.values(counts))
  const grades = GRADE_ORDER.filter((g) => counts[g] > 0)
  if (grades.length === 0) {
    return <p className="text-sm text-muted-foreground">No submitted grades yet.</p>
  }
  return (
    <div className="flex h-40 items-end gap-3">
      {grades.map((g) => (
        <div key={g} className="flex flex-1 flex-col items-center gap-1">
          <span className="text-xs font-medium tabular-nums">{counts[g]}</span>
          <div
            className="w-full rounded-t-sm transition-all"
            style={{
              height: `${(counts[g] / max) * 100}%`,
              minHeight: 4,
              backgroundColor: gradeColor(g),
            }}
          />
          <span className="text-xs text-muted-foreground">{g}</span>
        </div>
      ))}
    </div>
  )
}

/** Faculty Module — a single cross-course analytics view ("in one place he
 * can see the analysis of all his courses in terms of attainments, grades,
 * and other filterable stuff"), distinct from the per-section Analytics tab
 * inside Course Management (spec §25-27, which stays as-is). Reuses the
 * exact same backend reports (`/marks/grade-sheet`, `/marks/
 * attainment-report`, `/marks/program-attainment-report`) that those
 * per-section/program pages already call — Faculty already holds
 * `assessment.view`, which every one of those endpoints accepts. */
export function FacultyAnalyticsPanel() {
  const { current, previous, isLoading: coursesLoading } = useMyCourses()
  const allCourses = React.useMemo(() => [...current, ...previous], [current, previous])

  const terms = React.useMemo(
    () => Array.from(new Set(allCourses.map((c) => c.term_name))),
    [allCourses],
  )
  const [termFilter, setTermFilter] = React.useState('all')
  const [courseFilter, setCourseFilter] = React.useState('all')

  const filtered = React.useMemo(
    () =>
      allCourses.filter(
        (c) =>
          (termFilter === 'all' || c.term_name === termFilter) &&
          (courseFilter === 'all' || c.course_code === courseFilter),
      ),
    [allCourses, termFilter, courseFilter],
  )

  const gradeSheetQueries = useQueries({
    queries: filtered.map((c) => ({
      queryKey: ['marks', 'grade-sheet', c.course_section_id],
      queryFn: async () => {
        const res = await apiClient.get<GradeSheetReport>('/marks/grade-sheet', {
          params: { course_section_id: c.course_section_id },
        })
        return res.data
      },
    })),
  })
  const attainmentQueries = useQueries({
    queries: filtered.map((c) => ({
      queryKey: ['marks', 'attainment-report', c.course_section_id],
      queryFn: async () => {
        const res = await apiClient.get<CourseAttainmentReport>('/marks/attainment-report', {
          params: { course_section_id: c.course_section_id },
        })
        return res.data
      },
    })),
  })

  const programVersionIds = React.useMemo(
    () => Array.from(new Set(filtered.map((c) => c.program_version_id).filter(Boolean))) as string[],
    [filtered],
  )
  const poQueries = useQueries({
    queries: programVersionIds.map((pid) => ({
      queryKey: ['marks', 'program-attainment-report', pid],
      queryFn: async () => {
        const res = await apiClient.get<ProgramAttainmentReport>('/marks/program-attainment-report', {
          params: { program_version_id: pid },
        })
        return res.data
      },
    })),
  })

  const isLoading =
    coursesLoading ||
    gradeSheetQueries.some((q) => q.isLoading) ||
    attainmentQueries.some((q) => q.isLoading)

  const gradeCounts = React.useMemo(() => {
    const counts: Record<string, number> = {}
    for (const q of gradeSheetQueries) {
      for (const row of q.data?.rows ?? []) {
        if (!row.letter_grade) continue
        counts[row.letter_grade] = (counts[row.letter_grade] ?? 0) + 1
      }
    }
    return counts
  }, [gradeSheetQueries])

  const totalStudents = Object.values(gradeCounts).reduce((a, b) => a + b, 0)
  const passCount = Object.entries(gradeCounts)
    .filter(([g]) => g !== 'F' && g !== 'I' && g !== 'W' && g !== 'AW')
    .reduce((a, [, n]) => a + n, 0)
  const passRate = totalStudents > 0 ? Math.round((passCount / totalStudents) * 100) : null

  const coRows = React.useMemo(() => {
    const rows: { label: string; percent: number | null; achieved: boolean | null }[] = []
    attainmentQueries.forEach((q, i) => {
      const courseCode = filtered[i]?.course_code ?? ''
      for (const o of q.data?.outcomes ?? []) {
        if (!o.assessed) continue
        rows.push({
          label: `${courseCode} ${o.code}`,
          percent: o.attainment_percent ? Number(o.attainment_percent) : null,
          achieved: o.is_attained,
        })
      }
    })
    return rows
  }, [attainmentQueries, filtered])

  const myOwnCourseCodes = React.useMemo(() => new Set(allCourses.map((c) => c.course_code)), [allCourses])
  const poRows = React.useMemo(() => {
    const rows: { label: string; percent: number | null; achieved: boolean | null }[] = []
    const seen = new Set<string>()
    for (const q of poQueries) {
      for (const o of q.data?.outcomes ?? []) {
        const contributesFromMyCourses = o.contributions.some((c) => myOwnCourseCodes.has(c.course_code))
        if (!o.assessed || !contributesFromMyCourses || seen.has(o.code)) continue
        seen.add(o.code)
        rows.push({
          label: o.code,
          percent: o.attainment_percent ? Number(o.attainment_percent) : null,
          achieved: o.is_attained,
        })
      }
    }
    return rows.sort((a, b) => a.label.localeCompare(b.label))
  }, [poQueries, myOwnCourseCodes])

  if (coursesLoading) return <Skeleton className="h-96 w-full" />

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-2">
        <Select value={termFilter} onValueChange={setTermFilter}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="All terms" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All terms</SelectItem>
            {terms.map((t) => (
              <SelectItem key={t} value={t}>
                {t}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={courseFilter} onValueChange={setCourseFilter}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="All courses" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All courses</SelectItem>
            {Array.from(new Set(allCourses.map((c) => c.course_code))).map((code) => (
              <SelectItem key={code} value={code}>
                {code}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Badge variant="outline" className="font-normal">
          {filtered.length} section{filtered.length === 1 ? '' : 's'}
        </Badge>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card>
          <CardContent className="pt-6">
            <p className="text-2xl font-bold tabular-nums">{filtered.length}</p>
            <p className="text-xs text-muted-foreground">Sections in view</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-2xl font-bold tabular-nums">{totalStudents}</p>
            <p className="text-xs text-muted-foreground">Students graded</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <p className="text-2xl font-bold tabular-nums">{passRate === null ? '—' : `${passRate}%`}</p>
            <p className="text-xs text-muted-foreground">Pass rate</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Grade distribution</CardTitle>
          <CardDescription>Across every submitted section in the current filter.</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? <Skeleton className="h-40 w-full" /> : <GradeBarChart counts={gradeCounts} />}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Course Outcome attainment</CardTitle>
          <CardDescription>One bar per assessed CO, across the filtered sections.</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-40 w-full" />
          ) : (
            <HorizontalBars rows={coRows} emptyMessage="No CO attainment calculated yet." />
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Program Outcome attainment</CardTitle>
          <CardDescription>
            Program-level POs that your own courses&apos; COs contribute to.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <Skeleton className="h-40 w-full" />
          ) : (
            <HorizontalBars rows={poRows} emptyMessage="No PO attainment reachable from your courses yet." />
          )}
        </CardContent>
      </Card>
    </div>
  )
}
