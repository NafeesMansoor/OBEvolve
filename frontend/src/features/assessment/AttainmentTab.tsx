import * as React from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { ChevronDown, ChevronRight, Filter, Save } from 'lucide-react'
import { toast } from 'sonner'

import { useAuth } from '@/features/auth/useAuth'
import { useAcademicTermLookup, useCourseVersionLookup } from '@/features/academic-ops/useLookups'
import type { CourseOffering, CourseSection } from '@/features/academic-ops/types'
import type {
  CourseAttainmentConfig,
  CourseAttainmentReport,
  CourseOutcomeAttainment,
} from '@/features/assessment/types'
import { ImprovementPlansPanel } from '@/features/improvement/ImprovementPlansPanel'
import { ApiError, apiClient } from '@/lib/api-client'
import { useEntityGet, useEntityList } from '@/lib/crud-hooks'
import { useResetOnChange } from '@/lib/use-reset-on-change'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
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
import { cn } from '@/lib/utils'

/** Per-course attainment thresholds + an on-demand calculated report for one
 * section. No stored "run" history — see app.services.attainment's
 * docstring: this is a deliberately smaller MVP than a full accreditation
 * engine, calculated fresh on every view. */
export function AttainmentTab() {
  const { hasPermission } = useAuth()
  const canConfig = hasPermission('attainment.calculate') || hasPermission('assessment.approve')

  const { labelFor } = useCourseVersionLookup()
  const { termById } = useAcademicTermLookup()
  const { data: offerings } = useEntityList<CourseOffering>(
    ['academic', 'course-offerings'],
    '/academic/course-offerings',
  )
  const [offeringId, setOfferingId] = React.useState('')
  const offering = React.useMemo(
    () => (offerings ?? []).find((o) => o.id === offeringId),
    [offerings, offeringId],
  )
  const { data: sections } = useEntityList<CourseSection>(
    ['academic', 'sections', offeringId],
    '/academic/sections',
    { course_offering_id: offeringId || undefined },
    { enabled: Boolean(offeringId) },
  )
  const [sectionId, setSectionId] = useResetOnChange(offeringId, '')

  const { data: config, isLoading: configLoading } = useEntityGet<CourseAttainmentConfig | null>(
    ['marks', 'attainment-config', offering?.course_version_id ?? ''],
    `/marks/attainment-config?course_version_id=${offering?.course_version_id ?? ''}`,
    { enabled: Boolean(offering) },
  )

  const {
    data: report,
    isLoading: reportLoading,
    error: reportError,
  } = useEntityGet<CourseAttainmentReport>(
    ['marks', 'attainment-report', sectionId],
    `/marks/attainment-report?course_section_id=${sectionId}`,
    { enabled: Boolean(sectionId) },
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
      </div>

      {!offering ? (
        <div className="flex flex-col items-center gap-2 rounded-md border border-dashed py-10 text-center text-muted-foreground">
          <Filter className="size-6 opacity-50" />
          <p className="text-sm">Select an offering to configure attainment.</p>
        </div>
      ) : configLoading ? (
        <Skeleton className="h-32 w-full" />
      ) : (
        <ConfigPanel
          key={offering.course_version_id}
          courseVersionId={offering.course_version_id}
          config={config ?? null}
          canConfig={canConfig}
        />
      )}

      {!sectionId ? (
        <div className="flex flex-col items-center gap-2 rounded-md border border-dashed py-10 text-center text-muted-foreground">
          <Filter className="size-6 opacity-50" />
          <p className="text-sm">Select a section to see its attainment report.</p>
        </div>
      ) : reportLoading ? (
        <Skeleton className="h-48 w-full" />
      ) : reportError ? (
        <p className="text-sm text-destructive">
          {reportError instanceof ApiError ? reportError.detail : 'Unable to load attainment report.'}
        </p>
      ) : report ? (
        <div className="flex flex-col gap-2">
          <div>
            <h3 className="font-display text-sm font-semibold">Course outcome attainment</h3>
            <p className="text-sm text-muted-foreground">
              <span className="tabular-nums">{report.eligible_students}</span> eligible student
              {report.eligible_students === 1 ? '' : 's'} of{' '}
              <span className="tabular-nums">{report.total_enrolled}</span> enrolled (
              <span className="tabular-nums">{report.excluded_wi}</span> withdrawn/incomplete excluded) ·
              thresholds: <span className="tabular-nums">{report.min_marks_percent}%</span> marks /{' '}
              <span className="tabular-nums">{report.min_students_percent}%</span> students
            </p>
          </div>
          <CourseOutcomeTable outcomes={report.outcomes} courseSectionId={sectionId} />
        </div>
      ) : null}
    </div>
  )
}

function ConfigPanel({
  courseVersionId,
  config,
  canConfig,
}: {
  courseVersionId: string
  config: CourseAttainmentConfig | null
  canConfig: boolean
}) {
  const queryClient = useQueryClient()
  const [minMarks, setMinMarks] = React.useState(config?.min_marks_percent ?? '60')
  const [minStudents, setMinStudents] = React.useState(config?.min_students_percent ?? '60')
  const [wiTreatment, setWiTreatment] = React.useState(config?.wi_treatment ?? 'exclude')
  const [saving, setSaving] = React.useState(false)

  async function save() {
    setSaving(true)
    try {
      await apiClient.put('/marks/attainment-config', {
        course_version_id: courseVersionId,
        min_marks_percent: minMarks,
        min_students_percent: minStudents,
        wi_treatment: wiTreatment,
      })
      await queryClient.invalidateQueries({
        queryKey: ['marks', 'attainment-config', courseVersionId],
      })
      toast.success('Attainment thresholds saved')
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Unable to save thresholds.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm">Attainment thresholds</CardTitle>
        <CardDescription>
          {config
            ? 'Applied to every section of this course.'
            : 'Using default 60% / 60% / exclude until saved.'}
        </CardDescription>
      </CardHeader>
      <CardContent className="flex flex-wrap items-end gap-3 pt-0">
        <div>
          <label htmlFor="attainment-min-marks" className="text-xs font-medium text-muted-foreground">
            Min marks % (per student, per CO)
          </label>
          <Input
            id="attainment-min-marks"
            type="number"
            step="1"
            min={0}
            max={100}
            value={minMarks}
            onChange={(e) => setMinMarks(e.target.value)}
            disabled={!canConfig}
            className="mt-1 w-28 tabular-nums"
          />
        </div>
        <div>
          <label htmlFor="attainment-min-students" className="text-xs font-medium text-muted-foreground">
            Min students % (per CO)
          </label>
          <Input
            id="attainment-min-students"
            type="number"
            step="1"
            min={0}
            max={100}
            value={minStudents}
            onChange={(e) => setMinStudents(e.target.value)}
            disabled={!canConfig}
            className="mt-1 w-28 tabular-nums"
          />
        </div>
        <div>
          <label htmlFor="attainment-wi-treatment" className="text-xs font-medium text-muted-foreground">
            Withdrawn/Incomplete students
          </label>
          <Select value={wiTreatment} onValueChange={setWiTreatment} disabled={!canConfig}>
            <SelectTrigger id="attainment-wi-treatment" className="mt-1 h-9 w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="exclude">Exclude</SelectItem>
              <SelectItem value="include">Include</SelectItem>
            </SelectContent>
          </Select>
        </div>
        {canConfig && (
          <Button size="sm" onClick={() => void save()} disabled={saving}>
            <Save className="size-4" /> {saving ? 'Saving…' : 'Save thresholds'}
          </Button>
        )}
      </CardContent>
    </Card>
  )
}

function CourseOutcomeTable({
  outcomes,
  courseSectionId,
}: {
  outcomes: CourseOutcomeAttainment[]
  courseSectionId: string
}) {
  const [expanded, setExpanded] = React.useState<Set<string>>(new Set())

  function toggle(id: string) {
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-8" />
            <TableHead>CO</TableHead>
            <TableHead>Statement</TableHead>
            <TableHead>Students attained</TableHead>
            <TableHead>Attainment %</TableHead>
            <TableHead>Result</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {outcomes.map((o) => {
            const isOpen = expanded.has(o.course_outcome_id)
            return (
              <React.Fragment key={o.course_outcome_id}>
                <TableRow
                  className="cursor-pointer"
                  onClick={() => toggle(o.course_outcome_id)}
                  aria-expanded={isOpen}
                >
                  <TableCell className="text-muted-foreground">
                    {isOpen ? <ChevronDown className="size-4" /> : <ChevronRight className="size-4" />}
                  </TableCell>
                  <TableCell className="font-medium whitespace-nowrap">{o.code}</TableCell>
                  <TableCell>{o.statement}</TableCell>
                  <TableCell className="whitespace-nowrap tabular-nums">
                    {o.assessed ? `${o.students_attained} / ${o.eligible_students}` : '—'}
                  </TableCell>
                  <TableCell className="whitespace-nowrap tabular-nums">
                    {o.assessed ? `${Number(o.attainment_percent).toFixed(1)}%` : '—'}
                  </TableCell>
                  <TableCell>
                    {!o.assessed ? (
                      <Badge variant="outline" className="font-normal">
                        Not assessed
                      </Badge>
                    ) : (
                      <Badge variant={o.is_attained ? 'secondary' : 'destructive'} className="font-normal">
                        {o.is_attained ? 'Attained' : 'Not attained'}
                      </Badge>
                    )}
                  </TableCell>
                </TableRow>
                {isOpen && (
                  <TableRow className={cn('hover:bg-transparent', 'bg-muted/20')}>
                    <TableCell colSpan={6} className="py-3">
                      <ImprovementPlansPanel
                        courseSectionId={courseSectionId}
                        courseOutcomeId={o.course_outcome_id}
                      />
                    </TableCell>
                  </TableRow>
                )}
              </React.Fragment>
            )
          })}
        </TableBody>
      </Table>
    </div>
  )
}
