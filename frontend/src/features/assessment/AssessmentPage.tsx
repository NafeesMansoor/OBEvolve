import { useAuth } from '@/features/auth/useAuth'
import { AssessmentsTab } from '@/features/assessment/AssessmentsTab'
import { AttainmentTab } from '@/features/assessment/AttainmentTab'
import { MarksEntryTab } from '@/features/assessment/MarksEntryTab'
import { PendingDocumentsTab } from '@/features/assessment/PendingDocumentsTab'
import { QuestionsTab } from '@/features/assessment/QuestionsTab'
import { RubricsTab } from '@/features/assessment/RubricsTab'
import { TypesTab } from '@/features/assessment/TypesTab'
import type { PendingAssessmentDocument } from '@/features/assessment/types'
import { useActiveProgram } from '@/lib/active-program-context'
import { useEntityList } from '@/lib/crud-hooks'
import { Badge } from '@/components/ui/badge'
import { PageHeader } from '@/components/page-header'
import { RequirePermission } from '@/components/require-permission'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

export function AssessmentPage() {
  const { hasPermission } = useAuth()
  const canView = hasPermission('assessment.view')
  const canSeeMarks = hasPermission('marks.enter') || canView
  const canSeeAttainment =
    hasPermission('attainment.calculate') || hasPermission('assessment.approve') || canView
  const canReview = hasPermission('assessment.approve')
  const { activeProgramCode } = useActiveProgram()

  const { data: pending } = useEntityList<PendingAssessmentDocument>(
    ['assessment', 'documents', 'pending'],
    '/assessment/documents/pending',
    undefined,
    { enabled: canReview && Boolean(activeProgramCode) },
  )

  const tabs = [
    { value: 'types', label: 'Assessment types', show: canView, content: <TypesTab /> },
    { value: 'rubrics', label: 'Rubrics', show: canView, content: <RubricsTab /> },
    { value: 'questions', label: 'Question bank', show: canView, content: <QuestionsTab /> },
    { value: 'assessments', label: 'Assessments', show: canView, content: <AssessmentsTab /> },
    { value: 'marks', label: 'Marks entry', show: canSeeMarks, content: <MarksEntryTab /> },
    { value: 'attainment', label: 'Attainment', show: canSeeAttainment, content: <AttainmentTab /> },
    {
      value: 'pending-documents',
      label: (
        <span className="flex items-center gap-1.5">
          Pending documents
          {pending && pending.length > 0 && (
            <Badge variant="outline" className="border-transparent bg-warning/15 px-1.5 text-warning">
              {pending.length}
            </Badge>
          )}
        </span>
      ),
      show: canReview,
      content: <PendingDocumentsTab />,
    },
  ].filter((t) => t.show)

  return (
    <RequirePermission anyOf={['assessment.view', 'marks.enter', 'attainment.calculate']}>
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
