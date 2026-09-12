import { useAuth } from '@/features/auth/useAuth'
import { CoPoMatrixTab } from '@/features/curriculum/CoPoMatrixTab'
import { FrameworksTab } from '@/features/curriculum/FrameworksTab'
import { KpiMappingTab } from '@/features/curriculum/KpiMappingTab'
import { PeoPoMatrixTab } from '@/features/curriculum/PeoPoMatrixTab'
import { PageHeader } from '@/components/page-header'
import { RequirePermission } from '@/components/require-permission'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

/** Master_Architecture_Part1.md §2's "Outcome Mapping" nav group, split out
 * of Program & Curriculum once that page's tab bar grew too cluttered: every
 * mapping matrix (PEO<->PO, CO<->PO, PO/PI<->Knowledge Profile/CEP/CEA) plus
 * the read-only accreditation framework catalog those mappings draw their
 * targets from.
 *
 * `embedded`: see ProgramSettingsPage's docstring — true when nested under
 * Institute Settings → Programs instead of its own top-level route. */
export function OutcomeMappingPage({ embedded = false }: { embedded?: boolean } = {}) {
  const { hasPermission } = useAuth()
  const canView = hasPermission('curriculum.view')

  const tabs = [
    { value: 'peo-po-matrix', label: 'PEO-PO Mapping', show: canView, content: <PeoPoMatrixTab /> },
    { value: 'co-po-matrix', label: 'Course Outcome Mapping', show: canView, content: <CoPoMatrixTab /> },
    {
      value: 'kpi-mapping',
      label: 'K/CEP/CEA Mapping',
      show: canView,
      content: <KpiMappingTab />,
    },
    { value: 'frameworks', label: 'Accreditation Framework', show: canView, content: <FrameworksTab /> },
  ].filter((t) => t.show)

  return (
    <RequirePermission anyOf={['curriculum.view']}>
      {!embedded && (
        <PageHeader
          title="Outcome Mapping"
          description="PEO-PO, CO-PO, and Knowledge Profile/CEP/CEA mapping matrices, and the accreditation framework catalog."
        />
      )}
      {tabs.length === 0 ? (
        <p className="text-sm text-muted-foreground">No outcome mapping sections available.</p>
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
