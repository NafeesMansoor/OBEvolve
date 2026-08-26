import * as React from 'react'

import type { Course, CourseVersion } from '@/features/curriculum/types'
import type { AcademicTerm } from '@/features/organization/types'
import { useEntityList } from '@/lib/crud-hooks'

/** Shared lookups for the Academic Operations module — course versions
 * (labeled with their course code) and academic terms — used across
 * offerings/sections/questions/assessments wherever those ids need a
 * human-readable label or a select dropdown. */
export function useCourseVersionLookup() {
  const { data: courses } = useEntityList<Course>(['curriculum', 'courses'], '/curriculum/courses')
  const { data: versions } = useEntityList<CourseVersion>(
    ['curriculum', 'course-versions', 'all'],
    '/curriculum/course-versions',
  )

  const courseById = React.useMemo(() => new Map((courses ?? []).map((c) => [c.id, c])), [courses])
  const versionById = React.useMemo(
    () => new Map((versions ?? []).map((v) => [v.id, v])),
    [versions],
  )

  const options = React.useMemo(
    () =>
      (versions ?? []).map((v) => {
        const course = courseById.get(v.course_id)
        return {
          label: `${course?.code ?? '?'} ${v.version_label}${course ? ` — ${course.title}` : ''}`,
          value: v.id,
        }
      }),
    [versions, courseById],
  )

  function labelFor(courseVersionId: string): string {
    const v = versionById.get(courseVersionId)
    if (!v) return courseVersionId
    const course = courseById.get(v.course_id)
    return `${course?.code ?? '?'} ${v.version_label}`
  }

  return { options, courseById, versionById, labelFor, versions: versions ?? [], courses: courses ?? [] }
}

export function useAcademicTermLookup() {
  const { data: terms } = useEntityList<AcademicTerm>(
    ['org', 'academic-terms'],
    '/org/academic-terms',
  )
  const termById = React.useMemo(() => new Map((terms ?? []).map((t) => [t.id, t])), [terms])
  const options = React.useMemo(
    () => (terms ?? []).map((t) => ({ label: t.name, value: t.id })),
    [terms],
  )
  return { options, termById, terms: terms ?? [] }
}
