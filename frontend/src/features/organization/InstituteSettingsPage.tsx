import { Lock } from 'lucide-react'

import { useAuth } from '@/features/auth/useAuth'
import { AuditLogTab } from '@/features/organization/AuditLogTab'
import { DepartmentsTab } from '@/features/organization/DepartmentsTab'
import { InstitutionTab } from '@/features/organization/InstitutionTab'
import { ProgramsTab } from '@/features/organization/ProgramsTab'
import { SchoolsTab } from '@/features/organization/SchoolsTab'
import { UsersTab } from '@/features/organization/UsersTab'
import { PageHeader } from '@/components/page-header'
import { RequirePermission } from '@/components/require-permission'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

/** Formerly "Organization Admin" — renamed and restructured: Campuses
 * folded into a combined Institution tab, Program Versions moved to
 * Curriculum & Outcomes (relabeled "Curriculum" there), and Academic
 * Calendar moved to Academic Operations, since none of those three are
 * really "institute settings" so much as curriculum/operational data that
 * happened to live here originally. What's left is genuinely
 * institution-level configuration: the institution's own identity, its
 * org structure (schools/departments/programs), and user/role management. */
export function InstituteSettingsPage() {
  const { hasPermission } = useAuth()

  const tabs = [
    {
      value: 'institution',
      label: 'Institution',
      show: hasPermission('institution.view') || hasPermission('org.view'),
      content: <InstitutionTab />,
    },
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
    { value: 'users', label: 'Users & roles', show: hasPermission('user.view'), content: <UsersTab /> },
    {
      value: 'audit',
      label: 'Audit log',
      show: hasPermission('audit.view'),
      content: <AuditLogTab />,
    },
  ].filter((t) => t.show)

  return (
    <RequirePermission
      anyOf={['org.view', 'program.view', 'user.view', 'institution.view', 'audit.view']}
    >
      <PageHeader
        title="Institute Settings"
        description="Institution identity, campuses, schools, departments, programs, and users."
      />
      {tabs.length === 0 ? (
        <div className="flex flex-col items-center gap-2 rounded-lg border border-dashed py-16 text-center text-muted-foreground">
          <Lock className="size-6 opacity-50" />
          <p className="text-sm">No institute settings sections available.</p>
        </div>
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
