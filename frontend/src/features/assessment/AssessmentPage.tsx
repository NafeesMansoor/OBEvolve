import { useAuth } from '@/features/auth/useAuth'
import { AssessmentsTab } from '@/features/assessment/AssessmentsTab'
import { QuestionsTab } from '@/features/assessment/QuestionsTab'
import { RubricsTab } from '@/features/assessment/RubricsTab'
import { TypesTab } from '@/features/assessment/TypesTab'
import { PageHeader } from '@/components/page-header'
import { RequirePermission } from '@/components/require-permission'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

export function AssessmentPage() {
  const { hasPermission } = useAuth()
  const canView = hasPermission('assessment.view')

  const tabs = [
    { value: 'types', label: 'Assessment types', show: canView, content: <TypesTab /> },
    { value: 'rubrics', label: 'Rubrics', show: canView, content: <RubricsTab /> },
    { value: 'questions', label: 'Question bank', show: canView, content: <QuestionsTab /> },
    { value: 'assessments', label: 'Assessments', show: canView, content: <AssessmentsTab /> },
  ].filter((t) => t.show)

  return (
    <RequirePermission anyOf={['assessment.view']}>
      <PageHeader
        title="Assessment"
        description="Assessment types, rubrics, the question bank, and assessments."
      />
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
    </RequirePermission>
  )
}
