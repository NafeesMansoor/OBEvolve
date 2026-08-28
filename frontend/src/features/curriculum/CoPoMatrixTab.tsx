import * as React from 'react'
import { useQueries, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { useAuth } from '@/features/auth/useAuth'
import { useCourseVersionLookup } from '@/features/academic-ops/useLookups'
import type {
  Course,
  CourseOutcome,
  CourseOutcomePOMapping,
  CourseVersion,
  MappingScale,
  ProgramOutcome,
} from '@/features/curriculum/types'
import { MappingMatrix, type MatrixCell } from '@/features/curriculum/MappingMatrix'
import { useProgramVersionOptions } from '@/features/curriculum/useProgramVersionOptions'
import { ApiError, apiClient } from '@/lib/api-client'
import { useEntityList } from '@/lib/crud-hooks'
import { useResetOnChange } from '@/lib/use-reset-on-change'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

export function CoPoMatrixTab() {
  const { hasPermission } = useAuth()
  const canEdit = hasPermission('mapping.create')
  const queryClient = useQueryClient()

  const [courseId, setCourseId] = React.useState('')
  const { options: pvOptions } = useProgramVersionOptions()
  const [programVersionId, setProgramVersionId] = React.useState('')
  const { labelFor: courseVersionLabelFor } = useCourseVersionLookup()

  const { data: courses } = useEntityList<Course>(['curriculum', 'courses'], '/curriculum/courses')
  const { data: versions } = useEntityList<CourseVersion>(
    ['curriculum', 'course-versions', courseId],
    '/curriculum/course-versions',
    { course_id: courseId || undefined },
    { enabled: Boolean(courseId) },
  )
  const [courseVersionId, setCourseVersionId] = useResetOnChange(courseId, '')

  // No course picked: the "complete mapping" default view — every CO across
  // every course, read-only. Picking a course narrows to just that course's
  // COs, editable — the two-request-param split below (course_version_id vs.
  // none) matches list_course_outcomes' own filter.
  const { data: allCos, isLoading: allCosLoading } = useEntityList<CourseOutcome>(
    ['curriculum', 'course-outcomes', 'all'],
    '/curriculum/course-outcomes',
    undefined,
    { enabled: !courseVersionId },
  )
  const { data: courseCos, isLoading: courseCosLoading } = useEntityList<CourseOutcome>(
    ['curriculum', 'course-outcomes', courseVersionId],
    '/curriculum/course-outcomes',
    { course_version_id: courseVersionId || undefined },
    { enabled: Boolean(courseVersionId) },
  )
  const cos = courseVersionId ? courseCos : allCos
  const cosLoading = courseVersionId ? courseCosLoading : allCosLoading
  const isCompleteView = !courseVersionId

  const { data: pos, isLoading: posLoading } = useEntityList<ProgramOutcome>(
    ['curriculum', 'program-outcomes', programVersionId],
    '/curriculum/program-outcomes',
    { program_version_id: programVersionId || undefined },
    { enabled: Boolean(programVersionId) },
  )
  const { data: scales } = useEntityList<MappingScale>(
    ['curriculum', 'mapping-scales'],
    '/curriculum/mapping-scales',
  )
  const defaultScale = React.useMemo(
    () => scales?.find((s) => s.is_default) ?? scales?.[0],
    [scales],
  )

  // Complete view: fetch mappings per PO (few) rather than per CO (many —
  // every course's COs) — far fewer requests for the same coverage.
  const poIds = React.useMemo(() => (pos ?? []).map((p) => p.id), [pos])
  const coIds = React.useMemo(() => (cos ?? []).map((c) => c.id), [cos])
  const byCourseQueryKeys = isCompleteView ? poIds : coIds
  const mappingQueries = useQueries({
    queries: byCourseQueryKeys.map((id) => ({
      queryKey: ['curriculum', 'co-po-mappings', isCompleteView ? 'by-po' : 'by-co', id],
      queryFn: async () =>
        (
          await apiClient.get<CourseOutcomePOMapping[]>('/curriculum/course-outcome-po-mappings', {
            params: isCompleteView ? { program_outcome_id: id } : { course_outcome_id: id },
          })
        ).data,
      enabled: byCourseQueryKeys.length > 0,
    })),
  })
  const mappingsLoading = mappingQueries.some((q) => q.isLoading)

  const cells = React.useMemo(() => {
    const map = new Map<string, MatrixCell>()
    mappingQueries.forEach((q) => {
      ;(q.data ?? []).forEach((m) => {
        map.set(`${m.course_outcome_id}:${m.program_outcome_id}`, {
          mappingId: m.id,
          levelId: m.mapping_scale_level_id,
        })
      })
    })
    return map
  }, [mappingQueries])

  function invalidateAll() {
    byCourseQueryKeys.forEach((id) =>
      void queryClient.invalidateQueries({
        queryKey: ['curriculum', 'co-po-mappings', isCompleteView ? 'by-po' : 'by-co', id],
      }),
    )
  }

  const coRows = React.useMemo(
    () =>
      (cos ?? []).map((c) => ({
        id: c.id,
        code: isCompleteView ? `${courseVersionLabelFor(c.course_version_id)} · ${c.code}` : c.code,
        label: c.statement,
      })),
    [cos, isCompleteView, courseVersionLabelFor],
  )

  async function handleSet(rowId: string, colId: string, levelId: string) {
    const existing = cells.get(`${rowId}:${colId}`)
    try {
      if (existing) {
        await apiClient.delete(`/curriculum/course-outcome-po-mappings/${existing.mappingId}`)
      }
      await apiClient.post('/curriculum/course-outcome-po-mappings', {
        course_outcome_id: rowId,
        program_outcome_id: colId,
        mapping_scale_level_id: levelId,
      })
      invalidateAll()
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Unable to set mapping.')
    }
  }

  async function handleClear(_rowId: string, _colId: string, mappingId: string) {
    try {
      await apiClient.delete(`/curriculum/course-outcome-po-mappings/${mappingId}`)
      invalidateAll()
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Unable to clear mapping.')
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap gap-2 rounded-md border bg-muted/30 p-3">
        <div className="w-64">
          <Select value={courseId} onValueChange={setCourseId}>
            <SelectTrigger>
              <SelectValue placeholder="Select a course" />
            </SelectTrigger>
            <SelectContent>
              {(courses ?? []).map((c) => (
                <SelectItem key={c.id} value={c.id}>
                  {c.code} — {c.title}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="w-48">
          <Select value={courseVersionId} onValueChange={setCourseVersionId} disabled={!courseId}>
            <SelectTrigger>
              <SelectValue placeholder="Course version" />
            </SelectTrigger>
            <SelectContent>
              {(versions ?? []).map((v) => (
                <SelectItem key={v.id} value={v.id}>
                  {v.version_label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="w-64">
          <Select value={programVersionId} onValueChange={setProgramVersionId}>
            <SelectTrigger>
              <SelectValue placeholder="Select a program version" />
            </SelectTrigger>
            <SelectContent>
              {pvOptions.map((o) => (
                <SelectItem key={o.value} value={o.value}>
                  {o.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      {!programVersionId ? (
        <p className="text-sm text-muted-foreground">
          Select a program version to see the CO-PO mapping matrix.
        </p>
      ) : isCompleteView ? (
        <p className="rounded-md border border-dashed bg-muted/30 px-3 py-2 text-sm text-muted-foreground">
          Showing every course&apos;s outcomes mapped against this program&apos;s outcomes. Select a
          course above to switch to that course&apos;s editable mapping.
        </p>
      ) : !canEdit ? (
        <p className="rounded-md border border-dashed bg-muted/30 px-3 py-2 text-sm text-muted-foreground">
          You have read access to mappings, but not the mapping.create permission needed to edit
          this matrix.
        </p>
      ) : null}

      {programVersionId && (
        <MappingMatrix
          rows={coRows}
          cols={(pos ?? []).map((p) => ({ id: p.id, code: p.code, label: p.statement }))}
          rowHeader="Course Outcome"
          colHeader="Program Outcome"
          scale={defaultScale}
          cells={cells}
          isLoading={cosLoading || posLoading || mappingsLoading}
          readOnly={!canEdit || isCompleteView}
          onSetCell={handleSet}
          onClearCell={handleClear}
        />
      )}
    </div>
  )
}
