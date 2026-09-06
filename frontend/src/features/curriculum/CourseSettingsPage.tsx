import { useAuth } from '@/features/auth/useAuth'
import { CourseOutcomesTab } from '@/features/curriculum/CourseOutcomesTab'
import { CourseTypesTab } from '@/features/curriculum/CourseTypesTab'
import { CourseVersionsTab } from '@/features/curriculum/CourseVersionsTab'
import { CoursesTab } from '@/features/curriculum/CoursesTab'
import { PageHeader } from '@/components/page-header'
import { RequirePermission } from '@/components/require-permission'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

/** Course-level half of the old "Curriculum & Outcomes" page: the course
 * catalog, its versions, and each version's course outcomes (COs) — the
 * things a course/faculty coordinator configures independent of any one
 * program. PO/PEO-related configuration lives in Program Level Setting
 * instead (see ProgramSettingsPage). Course Types (docs/
 * course_level_settings_and_approval_workflow.md §1-§3) live here too —
 * they're the classification that drives which course-level sections a
 * Course Teacher may propose changes to. */
export function CourseSettingsPage() {
  const { hasPermission } = useAuth()
  const canView = hasPermission('curriculum.view')
  const canManageCourseTypes = hasPermission('course_type.manage')

  const tabs = [
    { value: 'courses', label: 'Courses', show: canView, content: <CoursesTab /> },
    { value: 'course-versions', label: 'Course versions', show: canView, content: <CourseVersionsTab /> },
    { value: 'course-outcomes', label: 'Course Outcomes', show: canView, content: <CourseOutcomesTab /> },
    {
      value: 'course-types',
      label: 'Course Types',
      show: canManageCourseTypes,
      content: <CourseTypesTab />,
    },
  ].filter((t) => t.show)

  return (
    <RequirePermission anyOf={['curriculum.view']}>
      <PageHeader
        title="Course Level Settings"
        description="The course catalog, course versions, and each version's course outcomes (COs)."
      />
      {tabs.length === 0 ? (
        <p className="text-sm text-muted-foreground">No course settings sections available.</p>
      ) : (
        <Tabs defaultValue={tabs[0]?.value}>
          <TabsList className="flex-wrap">
            {tabs.map((t) => (
              <TabsTrigger key={t.value} value={t.value}>
                {t.label}
              </TabsTrigger>
            ))}
          </TabsList>
          {tabs.map((t) => (
            <TabsContent key={t.value} value={t.value}>
              {t.content}
            </TabsContent>
          ))}
        </Tabs>
      )}
    </RequirePermission>
  )
}
