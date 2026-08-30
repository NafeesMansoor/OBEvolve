import * as React from 'react'

import { useAuth } from '@/features/auth/useAuth'
import { type AttainmentStage, AttainmentFlowDiagram } from '@/features/analytics/AttainmentFlowDiagram'
import { FacultyAnalyticsPanel } from '@/features/analytics/FacultyAnalyticsPanel'
import { AttainmentTab as CourseAttainmentTab } from '@/features/assessment/AttainmentTab'
import { POAttainmentTab } from '@/features/curriculum/POAttainmentTab'
import { ProgramAnalyticsTab } from '@/features/curriculum/ProgramAnalyticsTab'
import { PageHeader } from '@/components/page-header'
import { RequirePermission } from '@/components/require-permission'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'

/** All the read-only analysis/attainment dashboards in one place, so
 * "how are we doing against our outcomes" doesn't require hunting through
 * the settings pages that produced the underlying data. Course Attainment
 * and PO Attainment are the same underlying calculation at two levels
 * (course outcomes vs. program outcomes); Program Analytics rolls both up
 * further. */
export function AnalyticsPage() {
  const { hasPermission } = useAuth()
  const canViewProgram = hasPermission('program.view')
  const canSeeCourseAttainment =
    hasPermission('attainment.calculate') || hasPermission('assessment.approve') || hasPermission('assessment.view')
  // A caller with *only* assessment.view (no program.view/attainment.calculate/
  // assessment.approve) is Faculty, not an admin/coordinator — give them the
  // cross-their-own-courses view instead of the institution-wide rollup tabs.
  const isFacultyOnly = hasPermission('assessment.view') && !canViewProgram && !hasPermission('assessment.approve')

  const tabs = [
    {
      value: 'my-courses',
      label: 'My Courses',
      show: isFacultyOnly,
      stage: 'course' as AttainmentStage,
      content: <FacultyAnalyticsPanel />,
    },
    {
      value: 'po-attainment',
      label: 'PO Attainment',
      show: canViewProgram,
      stage: 'program' as AttainmentStage,
      content: <POAttainmentTab />,
    },
    {
      value: 'program-analytics',
      label: 'Program Analytics',
      show: canViewProgram,
      stage: 'rollup' as AttainmentStage,
      content: <ProgramAnalyticsTab />,
    },
    {
      // Institution-wide (every course in the program) — not the same
      // scope as "My Courses" above, so hidden for a Faculty-only viewer
      // to avoid leaking sections they don't teach.
      value: 'course-attainment',
      label: 'Course Attainment',
      show: canSeeCourseAttainment && !isFacultyOnly,
      stage: 'course' as AttainmentStage,
      content: <CourseAttainmentTab />,
    },
  ].filter((t) => t.show)

  const [activeTab, setActiveTab] = React.useState(tabs[0]?.value)
  const activeStage = tabs.find((t) => t.value === activeTab)?.stage ?? 'course'

  return (
    <RequirePermission anyOf={['program.view', 'attainment.calculate', 'assessment.approve', 'assessment.view']}>
      <PageHeader
        title="Analytics"
        description="Course and program outcome attainment, and program-wide analytics."
      />
      <AttainmentFlowDiagram activeStage={activeStage} />
      <Tabs value={activeTab} onValueChange={setActiveTab}>
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
