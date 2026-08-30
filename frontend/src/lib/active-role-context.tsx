import { useAuth } from '@/features/auth/useAuth'

/**
 * Thin compatibility wrapper: the actual `activeRole`/`setActiveRole` state
 * now lives in lib/auth-context.tsx (it restricts `hasPermission` there,
 * not just this file's presentational nav-dimming — a real permission
 * effect needs to live where `hasPermission` itself is computed, since
 * dozens of components call `useAuth().hasPermission(...)` directly and
 * would never see a separately-tracked "active role" otherwise). Kept as
 * its own hook so the three existing call sites (app/layout.tsx,
 * components/role-switcher.tsx) don't need to import from auth-context
 * directly.
 */
export function useActiveRole() {
  const { activeRole, setActiveRole } = useAuth()
  return { activeRole, setActiveRole }
}

/**
 * Maps each nav section to the role(s) it's normally relevant to. Roles not
 * listed here (or an unrecognized active role) fall back to showing the
 * section if the user has permission — see AppLayout's filtering logic.
 * Role names match the seed data (see app/seed / docs) loosely by
 * case-insensitive substring so minor naming variance doesn't hide sections.
 */
export const NAV_SECTION_ROLES: Record<string, string[]> = {
  dashboard: [],
  courses: ['Faculty', 'Course Coordinator', 'Program Coordinator', 'Institution Administrator', 'Super Administrator'],
  questionBank: ['Faculty', 'Course Coordinator', 'Institution Administrator', 'Super Administrator'],
  courseSettings: ['Faculty', 'Course Coordinator', 'Program Coordinator', 'Institution Administrator', 'Super Administrator'],
  programSettings: ['Program Coordinator', 'Institution Administrator', 'Super Administrator'],
  academic: ['Faculty', 'Course Coordinator', 'Registrar', 'Examination Administrator', 'Institution Administrator', 'Super Administrator'],
  grading: ['Faculty', 'Course Coordinator', 'Examination Administrator', 'Institution Administrator', 'Super Administrator'],
  assessment: ['Faculty', 'Course Coordinator', 'Examination Administrator', 'Institution Administrator', 'Super Administrator'],
  analytics: ['Faculty', 'Course Coordinator', 'Program Coordinator', 'Institution Administrator', 'Super Administrator'],
  organization: ['Institution Administrator', 'Super Administrator'],
  rawData: [
    'Institution Administrator',
    'Super Administrator',
    'Program Administrator',
    'Course Administrator',
    'Program Coordinator',
  ],
  about: [],
}

/** Case-insensitive, substring-tolerant match against the roles list above. */
export function sectionMatchesRole(sectionKey: string, role: string): boolean {
  const relevant = NAV_SECTION_ROLES[sectionKey]
  if (!relevant || relevant.length === 0) return true
  const roleLower = role.toLowerCase()
  return relevant.some(
    (r) => r.toLowerCase() === roleLower || roleLower.includes(r.toLowerCase()) || r.toLowerCase().includes(roleLower),
  )
}
