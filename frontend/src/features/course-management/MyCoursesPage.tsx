import { FacultyCoursesPanel } from '@/features/faculty-dashboard/FacultyCoursesPanel'
import { PageHeader } from '@/components/page-header'
import { RequirePermission } from '@/components/require-permission'

/** Faculty Module spec §30: "Courses" nav item — the course picker that
 * opens Course Management for a selected section.
 *
 * `embedded`: see curriculum/ProgramSettingsPage's docstring — true when
 * nested under Institute Settings → Programs instead of its own top-level
 * route (Institution Administrator's nav only). */
export function MyCoursesPage({ embedded = false }: { embedded?: boolean } = {}) {
  return (
    <RequirePermission anyOf={['section.view']}>
      {!embedded && (
        <PageHeader
          title="My Courses"
          description="Sections you're assigned to, current and previous semesters."
        />
      )}
      <FacultyCoursesPanel />
    </RequirePermission>
  )
}
