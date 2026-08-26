import * as React from 'react'
import { useQueries, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { useAuth } from '@/features/auth/useAuth'
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

  const { data: courses } = useEntityList<Course>(['curriculum', 'courses'], '/curriculum/courses')
  const { data: versions } = useEntityList<CourseVersion>(
    ['curriculum', 'course-versions', courseId],
    '/curriculum/course-versions',
    { course_id: courseId || undefined },
    { enabled: Boolean(courseId) },
  )
  const [courseVersionId, setCourseVersionId] = useResetOnChange(courseId, '')

  const { data: cos, isLoading: cosLoading } = useEntityList<CourseOutcome>(
    ['curriculum', 'course-outcomes', courseVersionId],
    '/curriculum/course-outcomes',
    { course_version_id: courseVersionId || undefined },
    { enabled: Boolean(courseVersionId) },
  )
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

  const coIds = React.useMemo(() => (cos ?? []).map((c) => c.id), [cos])
  const mappingQueries = useQueries({
    queries: coIds.map((coId) => ({
      queryKey: ['curriculum', 'co-po-mappings', coId],
      queryFn: async () =>
        (
          await apiClient.get<CourseOutcomePOMapping[]>('/curriculum/course-outcome-po-mappings', {
            params: { course_outcome_id: coId },
          })
        ).data,
      enabled: coIds.length > 0,
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
    coIds.forEach((coId) =>
      void queryClient.invalidateQueries({ queryKey: ['curriculum', 'co-po-mappings', coId] }),
    )
  }

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
      <div className="flex flex-wrap gap-2">
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

      {!courseVersionId || !programVersionId ? (
        <p className="text-sm text-muted-foreground">
          Select a course version and a program version to build the CO-PO mapping matrix.
        </p>
      ) : !canEdit ? (
        <p className="text-sm text-muted-foreground">
          You have read access to mappings, but not the mapping.create permission needed to edit
          this matrix.
        </p>
      ) : null}

      {courseVersionId && programVersionId && (
        <MappingMatrix
          rows={(cos ?? []).map((c) => ({ id: c.id, code: c.code, label: c.statement }))}
          cols={(pos ?? []).map((p) => ({ id: p.id, code: p.code, label: p.statement }))}
          rowHeader="Course Outcome"
          colHeader="Program Outcome"
          scale={defaultScale}
          cells={cells}
          isLoading={cosLoading || posLoading || mappingsLoading}
          readOnly={!canEdit}
          onSetCell={handleSet}
          onClearCell={handleClear}
        />
      )}
    </div>
  )
}
