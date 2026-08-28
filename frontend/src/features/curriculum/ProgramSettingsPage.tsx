import { useAuth } from '@/features/auth/useAuth'
import { CoPoMatrixTab } from '@/features/curriculum/CoPoMatrixTab'
import { FrameworksTab } from '@/features/curriculum/FrameworksTab'
import { PEOsTab } from '@/features/curriculum/PEOsTab'
import { PeoPoMatrixTab } from '@/features/curriculum/PeoPoMatrixTab'
import { ProgramOutcomesTab } from '@/features/curriculum/ProgramOutcomesTab'
import { ProgramVersionsTab } from '@/features/organization/ProgramVersionsTab'
import { PageHeader } from '@/components/page-header'
import { RequirePermission } from '@/components/require-permission'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

/** Program-level half of the old "Curriculum & Outcomes" page: everything
 * tied to PEOs and POs — curricula (program versions), PEOs, POs, the
 * CO-PO / PEO-PO mapping matrices, and the accreditation framework catalog
 * those POs are drawn from. Course-level configuration (the course catalog,
 * course versions, course outcomes) lives in Course Level Settings instead.
 * Attainment/analysis views for these same POs live under Analytics, not
 * here — this page is CRUD/configuration only. */
export function ProgramSettingsPage() {
  const { hasPermission } = useAuth()
  const canView = hasPermission('curriculum.view')
  const canViewProgram = hasPermission('program.view')

  const tabs = [
    {
      value: 'curriculum',
      label: 'Curriculum',
      show: canViewProgram,
      content: <ProgramVersionsTab />,
    },
    { value: 'peos', label: 'PEOs', show: canView, content: <PEOsTab /> },
    { value: 'program-outcomes', label: 'Program Outcomes', show: canView, content: <ProgramOutcomesTab /> },
    { value: 'co-po-matrix', label: 'CO-PO Mapping', show: canView, content: <CoPoMatrixTab /> },
    { value: 'peo-po-matrix', label: 'PEO-PO Mapping', show: canView, content: <PeoPoMatrixTab /> },
    { value: 'frameworks', label: 'Accreditation Framework', show: canView, content: <FrameworksTab /> },
  ].filter((t) => t.show)

  return (
    <RequirePermission anyOf={['curriculum.view', 'program.view']}>
      <PageHeader
        title="Program Level Setting"
        description="Curricula, PEOs, program outcomes, and the outcome mapping matrices."
      />
      {tabs.length === 0 ? (
        <p className="text-sm text-muted-foreground">No program-level settings available.</p>
      ) : (
        <Tabs defaultValue={tabs[0]?.value}>
          <TabsList className="h-auto flex-wrap justify-start gap-1">
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
