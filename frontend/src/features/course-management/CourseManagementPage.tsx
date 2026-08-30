import { Navigate, useParams, useSearchParams } from 'react-router-dom'

import { useAuth } from '@/features/auth/useAuth'
import { AssessmentsTab } from '@/features/course-management/AssessmentsTab'
import { CourseFilesTab } from '@/features/course-management/CourseFilesTab'
import { CourseSettingsTab } from '@/features/course-management/CourseSettingsTab'
import { GradesTab } from '@/features/course-management/GradesTab'
import { MarksEntryTab } from '@/features/course-management/MarksEntryTab'
import { OverviewTab } from '@/features/course-management/OverviewTab'
import { SectionAnalyticsTab } from '@/features/course-management/SectionAnalyticsTab'
import { SectionStudentsTab } from '@/features/course-management/SectionStudentsTab'
import { useMyCourses } from '@/features/course-management/useMyCourses'
import { PageHeader } from '@/components/page-header'
import { RequirePermission } from '@/components/require-permission'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

/** Faculty Module spec §3: the per-course-section workspace opened from
 * "Current Courses" (or Previous Courses, read-mostly). Course selection
 * itself (a `CourseSection` id) comes from the route param — there is no
 * separate "pick a course" landing page here, since the Dashboard/`/courses`
 * grid already is that picker. */
export function CourseManagementPage() {
  const { sectionId } = useParams<{ sectionId: string }>()
  const [searchParams] = useSearchParams()
  const { hasPermission } = useAuth()
  const { current, previous, isLoading } = useMyCourses()

  if (isLoading) {
    return <Skeleton className="h-64 w-full" />
  }

  const course = [...current, ...previous].find((c) => c.course_section_id === sectionId)
  if (!sectionId) return <Navigate to="/courses" replace />
  if (!course) {
    return (
      <div className="rounded-lg border border-dashed p-10 text-center text-sm text-muted-foreground">
        This course section isn&apos;t assigned to you, or doesn&apos;t exist.
      </div>
    )
  }

  const isCurrent = course.is_current_term
  const defaultTab = searchParams.get('tab') ?? 'overview'

  return (
    <RequirePermission anyOf={['section.view']}>
      <PageHeader
        title={`${course.course_code} · ${course.course_title} · Section ${course.section_code}`}
        description={`${course.term_name} · ${course.credits} credits${
          !isCurrent ? ' · Previous semester (view-only)' : ''
        }`}
      />
      <Tabs defaultValue={defaultTab}>
        <TabsList className="flex-wrap">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="settings">Course Settings</TabsTrigger>
          <TabsTrigger value="files">Course Files</TabsTrigger>
          <TabsTrigger value="students">Students</TabsTrigger>
          {hasPermission('assessment.view') && (
            <TabsTrigger value="assessments">Assessments</TabsTrigger>
          )}
          {hasPermission('marks.enter') && isCurrent && (
            <TabsTrigger value="marks">Marks Entry</TabsTrigger>
          )}
          <TabsTrigger value="grades">Grades</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <OverviewTab course={course} />
        </TabsContent>
        <TabsContent value="settings">
          <CourseSettingsTab course={course} />
        </TabsContent>
        <TabsContent value="files">
          <CourseFilesTab course={course} />
        </TabsContent>
        <TabsContent value="students">
          <SectionStudentsTab course={course} />
        </TabsContent>
        <TabsContent value="assessments">
          <AssessmentsTab course={course} />
        </TabsContent>
        <TabsContent value="marks">
          <MarksEntryTab course={course} />
        </TabsContent>
        <TabsContent value="grades">
          <GradesTab course={course} />
        </TabsContent>
        <TabsContent value="analytics">
          <SectionAnalyticsTab course={course} />
        </TabsContent>
      </Tabs>
    </RequirePermission>
  )
}
