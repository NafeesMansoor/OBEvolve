import { FacultyCoursesPanel } from '@/features/faculty-dashboard/FacultyCoursesPanel'
import { PageHeader } from '@/components/page-header'
import { RequirePermission } from '@/components/require-permission'

/** Faculty Module spec §30: "Courses" nav item — the course picker that
 * opens Course Management for a selected section. */
export function MyCoursesPage() {
  return (
    <RequirePermission anyOf={['section.view']}>
      <PageHeader
        title="My Courses"
        description="Sections you're assigned to, current and previous semesters."
      />
      <FacultyCoursesPanel />
    </RequirePermission>
  )
}
