import { useAuth } from '@/features/auth/useAuth'
import { CurriculumFeedbackTab } from '@/features/curriculum/CurriculumFeedbackTab'
import { MissionVisionTab } from '@/features/curriculum/MissionVisionTab'
import { PEOsTab } from '@/features/curriculum/PEOsTab'
import { PerformanceIndicatorsTab } from '@/features/curriculum/PerformanceIndicatorsTab'
import { ProgramOutcomesTab } from '@/features/curriculum/ProgramOutcomesTab'
import { ProgramVersionsTab } from '@/features/organization/ProgramVersionsTab'
import { PageHeader } from '@/components/page-header'
import { RequirePermission } from '@/components/require-permission'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

/** Program & Curriculum Level content only (Master_Architecture_Part1.md §1A:
 * "the strategic and relatively stable academic framework") — curricula
 * (program versions, publish/unpublish/version history), mission & vision,
 * PEOs, program outcomes, performance indicators, and the Program
 * Coordinator feedback loop on all of the above.
 *
 * Split out of what used to be one 12-tab mega-page (mapping matrices moved
 * to Outcome Mapping, faculty-role/final-commit administration moved to
 * Program Administration — see those pages' own docstrings) once this page
 * had grown too cluttered for a single tab bar to stay usable.
 *
 * `embedded`: true when rendered as a nested tab under Institute Settings →
 * Programs (Institution Administrator's nav — see layout.tsx's
 * `institution.manage`-gated nav filtering) instead of at its own top-level
 * route; suppresses the page's own header, which would otherwise duplicate
 * the parent tab's. */
export function ProgramSettingsPage({ embedded = false }: { embedded?: boolean } = {}) {
  const { hasPermission } = useAuth()
  const canView = hasPermission('curriculum.view')
  const canViewProgram = hasPermission('program.view')
  const canSeeFeedback = hasPermission('curriculum.view') || hasPermission('curriculum_feedback.create')

  const tabs = [
    {
      value: 'curriculum',
      label: 'Curriculum',
      show: canViewProgram,
      content: <ProgramVersionsTab />,
    },
    {
      value: 'mission-vision',
      label: 'Mission & Vision',
      show: canView,
      content: <MissionVisionTab />,
    },
    { value: 'peos', label: 'PEOs', show: canView, content: <PEOsTab /> },
    { value: 'program-outcomes', label: 'Program Outcomes', show: canView, content: <ProgramOutcomesTab /> },
    {
      value: 'performance-indicators',
      label: 'Performance Indicators',
      show: canView,
      content: <PerformanceIndicatorsTab />,
    },
    {
      value: 'curriculum-feedback',
      label: 'Feedback',
      show: canSeeFeedback,
      content: <CurriculumFeedbackTab />,
    },
  ].filter((t) => t.show)

  return (
    <RequirePermission anyOf={['curriculum.view', 'program.view', 'curriculum_feedback.create']}>
      {!embedded && (
        <PageHeader
          title="Program & Curriculum"
          description="Curricula, mission & vision, PEOs, program outcomes, performance indicators, and feedback."
        />
      )}
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
