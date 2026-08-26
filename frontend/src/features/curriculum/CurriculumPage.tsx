import { useAuth } from '@/features/auth/useAuth'
import { CoPoMatrixTab } from '@/features/curriculum/CoPoMatrixTab'
import { CourseOutcomesTab } from '@/features/curriculum/CourseOutcomesTab'
import { CourseVersionsTab } from '@/features/curriculum/CourseVersionsTab'
import { CoursesTab } from '@/features/curriculum/CoursesTab'
import { FrameworksTab } from '@/features/curriculum/FrameworksTab'
import { PEOsTab } from '@/features/curriculum/PEOsTab'
import { PeoPoMatrixTab } from '@/features/curriculum/PeoPoMatrixTab'
import { ProgramOutcomesTab } from '@/features/curriculum/ProgramOutcomesTab'
import { PageHeader } from '@/components/page-header'
import { RequirePermission } from '@/components/require-permission'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

export function CurriculumPage() {
  const { hasPermission } = useAuth()
  const canView = hasPermission('curriculum.view')

  const tabs = [
    { value: 'courses', label: 'Courses', show: canView, content: <CoursesTab /> },
    { value: 'course-versions', label: 'Course versions', show: canView, content: <CourseVersionsTab /> },
    { value: 'peos', label: 'PEOs', show: canView, content: <PEOsTab /> },
    { value: 'program-outcomes', label: 'Program Outcomes', show: canView, content: <ProgramOutcomesTab /> },
    { value: 'course-outcomes', label: 'Course Outcomes', show: canView, content: <CourseOutcomesTab /> },
    { value: 'co-po-matrix', label: 'CO-PO Mapping', show: canView, content: <CoPoMatrixTab /> },
    { value: 'peo-po-matrix', label: 'PEO-PO Mapping', show: canView, content: <PeoPoMatrixTab /> },
    { value: 'frameworks', label: 'Accreditation Framework', show: canView, content: <FrameworksTab /> },
  ].filter((t) => t.show)

  return (
    <RequirePermission anyOf={['curriculum.view']}>
      <PageHeader
        title="Curriculum & Outcomes"
        description="Courses, PEOs, program & course outcomes, and outcome mapping matrices."
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
