import type {
  CourseOffering,
  CourseSection,
  FacultyAssignment,
  StudentEnrollment,
} from '@/features/academic-ops/types'
import { useAuth } from '@/features/auth/useAuth'
import type { Course, CourseVersion } from '@/features/curriculum/types'
import type { AcademicTerm } from '@/features/organization/types'
import { useActiveProgram } from '@/lib/active-program-context'
import { useEntityList } from '@/lib/crud-hooks'
import type { MyCourseCard } from '@/features/course-management/types'

/**
 * Faculty Module spec §2/§30: "Current Courses" and "Previous Courses" are
 * every section a faculty member is *personally* assigned to, split by
 * whether the section's academic term is the active one — never broadened
 * by administrative authority. `/academic/faculty-assignments` without a
 * `faculty_user_id` filter returns every section in the program for a
 * caller who holds program-wide `section.manage` (Program Coordinator etc.
 * — see `app.services.faculty_scope`'s `is_section_authority` bypass,
 * which is correct for admin/oversight endpoints but wrong for "my
 * courses"), so this hook always passes its own id explicitly rather than
 * relying on that server-side scoping.
 */
export function useMyCourses(): {
  current: MyCourseCard[]
  previous: MyCourseCard[]
  isLoading: boolean
} {
  const { user } = useAuth()
  const { activeProgramCode } = useActiveProgram()
  const enabled = Boolean(activeProgramCode) && Boolean(user?.id)

  const { data: assignments, isLoading: l1 } = useEntityList<FacultyAssignment>(
    ['academic', 'faculty-assignments', 'mine', activeProgramCode, user?.id],
    '/academic/faculty-assignments',
    { faculty_user_id: user?.id },
    { enabled },
  )
  const { data: sections, isLoading: l2 } = useEntityList<CourseSection>(
    ['academic', 'sections', 'mine', activeProgramCode],
    '/academic/sections',
    undefined,
    { enabled },
  )
  const { data: offerings, isLoading: l3 } = useEntityList<CourseOffering>(
    ['academic', 'course-offerings', activeProgramCode],
    '/academic/course-offerings',
    undefined,
    { enabled },
  )
  const { data: enrollments, isLoading: l4 } = useEntityList<StudentEnrollment>(
    ['academic', 'enrollments', 'mine', activeProgramCode],
    '/academic/enrollments',
    undefined,
    { enabled },
  )
  const { data: courseVersions, isLoading: l5 } = useEntityList<CourseVersion>(
    ['curriculum', 'course-versions'],
    '/curriculum/course-versions',
    undefined,
    { enabled },
  )
  const { data: courses, isLoading: l6 } = useEntityList<Course>(
    ['curriculum', 'courses'],
    '/curriculum/courses',
    undefined,
    { enabled },
  )
  const { data: terms, isLoading: l7 } = useEntityList<AcademicTerm>(
    ['org', 'academic-terms'],
    '/org/academic-terms',
    undefined,
    { enabled },
  )

  const isLoading = l1 || l2 || l3 || l4 || l5 || l6 || l7

  if (isLoading || !assignments || !sections || !offerings || !courseVersions || !courses || !terms) {
    return { current: [], previous: [], isLoading: true }
  }

  const sectionsById = new Map(sections.map((s) => [s.id, s]))
  const offeringsById = new Map(offerings.map((o) => [o.id, o]))
  const versionsById = new Map(courseVersions.map((v) => [v.id, v]))
  const coursesById = new Map(courses.map((c) => [c.id, c]))
  const termsById = new Map(terms.map((t) => [t.id, t]))
  const enrollCountBySection = new Map<string, number>()
  for (const e of enrollments ?? []) {
    enrollCountBySection.set(
      e.course_section_id,
      (enrollCountBySection.get(e.course_section_id) ?? 0) + 1,
    )
  }

  const cards: MyCourseCard[] = []
  for (const assignment of assignments) {
    const section = sectionsById.get(assignment.course_section_id)
    if (!section) continue
    const offering = offeringsById.get(section.course_offering_id)
    if (!offering) continue
    const version = versionsById.get(offering.course_version_id)
    const course = version ? coursesById.get(version.course_id) : undefined
    const term = termsById.get(offering.academic_term_id)
    cards.push({
      course_section_id: section.id,
      course_offering_id: offering.id,
      course_version_id: offering.course_version_id,
      program_version_id: offering.program_version_id,
      course_code: course?.code ?? 'Unknown',
      course_title: course?.title ?? 'Unknown course',
      section_code: section.section_code,
      credits: course?.credits ?? '—',
      academic_term_id: offering.academic_term_id,
      term_name: term?.name ?? 'Unknown term',
      is_current_term: term?.is_active ?? false,
      enrolled_count: enrollCountBySection.get(section.id) ?? 0,
      role: assignment.role,
    })
  }

  return {
    current: cards.filter((c) => c.is_current_term),
    previous: cards.filter((c) => !c.is_current_term),
    isLoading: false,
  }
}
