import * as React from 'react'

import { useAuth } from '@/features/auth/useAuth'

const STORAGE_KEY = 'obevolve.active_role'

interface ActiveRoleContextValue {
  /** The role currently selected in the top-bar switcher, or null if none
   * selected (or the user only holds one role) — in which case every nav
   * section the user has permission for is shown, same as before this
   * feature existed. This is presentational only: it never restricts which
   * API calls succeed, only which sidebar sections are emphasized. */
  activeRole: string | null
  setActiveRole: (role: string | null) => void
}

const ActiveRoleContext = React.createContext<ActiveRoleContextValue | undefined>(undefined)

export function ActiveRoleProvider({ children }: { children: React.ReactNode }) {
  const { user } = useAuth()
  const [activeRole, setActiveRoleState] = React.useState<string | null>(() => {
    try {
      return localStorage.getItem(STORAGE_KEY)
    } catch {
      return null
    }
  })

  // If the stored role is no longer one the user holds (different account,
  // role revoked, etc.), drop it rather than filtering everything out.
  // Adjusted directly during render rather than in an effect — this only
  // fires once per invalidation since activeRole becomes null immediately.
  if (activeRole && user && !user.roles.includes(activeRole)) {
    setActiveRoleState(null)
  }

  const setActiveRole = React.useCallback((role: string | null) => {
    setActiveRoleState(role)
    try {
      if (role) {
        localStorage.setItem(STORAGE_KEY, role)
      } else {
        localStorage.removeItem(STORAGE_KEY)
      }
    } catch {
      // localStorage unavailable (private browsing etc.) — in-memory state still works.
    }
  }, [])

  const value = React.useMemo(() => ({ activeRole, setActiveRole }), [activeRole, setActiveRole])

  return <ActiveRoleContext.Provider value={value}>{children}</ActiveRoleContext.Provider>
}

export function useActiveRole(): ActiveRoleContextValue {
  const ctx = React.useContext(ActiveRoleContext)
  if (!ctx) {
    throw new Error('useActiveRole must be used within an ActiveRoleProvider')
  }
  return ctx
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
  curriculum: ['Faculty', 'Course Coordinator', 'Program Coordinator', 'Institution Administrator', 'Super Administrator'],
  academic: ['Faculty', 'Course Coordinator', 'Registrar', 'Examination Administrator', 'Institution Administrator', 'Super Administrator'],
  grading: ['Faculty', 'Course Coordinator', 'Examination Administrator', 'Institution Administrator', 'Super Administrator'],
  assessment: ['Faculty', 'Course Coordinator', 'Examination Administrator', 'Institution Administrator', 'Super Administrator'],
  organization: ['Institution Administrator', 'Super Administrator'],
  rawData: [
    'Institution Administrator',
    'Super Administrator',
    'Program Administrator',
    'Course Administrator',
    'Program Coordinator',
  ],
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
