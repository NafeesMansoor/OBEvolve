import { useQueries } from '@tanstack/react-query'
import { AlertTriangle, ArrowRight, BookOpen, GraduationCap, History, Users } from 'lucide-react'
import { Link } from 'react-router-dom'

import { useMyCourses } from '@/features/course-management/useMyCourses'
import type { GradeSheetReport, MyCourseCard } from '@/features/course-management/types'
import { useActiveProgram } from '@/lib/active-program-context'
import { apiClient } from '@/lib/api-client'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'

function isIncomplete(sheet: GradeSheetReport | undefined): boolean {
  if (!sheet || sheet.submission_status === 'submitted') return false
  return !(sheet.weight_complete && sheet.marks_complete)
}

/** One batched fetch (react-query's `useQueries`, not one hook per section —
 * Rules of Hooks forbid calling a hook inside `.map()`) for every current
 * section's grade-sheet status, shared by the Action Required list and each
 * course card's badge so this data is fetched exactly once. */
function useGradeStatusBySection(sectionIds: string[]) {
  const { activeProgramCode } = useActiveProgram()
  const results = useQueries({
    queries: sectionIds.map((id) => ({
      queryKey: ['marks', 'grade-sheet', id],
      queryFn: async () =>
        (await apiClient.get<GradeSheetReport>('/marks/grade-sheet', {
          params: { course_section_id: id },
        })).data,
      enabled: Boolean(activeProgramCode),
    })),
  })
  const byId = new Map<string, GradeSheetReport | undefined>()
  sectionIds.forEach((id, i) => byId.set(id, results[i]?.data))
  return byId
}

/** Faculty Module spec §2/§30: Overview first (a summarized view), then
 * Current Courses, Students (via each course card's count), Previous
 * Courses, and Action Required — for anyone who teaches at least one
 * section. Renders nothing for a caller with zero FacultyAssignment rows
 * (Program Admin/Coordinator browsing without teaching duties).
 *
 * Action Required deliberately does *not* repeat each affected course as
 * its own full card under a separate heading (the original shape) — with
 * more than one or two incomplete sections that read as a wall of
 * duplicate-looking cards. It's a compact row list here, and the same
 * signal shows as a small badge directly on the course's own card in
 * Current Courses — one place to look, not two — both fed by the same
 * single batched fetch above. */
export function FacultyCoursesPanel() {
  const { current, previous, isLoading } = useMyCourses()
  const gradeStatusBySection = useGradeStatusBySection(current.map((c) => c.course_section_id))

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <Skeleton className="h-32" />
        <Skeleton className="h-32" />
      </div>
    )
  }

  if (current.length === 0 && previous.length === 0) return null

  const totalStudents = current.reduce((sum, c) => sum + c.enrolled_count, 0)
  const needsAttention = current.filter((c) =>
    isIncomplete(gradeStatusBySection.get(c.course_section_id)),
  )

  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <OverviewStat icon={BookOpen} label="Current courses" value={current.length} />
        <OverviewStat icon={Users} label="Students taught" value={totalStudents} />
        <OverviewStat icon={History} label="Previous courses" value={previous.length} />
        <OverviewStat
          icon={GraduationCap}
          label="Coordinator role"
          value={current.filter((c) => c.role === 'coordinator').length}
        />
      </div>

      {needsAttention.length > 0 && (
        <div className="flex flex-col gap-2">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
            Action Required
          </h2>
          <Card className="divide-y p-0">
            {needsAttention.map((s) => (
              <ActionRow
                key={s.course_section_id}
                section={s}
                sheet={gradeStatusBySection.get(s.course_section_id)}
              />
            ))}
          </Card>
        </div>
      )}

      <div className="flex flex-col gap-3">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
            Current Courses
          </h2>
          <Link
            to="/courses"
            className="flex items-center gap-1 text-xs font-medium text-primary hover:underline"
          >
            View all <ArrowRight className="size-3" />
          </Link>
        </div>
        {current.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            No courses assigned to you this term.
          </p>
        ) : (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {current.map((c) => (
              <CourseCard
                key={c.course_section_id}
                course={c}
                needsAttention={isIncomplete(gradeStatusBySection.get(c.course_section_id))}
              />
            ))}
          </div>
        )}
      </div>

      {previous.length > 0 && (
        <div className="flex flex-col gap-3">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
            Previous Courses
          </h2>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {previous.map((c) => (
              <CourseCard key={c.course_section_id} course={c} readOnly />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function OverviewStat({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof BookOpen
  label: string
  value: number
}) {
  return (
    <Card>
      <CardContent className="flex items-center gap-3 py-4">
        <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
          <Icon className="size-4" />
        </div>
        <div className="flex flex-col gap-0.5">
          <span className="font-display text-xl font-semibold leading-none tabular-nums">
            {value}
          </span>
          <span className="text-xs text-muted-foreground">{label}</span>
        </div>
      </CardContent>
    </Card>
  )
}

function CourseCard({
  course,
  readOnly,
  needsAttention,
}: {
  course: MyCourseCard
  readOnly?: boolean
  needsAttention?: boolean
}) {
  return (
    <Link
      to={`/courses/${course.course_section_id}`}
      className="block rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
    >
      <Card className="cursor-pointer transition-all hover:-translate-y-0.5 hover:border-primary/50 hover:shadow-md">
        <CardHeader className="pb-2">
          <div className="flex items-start justify-between gap-2">
            <CardTitle className="text-sm">
              {course.course_code} · Section {course.section_code}
            </CardTitle>
            {readOnly ? (
              <Badge variant="outline" className="shrink-0 font-normal">
                {course.term_name}
              </Badge>
            ) : (
              needsAttention && (
                <Badge
                  variant="outline"
                  className="shrink-0 gap-1 border-warning/30 bg-warning/10 font-normal text-warning"
                >
                  <AlertTriangle className="size-3" /> Grades
                </Badge>
              )
            )}
          </div>
          <CardDescription>{course.course_title}</CardDescription>
        </CardHeader>
        <CardContent className="flex items-center justify-between pt-0 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <BookOpen className="size-3.5" /> {course.credits} credits
          </span>
          <span className="flex items-center gap-1">
            <Users className="size-3.5" /> {course.enrolled_count} students
          </span>
          {course.role === 'coordinator' && (
            <Badge variant="secondary" className="font-normal">
              Coordinator
            </Badge>
          )}
        </CardContent>
      </Card>
    </Link>
  )
}

function ActionRow({
  section,
  sheet,
}: {
  section: MyCourseCard
  sheet: GradeSheetReport | undefined
}) {
  if (!sheet) return null
  return (
    <Link
      to={`/courses/${section.course_section_id}?tab=grades`}
      className="flex items-center gap-3 px-4 py-3 transition-colors first:rounded-t-xl last:rounded-b-xl hover:bg-warning/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-inset"
    >
      <AlertTriangle className="size-4 shrink-0 text-warning" />
      <span className="min-w-0 flex-1 truncate text-sm">
        <span className="font-medium">
          {section.course_code} · Section {section.section_code}
        </span>
        <span className="text-muted-foreground">
          {' — '}
          {!sheet.weight_complete
            ? 'assessment weights do not total 100%'
            : `marks missing for ${sheet.incomplete_assessment_titles.join(', ')}`}
        </span>
      </span>
      <ArrowRight className="size-3.5 shrink-0 text-muted-foreground" />
    </Link>
  )
}
