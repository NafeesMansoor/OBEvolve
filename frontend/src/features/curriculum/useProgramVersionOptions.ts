import * as React from 'react'

import type { Program, ProgramVersion } from '@/features/organization/types'
import { useEntityList } from '@/lib/crud-hooks'

/** Shared "Program (version label)" dropdown options, used everywhere a
 * program_version_id needs to be picked (PEOs, program outcomes, course
 * offerings, grading policies, ...). */
export function useProgramVersionOptions() {
  const { data: programs } = useEntityList<Program>(['org', 'programs'], '/org/programs')
  const { data: versions } = useEntityList<ProgramVersion>(
    ['org', 'program-versions'],
    '/org/program-versions',
  )

  const programById = React.useMemo(
    () => new Map((programs ?? []).map((p) => [p.id, p])),
    [programs],
  )

  const options = React.useMemo(
    () =>
      (versions ?? []).map((v) => ({
        label: `${programById.get(v.program_id)?.name ?? 'Unknown program'} — ${v.version_label}`,
        value: v.id,
      })),
    [versions, programById],
  )

  return { options, versions: versions ?? [], programs: programs ?? [], programById }
}
