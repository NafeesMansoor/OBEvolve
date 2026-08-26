import { useAuth } from '@/features/auth/useAuth'
import { AcademicCalendarTab } from '@/features/organization/AcademicCalendarTab'
import { CampusesTab } from '@/features/organization/CampusesTab'
import { DepartmentsTab } from '@/features/organization/DepartmentsTab'
import { ProgramVersionsTab } from '@/features/organization/ProgramVersionsTab'
import { ProgramsTab } from '@/features/organization/ProgramsTab'
import { SchoolsTab } from '@/features/organization/SchoolsTab'
import { UsersTab } from '@/features/organization/UsersTab'
import { PageHeader } from '@/components/page-header'
import { RequirePermission } from '@/components/require-permission'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

export function OrganizationPage() {
  const { hasPermission } = useAuth()

  const tabs = [
    { value: 'campuses', label: 'Campuses', show: hasPermission('org.view'), content: <CampusesTab /> },
    { value: 'schools', label: 'Schools', show: hasPermission('org.view'), content: <SchoolsTab /> },
    {
      value: 'departments',
      label: 'Departments',
      show: hasPermission('org.view'),
      content: <DepartmentsTab />,
    },
    {
      value: 'programs',
      label: 'Programs',
      show: hasPermission('program.view'),
      content: <ProgramsTab />,
    },
    {
      value: 'program-versions',
      label: 'Program versions',
      show: hasPermission('program.view'),
      content: <ProgramVersionsTab />,
    },
    {
      value: 'calendar',
      label: 'Academic calendar',
      show: hasPermission('academic_calendar.view'),
      content: <AcademicCalendarTab />,
    },
    { value: 'users', label: 'Users & roles', show: hasPermission('user.view'), content: <UsersTab /> },
  ].filter((t) => t.show)

  return (
    <RequirePermission anyOf={['org.view', 'program.view', 'user.view', 'academic_calendar.view']}>
      <PageHeader
        title="Organization admin"
        description="Campuses, schools, departments, programs, academic calendar, and users."
      />
      {tabs.length === 0 ? (
        <p className="text-sm text-muted-foreground">No organization admin sections available.</p>
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
