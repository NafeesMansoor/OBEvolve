import { useAuth } from '@/features/auth/useAuth'
import { AcademicCalendarTab } from '@/features/organization/AcademicCalendarTab'
import { CohortsTab } from '@/features/academic-ops/CohortsTab'
import { EnrollmentsTab } from '@/features/academic-ops/EnrollmentsTab'
import { FacultyAssignmentsTab } from '@/features/academic-ops/FacultyAssignmentsTab'
import { OfferingsTab } from '@/features/academic-ops/OfferingsTab'
import { SectionsTab } from '@/features/academic-ops/SectionsTab'
import { StudentsTab } from '@/features/academic-ops/StudentsTab'
import { PageHeader } from '@/components/page-header'
import { RequirePermission } from '@/components/require-permission'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

export function AcademicOpsPage() {
  const { hasPermission } = useAuth()

  // Academic calendar leads the list: a trimester must be defined (and
  // activated) before offerings/sections/faculty/enrollments/cohorts can
  // reference it, so the tab that defines it comes before the tabs that
  // operate within it — also makes it the default-open tab (tabs[0]) an
  // Institution Administrator lands on here, since term setup is their job,
  // not the Program Coordinator's operational tabs that follow.
  const tabs = [
    {
      value: 'calendar',
      label: 'Academic calendar',
      show: hasPermission('academic_calendar.view'),
      content: <AcademicCalendarTab />,
    },
    { value: 'offerings', label: 'Course offerings', show: hasPermission('section.view'), content: <OfferingsTab /> },
    { value: 'sections', label: 'Sections', show: hasPermission('section.view'), content: <SectionsTab /> },
    {
      value: 'faculty',
      label: 'Faculty assignments',
      show: hasPermission('section.view'),
      content: <FacultyAssignmentsTab />,
    },
    { value: 'enrollments', label: 'Enrollments', show: hasPermission('student.view'), content: <EnrollmentsTab /> },
    { value: 'students', label: 'Students', show: hasPermission('student.view'), content: <StudentsTab /> },
    {
      value: 'cohorts',
      label: 'Student cohorts',
      show: hasPermission('section.view'),
      content: <CohortsTab />,
    },
  ].filter((t) => t.show)

  return (
    <RequirePermission anyOf={['section.view', 'student.view', 'academic_calendar.view']}>
      <PageHeader
        title="Trimester Management"
        description="Course offerings, sections, faculty assignments, enrollments, students, cohorts, and the academic calendar."
      />
      {tabs.length === 0 ? (
        <p className="text-sm text-muted-foreground">No academic operations sections available.</p>
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
