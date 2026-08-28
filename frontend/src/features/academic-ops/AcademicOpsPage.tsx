import { useAuth } from '@/features/auth/useAuth'
import { AcademicCalendarTab } from '@/features/organization/AcademicCalendarTab'
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

  const tabs = [
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
      value: 'calendar',
      label: 'Academic calendar',
      show: hasPermission('academic_calendar.view'),
      content: <AcademicCalendarTab />,
    },
  ].filter((t) => t.show)

  return (
    <RequirePermission anyOf={['section.view', 'student.view', 'academic_calendar.view']}>
      <PageHeader
        title="Academic Operations"
        description="Course offerings, sections, faculty assignments, enrollments, students, and the academic calendar."
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
