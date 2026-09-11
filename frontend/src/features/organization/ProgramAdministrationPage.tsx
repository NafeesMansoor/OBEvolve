import { useAuth } from '@/features/auth/useAuth'
import { FinalCommitTab } from '@/features/organization/FinalCommitTab'
import { ProgramRoleMatrixTab } from '@/features/organization/ProgramRoleMatrixTab'
import { PageHeader } from '@/components/page-header'
import { RequirePermission } from '@/components/require-permission'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

/** Program-scoped administrative actions, split out of the old Program &
 * Curriculum mega-page: assigning Faculty/Section Coordinator/Course
 * Administrator roles for this program, and permanently committing a
 * finished term's assessment/marks/attainment data — see
 * `app.api.v1.endpoints.program_roles`/`app.services.term_commit`'s module
 * docstrings for why each is a separate, narrower surface from its
 * institution-wide counterpart (or, for Final Commit, from the pre-existing
 * WorkflowStatus/GradeSubmission locks it deliberately supersedes). */
export function ProgramAdministrationPage() {
  const { hasPermission } = useAuth()
  const canManageProgramRoles = hasPermission('program_role.manage')
  const canManageTermCommit = hasPermission('term_commit.manage')

  const tabs = [
    {
      value: 'faculty-roles',
      label: 'Faculty roles',
      show: canManageProgramRoles,
      content: <ProgramRoleMatrixTab />,
    },
    {
      value: 'final-commit',
      label: 'Final Commit',
      show: canManageTermCommit,
      content: <FinalCommitTab />,
    },
  ].filter((t) => t.show)

  return (
    <RequirePermission anyOf={['program_role.manage', 'term_commit.manage']}>
      <PageHeader
        title="Program Administration"
        description="Assign Faculty/Section Coordinator roles and commit a finished term."
      />
      {tabs.length === 0 ? (
        <p className="text-sm text-muted-foreground">No program administration sections available.</p>
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
