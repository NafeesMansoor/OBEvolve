import * as React from 'react'
import { useQueryClient } from '@tanstack/react-query'

import { useAuth } from '@/features/auth/useAuth'
import { apiClient, setActiveProgramCode } from '@/lib/api-client'

const STORAGE_KEY = 'obevolve.active_program_code'

interface Program {
  id: string
  code: string
  name: string
  is_active: boolean
}

interface ActiveProgramContextValue {
  /** Every program this institution has (regardless of which one is
   * selected) — for the switcher UI. */
  programs: Program[]
  isLoading: boolean
  /** The program code currently sent as X-Program-Code on every request
   * (see lib/api-client.ts) — null means no program selected yet, which
   * makes any program-scoped endpoint 400. Auto-selected when the
   * institution has exactly one active program. */
  activeProgramCode: string | null
  setActiveProgram: (code: string | null) => void
}

const ActiveProgramContext = React.createContext<ActiveProgramContextValue | undefined>(undefined)

export function ActiveProgramProvider({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth()
  const queryClient = useQueryClient()
  const [programs, setPrograms] = React.useState<Program[]>([])
  const [isLoading, setIsLoading] = React.useState(true)
  const [activeProgramCode, setActiveProgramCodeState] = React.useState<string | null>(() => {
    try {
      return localStorage.getItem(STORAGE_KEY)
    } catch {
      return null
    }
  })
  // For detecting an actual switch below without making setActiveProgram's
  // identity churn on every activeProgramCode change. Synced in an effect
  // (not during render) — see react-hooks/refs.
  const activeProgramCodeRef = React.useRef(activeProgramCode)
  React.useEffect(() => {
    activeProgramCodeRef.current = activeProgramCode
  }, [activeProgramCode])

  const setActiveProgram = React.useCallback(
    (code: string | null) => {
      const changed = code !== activeProgramCodeRef.current
      setActiveProgramCodeState(code)
      setActiveProgramCode(code)
      try {
        if (code) {
          localStorage.setItem(STORAGE_KEY, code)
        } else {
          localStorage.removeItem(STORAGE_KEY)
        }
      } catch {
        // localStorage unavailable (private browsing etc.) — in-memory state still works.
      }
      if (changed) {
        // Every program-scoped query (offerings, PEOs/POs/mappings,
        // assessments, marks, attainment, improvement plans, ...) is
        // implicitly bound to whichever program's X-Program-Code header was
        // active when it last fetched — react-query's cache key for these
        // doesn't include the program code (most were written before a
        // second program existed to switch to), so on an actual switch
        // they'd otherwise keep serving the *previous* program's cached
        // data until something unrelated happened to remount them. Found
        // live: switching to a second program left every program-scoped
        // tab showing the first program's data. Invalidating the whole
        // cache on switch is blunt but correct, and switching programs is a
        // rare, deliberate action — not a per-render cost.
        void queryClient.invalidateQueries()
      }
    },
    [queryClient],
  )

  // Keep the module-level value lib/api-client.ts's interceptor reads in
  // sync with whatever was restored from localStorage on mount.
  React.useEffect(() => {
    setActiveProgramCode(activeProgramCode)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  React.useEffect(() => {
    // Logged out: nothing to fetch. Don't reset `programs`/`isLoading`
    // state here — the `value` memo below derives the externally-visible
    // values as empty whenever !isAuthenticated instead.
    if (!isAuthenticated) return

    let cancelled = false

    async function fetchPrograms() {
      setIsLoading(true)
      try {
        const res = await apiClient.get<Program[]>('/org/programs')
        if (cancelled) return
        const active = res.data.filter((p) => p.is_active)
        setPrograms(active)

        const stillValid = active.some((p) => p.code === activeProgramCode)
        if (!stillValid) {
          // Always default to a program when at least one exists — every
          // program-scoped page (Program Versions, PEOs/POs, CO-PO mapping,
          // course offerings/sections/faculty/enrollments, assessments) 400s
          // with no active program at all, which previously meant leaving 2+
          // programs unresolved forced a manual switcher click before any of
          // those pages showed anything. The switcher stays available to
          // change it; this only picks a reasonable starting point.
          setActiveProgram(active.length > 0 ? active[0].code : null)
        }
      } catch {
        if (!cancelled) setPrograms([])
      } finally {
        if (!cancelled) setIsLoading(false)
      }
    }

    void fetchPrograms()
    return () => {
      cancelled = true
    }
    // Deliberately only re-runs on auth change — re-fetching on every
    // activeProgramCode change would refetch the list every time the user
    // picks a program, which is unnecessary.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated])

  const value = React.useMemo(
    () => ({
      programs: isAuthenticated ? programs : [],
      isLoading: isAuthenticated && isLoading,
      activeProgramCode,
      setActiveProgram,
    }),
    [isAuthenticated, programs, isLoading, activeProgramCode, setActiveProgram],
  )

  return <ActiveProgramContext.Provider value={value}>{children}</ActiveProgramContext.Provider>
}

export function useActiveProgram(): ActiveProgramContextValue {
  const ctx = React.useContext(ActiveProgramContext)
  if (!ctx) {
    throw new Error('useActiveProgram must be used within an ActiveProgramProvider')
  }
  return ctx
}
