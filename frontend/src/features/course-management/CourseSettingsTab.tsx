import * as React from 'react'
import { useQueries } from '@tanstack/react-query'
import { toast } from 'sonner'

import type { ChangeRequestTargetField, CourseChangeRequest } from '@/features/change-requests/types'
import { ChangeRequestRow } from '@/features/change-requests/ChangeRequestRow'
import { BulletList } from '@/features/course-management/BulletList'
import { InlineEditableField } from '@/features/course-management/InlineEditableField'
import { InlineEditableOutcomesTable } from '@/features/course-management/InlineEditableOutcomesTable'
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
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

/** Faculty Module spec §4: Course Settings itself (description, outcomes,
 * TLA mapping, learning materials, weights, grading policy) stays
 * admin-controlled — a faculty member can only view it here and propose a
 * change by double-clicking a field or table cell (Wix-editor-style — see
 * `InlineEditableField`/`InlineEditableOutcomesTable`), not a separate
 * button + modal. Description/objectives are the one exception, edited
 * from the Overview tab instead — single-stage approval, the rest of
 * Course Settings goes through two stages. Mirrors the course outline
 * structure directly (basic info / description+objectives / §1.2 CO
 * mapping / TLA / §1.6 materials / §1.7 weights / §1.8 grading —
 * deliberately excludes §1.5's week-by-week delivery plan). A
 * previous-semester course (BR-01) renders identically except nothing is
 * editable — the backend enforces the same rule independently via
 * `ensure_assigned_to_section`/`ensure_current_term`. */
export function CourseSettingsTab({ course }: { course: MyCourseCard }) {
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
  // Course-Level Settings spec §2/§3: whether "settings" is enabled for
  // this section's course type — drives whether fields below are editable.
  const { data: sectionConfig } = useEntityGet<Record<string, boolean>>(
    ['course-types', 'resolve', course.course_section_id],
    `/course-types/resolve/${course.course_section_id}`,
  )
  const settingsEnabled = sectionConfig?.settings ?? false
  const editable = settingsEnabled && course.is_current_term

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

  async function submitChange(
    targetField: ChangeRequestTargetField,
    proposedValueJson: Record<string, unknown>,
    message: string,
  ) {
    try {
      await create.mutateAsync({
        course_section_id: course.course_section_id,
        section_key: 'settings',
        target_field: targetField,
        proposed_value_json: proposedValueJson,
        reason: message,
      })
      toast.success('Sent for review')
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Unable to submit change')
      throw err
    }
  }

  return (
    <div className="flex flex-col gap-4">
      {!course.is_current_term && (
        <div className="rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-sm text-warning-foreground">
          This is a previous-semester course — everything below is read-only.
        </div>
      )}
      {course.is_current_term && (
        <p className="text-xs text-muted-foreground">
          {settingsEnabled
            ? 'Double-click a field or table cell below to propose a change — it goes to your Section Coordinator, then your Program Coordinator, for approval.'
            : 'Course Settings changes are not enabled for this course type.'}
        </p>
      )}

      <Accordion type="multiple" defaultValue={['description', 'outcomes']} className="w-full">
        <AccordionItem value="description">
          <AccordionTrigger>Course description &amp; objectives</AccordionTrigger>
          <AccordionContent className="flex flex-col gap-3">
            <p className="text-xs text-muted-foreground">
              Edited from the Overview tab, not here — description/objectives go through a
              single-stage approval, the rest of Course Settings through two stages.
            </p>
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
            <InlineEditableOutcomesTable
              outcomes={courseOutcomes}
              editable={editable}
              onSave={(newOutcomes, message) =>
                submitChange('outcomes', { outcomes: newOutcomes }, message)
              }
            />
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
            <InlineEditableField
              value={courseVersion?.tla_items}
              editable={editable}
              renderDisplay={(v) => <BulletList text={v} empty="No TLA list on file." />}
              onSave={(newValue, message) =>
                submitChange('tla_mapping', { value: newValue }, message)
              }
            />
          </AccordionContent>
        </AccordionItem>

        <AccordionItem value="materials">
          <AccordionTrigger>Learning materials</AccordionTrigger>
          <AccordionContent>
            <InlineEditableField
              value={courseVersion?.learning_materials}
              editable={editable}
              renderDisplay={(v) => <BulletList text={v} empty="No materials on file." />}
              onSave={(newValue, message) =>
                submitChange('learning_materials', { value: newValue }, message)
              }
            />
          </AccordionContent>
        </AccordionItem>

        <AccordionItem value="weights">
          <AccordionTrigger>Assessment &amp; weights</AccordionTrigger>
          <AccordionContent className="flex flex-col gap-4">
            <div>
              <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                Target distribution
              </p>
              <InlineEditableField
                value={courseVersion?.target_assessment_weights}
                editable={editable}
                renderDisplay={(v) => (
                  <BulletList text={v} empty="No target weight distribution on file." />
                )}
                onSave={(newValue, message) =>
                  submitChange('weights', { value: newValue }, message)
                }
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
          <AccordionContent className="flex flex-col gap-3">
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
            <InlineEditableField
              value={null}
              editable={editable}
              emptyPlaceholder="Double-click to propose a different grading policy."
              onSave={(newValue, message) =>
                submitChange('grading_policy', { value: newValue }, message)
              }
            />
            {editable && (
              <p className="text-xs text-muted-foreground">
                Grading policy is shared across courses, so an approved change here is applied
                manually by an admin rather than automatically.
              </p>
            )}
          </AccordionContent>
        </AccordionItem>
      </Accordion>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Change requests</CardTitle>
          <CardDescription>History of proposed changes for this section.</CardDescription>
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
                  <TableHead>Current</TableHead>
                  <TableHead>Proposed</TableHead>
                  <TableHead>Edited</TableHead>
                  <TableHead>Reason</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Submitted</TableHead>
                  <TableHead className="text-right">Review</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {requests.map((r) => (
                  <ChangeRequestRow key={r.id} request={r} />
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
