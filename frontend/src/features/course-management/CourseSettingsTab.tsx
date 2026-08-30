import * as React from 'react'
import { useQueries } from '@tanstack/react-query'
import { z } from 'zod'

import { useAuth } from '@/features/auth/useAuth'
import {
  TARGET_FIELD_LABELS,
  type ChangeRequestTargetField,
  type CourseChangeRequest,
} from '@/features/change-requests/types'
import type { MyCourseCard } from '@/features/course-management/types'
import type {
  Course,
  CourseOutcome,
  CourseOutcomePOMapping,
  CourseVersion,
  MappingScale,
  ProgramOutcome,
} from '@/features/curriculum/types'
import type { GradingBand, GradingPolicy } from '@/features/grading/types'
import type { Assessment, AssessmentType } from '@/features/assessment/types'
import { ApiError, apiClient } from '@/lib/api-client'
import { useEntityCreate, useEntityGet, useEntityList } from '@/lib/crud-hooks'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { EntityFormDialog, type EntityField } from '@/components/entity-form-dialog'
import { Skeleton } from '@/components/ui/skeleton'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { toast } from 'sonner'

const TARGET_FIELD_OPTIONS = Object.entries(TARGET_FIELD_LABELS).map(([value, label]) => ({
  value,
  label,
}))

const schema = z.object({
  target_field: z.string().min(1, 'Select what you want changed'),
  proposed_value: z.string().min(1, 'Describe the proposed value'),
  reason: z.string().min(1, 'A reason is required'),
})

const fields: EntityField[] = [
  { name: 'target_field', label: 'What needs to change', type: 'select', options: TARGET_FIELD_OPTIONS },
  {
    name: 'proposed_value',
    label: 'Proposed value',
    type: 'textarea',
    placeholder: 'Describe the change you want made',
  },
  { name: 'reason', label: 'Reason', type: 'textarea', placeholder: 'Why is this change needed?' },
]

const STATUS_STYLE: Record<string, string> = {
  pending: 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300',
  approved: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300',
  rejected: 'bg-destructive/10 text-destructive',
}

function BulletList({ text, empty }: { text: string | null | undefined; empty: string }) {
  const lines = (text ?? '').split('\n').map((l) => l.trim()).filter(Boolean)
  if (lines.length === 0) return <p className="text-sm text-muted-foreground">{empty}</p>
  return (
    <ul className="list-disc space-y-1 pl-5 text-sm">
      {lines.map((line, i) => (
        <li key={i}>{line}</li>
      ))}
    </ul>
  )
}

/** Faculty Module spec §4: Course Settings itself (description, outcomes,
 * TLA mapping, learning materials, weights, grading policy) stays
 * admin-controlled — a faculty member can only view it here and propose a
 * change (the one exception, office/consultation/meeting-link, lives on the
 * Overview tab instead). Mirrors the course outline structure directly
 * (basic info / description+objectives / §1.2 CO mapping / TLA / §1.6
 * materials / §1.7 weights / §1.8 grading — deliberately excludes §1.5's
 * week-by-week delivery plan). A previous-semester course (BR-01) renders
 * identically except the "Request modification" action is hidden — the
 * backend enforces the same rule independently via
 * `ensure_assigned_to_section`/`ensure_current_term`. */
export function CourseSettingsTab({ course }: { course: MyCourseCard }) {
  const { hasPermission } = useAuth()
  const [open, setOpen] = React.useState(false)

  const { data: courseVersion } = useEntityGet<CourseVersion>(
    ['curriculum', 'course-version', course.course_version_id],
    `/curriculum/course-versions/${course.course_version_id}`,
  )
  const { data: courseDetail } = useEntityGet<Course>(
    ['curriculum', 'course', courseVersion?.course_id ?? ''],
    `/curriculum/courses/${courseVersion?.course_id}`,
    { enabled: Boolean(courseVersion?.course_id) },
  )
  const { data: courseOutcomes } = useEntityList<CourseOutcome>(
    ['curriculum', 'course-outcomes', course.course_version_id],
    '/curriculum/course-outcomes',
    { course_version_id: course.course_version_id },
  )
  const { data: programOutcomes } = useEntityList<ProgramOutcome>(
    ['curriculum', 'program-outcomes', course.program_version_id ?? ''],
    '/curriculum/program-outcomes',
    { program_version_id: course.program_version_id ?? undefined },
    { enabled: Boolean(course.program_version_id) },
  )
  const { data: mappingScales } = useEntityList<MappingScale>(
    ['curriculum', 'mapping-scales'],
    '/curriculum/mapping-scales',
  )

  const coPoQueries = useQueries({
    queries: (courseOutcomes ?? []).map((co) => ({
      queryKey: ['curriculum', 'course-outcome-po-mappings', co.id],
      queryFn: async () => {
        const res = await apiClient.get<CourseOutcomePOMapping[]>(
          '/curriculum/course-outcome-po-mappings',
          { params: { course_outcome_id: co.id } },
        )
        return res.data
      },
      enabled: Boolean(courseOutcomes),
    })),
  })
  const coPoMappings = coPoQueries.flatMap((q) => q.data ?? [])
  const hasCoPoMapping = coPoMappings.length > 0

  const { data: assessments } = useEntityList<Assessment>(
    ['assessment', 'assessments', course.course_section_id],
    '/assessment/assessments',
    { course_section_id: course.course_section_id },
  )
  const { data: assessmentTypes } = useEntityList<AssessmentType>(
    ['assessment', 'types'],
    '/assessment/types',
  )
  const typeById = React.useMemo(
    () => new Map((assessmentTypes ?? []).map((t) => [t.id, t.name])),
    [assessmentTypes],
  )

  const { data: gradingPolicies } = useEntityList<GradingPolicy>(
    ['grading', 'policies', course.program_version_id ?? ''],
    '/grading/policies',
    { program_version_id: course.program_version_id ?? undefined },
  )
  const { data: defaultGradingPolicies } = useEntityList<GradingPolicy>(
    ['grading', 'policies', 'default'],
    '/grading/policies',
    undefined,
    { enabled: (gradingPolicies ?? []).length === 0 },
  )
  const resolvedPolicy =
    gradingPolicies?.[0] ?? defaultGradingPolicies?.find((p) => p.is_default) ?? null
  const { data: gradingBands } = useEntityList<GradingBand>(
    ['grading', 'bands', resolvedPolicy?.id ?? ''],
    '/grading/bands',
    { grading_policy_id: resolvedPolicy?.id },
    { enabled: Boolean(resolvedPolicy?.id) },
  )

  const { data: requests, isLoading: requestsLoading } = useEntityList<CourseChangeRequest>(
    ['course-change-requests', course.course_section_id],
    '/course-change-requests',
    { course_section_id: course.course_section_id },
  )
  const create = useEntityCreate<Record<string, unknown>>('/course-change-requests', [
    ['course-change-requests', course.course_section_id],
  ])
  const canReview = hasPermission('course_change_request.review')

  const poById = React.useMemo(
    () => new Map((programOutcomes ?? []).map((p) => [p.id, p])),
    [programOutcomes],
  )
  const coById = React.useMemo(
    () => new Map((courseOutcomes ?? []).map((c) => [c.id, c])),
    [courseOutcomes],
  )
  const levelById = React.useMemo(() => {
    const map = new Map<string, { value: number; label: string }>()
    for (const scale of mappingScales ?? []) {
      for (const level of scale.levels) {
        map.set(level.id, { value: level.value, label: level.label })
      }
    }
    return map
  }, [mappingScales])

  return (
    <div className="flex flex-col gap-4">
      {!course.is_current_term && (
        <div className="rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-sm text-warning-foreground">
          This is a previous-semester course — everything below is read-only.
        </div>
      )}

      <Accordion type="multiple" defaultValue={['description', 'outcomes']} className="w-full">
        <AccordionItem value="description">
          <AccordionTrigger>Course description &amp; objectives</AccordionTrigger>
          <AccordionContent className="flex flex-col gap-3">
            <p className="text-sm">{courseDetail?.description ?? 'No description on file.'}</p>
            <div>
              <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Objectives
              </p>
              <BulletList text={courseVersion?.objectives} empty="No objectives on file." />
            </div>
          </AccordionContent>
        </AccordionItem>

        <AccordionItem value="outcomes">
          <AccordionTrigger>Course outcomes</AccordionTrigger>
          <AccordionContent>
            {!courseOutcomes ? (
              <Skeleton className="h-24 w-full" />
            ) : courseOutcomes.length === 0 ? (
              <p className="text-sm text-muted-foreground">No course outcomes defined yet.</p>
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-16">Code</TableHead>
                    <TableHead>Statement</TableHead>
                    <TableHead>Delivery methods</TableHead>
                    <TableHead>Assessment tools</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {courseOutcomes.map((co) => (
                    <TableRow key={co.id}>
                      <TableCell className="font-medium">{co.code}</TableCell>
                      <TableCell>{co.statement}</TableCell>
                      <TableCell className="text-muted-foreground">
                        {co.delivery_methods ?? '—'}
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {co.assessment_tools ?? '—'}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </AccordionContent>
        </AccordionItem>

        {hasCoPoMapping && (
          <AccordionItem value="co-po">
            <AccordionTrigger>CO–PO mapping</AccordionTrigger>
            <AccordionContent>
              <p className="mb-3 text-xs text-muted-foreground">
                Set at the program level — showing only the mappings for this course&apos;s own
                outcomes.
              </p>
              <div className="flex flex-col gap-2">
                {(courseOutcomes ?? []).map((co) => {
                  const mine = coPoMappings.filter((m) => m.course_outcome_id === co.id)
                  if (mine.length === 0) return null
                  return (
                    <div key={co.id} className="rounded-md border p-3">
                      <p className="mb-1.5 text-sm font-medium">
                        {co.code} — {coById.get(co.id)?.statement}
                      </p>
                      <div className="flex flex-wrap gap-1.5">
                        {mine.map((m) => {
                          const po = poById.get(m.program_outcome_id)
                          const level = levelById.get(m.mapping_scale_level_id)
                          return (
                            <Badge key={m.id} variant="outline" className="font-normal">
                              {po?.code ?? m.program_outcome_id}
                              {level ? ` · ${level.label} (${level.value})` : ''}
                            </Badge>
                          )
                        })}
                      </div>
                    </div>
                  )
                })}
              </div>
            </AccordionContent>
          </AccordionItem>
        )}

        <AccordionItem value="tla">
          <AccordionTrigger>Teaching &amp; learning activities</AccordionTrigger>
          <AccordionContent>
            <BulletList text={courseVersion?.tla_items} empty="No TLA list on file." />
          </AccordionContent>
        </AccordionItem>

        <AccordionItem value="materials">
          <AccordionTrigger>Learning materials</AccordionTrigger>
          <AccordionContent>
            <BulletList text={courseVersion?.learning_materials} empty="No materials on file." />
          </AccordionContent>
        </AccordionItem>

        <AccordionItem value="weights">
          <AccordionTrigger>Assessment &amp; weights</AccordionTrigger>
          <AccordionContent className="flex flex-col gap-4">
            <div>
              <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Target distribution
              </p>
              <BulletList
                text={courseVersion?.target_assessment_weights}
                empty="No target weight distribution on file."
              />
            </div>
            <div>
              <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                This section&apos;s recorded assessments
              </p>
              {!assessments || assessments.length === 0 ? (
                <p className="text-sm text-muted-foreground">No assessments recorded yet.</p>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Title</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Weight</TableHead>
                      <TableHead>Total marks</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {assessments.map((a) => (
                      <TableRow key={a.id}>
                        <TableCell>{a.title}</TableCell>
                        <TableCell className="text-muted-foreground">
                          {typeById.get(a.assessment_type_id) ?? '—'}
                        </TableCell>
                        <TableCell>{a.weight ? `${a.weight}%` : '—'}</TableCell>
                        <TableCell>{a.max_marks}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </div>
          </AccordionContent>
        </AccordionItem>

        <AccordionItem value="grading">
          <AccordionTrigger>Grading policy</AccordionTrigger>
          <AccordionContent>
            {!resolvedPolicy ? (
              <p className="text-sm text-muted-foreground">No grading policy configured.</p>
            ) : !gradingBands || gradingBands.length === 0 ? (
              <Skeleton className="h-24 w-full" />
            ) : (
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Letter grade</TableHead>
                    <TableHead>Range</TableHead>
                    <TableHead>Grade point</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {[...gradingBands]
                    .sort((a, b) => a.sequence - b.sequence)
                    .map((band) => (
                      <TableRow key={band.id}>
                        <TableCell className="font-medium">{band.letter_grade}</TableCell>
                        <TableCell className="text-muted-foreground">
                          {band.min_percentage}–{band.max_percentage}%
                        </TableCell>
                        <TableCell>{band.grade_point ?? '—'}</TableCell>
                      </TableRow>
                    ))}
                </TableBody>
              </Table>
            )}
          </AccordionContent>
        </AccordionItem>
      </Accordion>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between gap-2">
          <div>
            <CardTitle className="text-base">Change requests</CardTitle>
            <CardDescription>
              Submitted requests forward to your Course Coordinator for review.
            </CardDescription>
          </div>
          {course.is_current_term && <Button onClick={() => setOpen(true)}>Request modification</Button>}
        </CardHeader>
        <CardContent>
          {requestsLoading ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : !requests || requests.length === 0 ? (
            <p className="text-sm text-muted-foreground">No change requests submitted yet.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Field</TableHead>
                  <TableHead>Reason</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Submitted</TableHead>
                  {canReview && <TableHead className="text-right">Review</TableHead>}
                </TableRow>
              </TableHeader>
              <TableBody>
                {requests.map((r) => (
                  <ChangeRequestRow key={r.id} request={r} canReview={canReview} />
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <EntityFormDialog
        open={open}
        onOpenChange={setOpen}
        title="Request a course settings modification"
        description="Your Course Coordinator will review this before any change is applied."
        fields={fields}
        schema={schema}
        defaultValues={{ target_field: '', proposed_value: '', reason: '' }}
        onSubmit={async (values) => {
          await create.mutateAsync({
            course_section_id: course.course_section_id,
            target_field: values.target_field as ChangeRequestTargetField,
            proposed_value_json: { value: values.proposed_value },
            reason: values.reason,
          })
        }}
        submitLabel="Submit request"
      />
    </div>
  )
}

function ChangeRequestRow({
  request,
  canReview,
}: {
  request: CourseChangeRequest
  canReview: boolean
}) {
  const [isReviewing, setIsReviewing] = React.useState(false)

  async function review(reviewStatus: 'approved' | 'rejected') {
    setIsReviewing(true)
    try {
      await apiClient.post(`/course-change-requests/${request.id}/review`, {
        status: reviewStatus,
      })
      toast.success(`Request ${reviewStatus}`)
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Review failed')
    } finally {
      setIsReviewing(false)
    }
  }

  return (
    <TableRow>
      <TableCell>{TARGET_FIELD_LABELS[request.target_field]}</TableCell>
      <TableCell className="max-w-xs truncate">{request.reason}</TableCell>
      <TableCell>
        <Badge className={STATUS_STYLE[request.status]} variant="outline">
          {request.status}
        </Badge>
      </TableCell>
      <TableCell className="text-muted-foreground">
        {new Date(request.created_at).toLocaleDateString()}
      </TableCell>
      {canReview && (
        <TableCell className="text-right">
          {request.status === 'pending' && (
            <div className="flex justify-end gap-2">
              <Button
                size="sm"
                variant="outline"
                disabled={isReviewing}
                onClick={() => void review('approved')}
              >
                Approve
              </Button>
              <Button
                size="sm"
                variant="outline"
                disabled={isReviewing}
                onClick={() => void review('rejected')}
              >
                Reject
              </Button>
            </div>
          )}
        </TableCell>
      )}
    </TableRow>
  )
}
