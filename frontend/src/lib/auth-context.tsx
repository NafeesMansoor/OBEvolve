import * as React from 'react'

import {
  ApiError,
  apiClient,
  clearTokens,
  getRefreshToken,
  registerUnauthorizedHandler,
  setAccessToken,
  setRefreshToken,
} from '@/lib/api-client'

export interface AuthUser {
  id: string
  email: string
  full_name: string
  is_active: boolean
  mfa_enabled: boolean
  bio: string | null
  /** Flat, already-deduplicated permission codes — see CurrentUserRead on the backend. */
  permissions: string[]
  /** Flat role names. The backend resolves scope-aware permission checks
   * server-side (app/services/rbac.py); the frontend only needs the flat
   * union of permissions to decide what UI to show. */
  roles: string[]
  /** Role name -> that role's own permission codes — see CurrentUserRead's
   * `role_permissions` docstring on the backend. Used by `hasPermission`
   * below to restrict checks to a single "viewed as" role instead of the
   * full union, when one is active (see activeRole/setActiveRole). */
  role_permissions: Record<string, string[]>
}

const ACTIVE_ROLE_STORAGE_KEY = 'obevolve.active_role'

interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

interface AuthContextValue {
  user: AuthUser | null
  /** True while the initial session check (or a login/refresh) is in flight. */
  isLoading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  /** Alternate sign-in path: `idToken` is the credential Google Identity
   * Services returns after the user picks a Google account in the browser.
   * Only succeeds if that verified email matches an existing active user —
   * it's an alternate path to the same accounts password login reaches,
   * not a way to create new ones. */
  loginWithGoogle: (idToken: string) => Promise<void>
  logout: () => void
  /** Re-fetches /auth/me — call after a self-service profile edit
   * (PATCH /auth/me) so the topbar/profile page reflect the new values. */
  refreshUser: () => Promise<void>
  /** All permission codes the user holds across every role/scope — or, when
   * `activeRole` is set, just that one role's own codes (see below). */
  permissions: string[]
  hasPermission: (permission: string) => boolean
  /** The role currently selected in the top-bar switcher, or null for "all
   * roles" (every permission the user holds, the default). Unlike a purely
   * presentational filter, setting this ACTUALLY restricts `hasPermission`
   * (and therefore `permissions` above) to that one role's own grants — a
   * real admin previewing what a lower-privileged role can do should not
   * still be able to reach admin-only actions through it. This is a
   * self-service UI preview, not a backend security boundary: the user
   * still holds every permission in the backend's eyes regardless of which
   * role is "active" here (see CurrentUserRead.role_permissions on the
   * backend). */
  activeRole: string | null
  setActiveRole: (role: string | null) => void
}

const AuthContext = React.createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = React.useState<AuthUser | null>(null)
  const [isLoading, setIsLoading] = React.useState(true)
  const [activeRole, setActiveRoleState] = React.useState<string | null>(() => {
    try {
      return localStorage.getItem(ACTIVE_ROLE_STORAGE_KEY)
    } catch {
      return null
    }
  })

  const setActiveRole = React.useCallback((role: string | null) => {
    setActiveRoleState(role)
    try {
      if (role) {
        localStorage.setItem(ACTIVE_ROLE_STORAGE_KEY, role)
      } else {
        localStorage.removeItem(ACTIVE_ROLE_STORAGE_KEY)
      }
    } catch {
      // localStorage unavailable (private browsing etc.) — in-memory state still works.
    }
  }, [])

  // If the stored role is no longer one the user holds (different account,
  // role revoked, etc.), drop it rather than restricting hasPermission()
  // against a role that no longer applies. Adjusted directly during render
  // rather than in an effect — this only fires once per invalidation since
  // activeRole becomes null immediately.
  if (activeRole && user && !user.roles.includes(activeRole)) {
    setActiveRoleState(null)
  }

  const fetchCurrentUser = React.useCallback(async () => {
    const res = await apiClient.get<AuthUser>('/auth/me')
    setUser(res.data)
    return res.data
  }, [])

  const logout = React.useCallback(() => {
    clearTokens()
    setUser(null)
  }, [])

  // On mount: if a refresh token is stashed from a previous session, try to
  // silently restore it before rendering protected routes.
  React.useEffect(() => {
    let cancelled = false

    async function bootstrap() {
      const refreshToken = getRefreshToken()
      if (!refreshToken) {
        setIsLoading(false)
        return
      }

      try {
        const res = await apiClient.post<{ access_token: string }>('/auth/refresh', {
          refresh_token: refreshToken,
        })
        if (cancelled) return
        setAccessToken(res.data.access_token)
        await fetchCurrentUser()
      } catch {
        clearTokens()
      } finally {
        if (!cancelled) setIsLoading(false)
      }
    }

    void bootstrap()
    return () => {
      cancelled = true
    }
  }, [fetchCurrentUser])

  // Wire the api-client's 401-after-failed-refresh handler to a full logout.
  React.useEffect(() => {
    registerUnauthorizedHandler(() => {
      clearTokens()
      setUser(null)
    })
  }, [])

  const login = React.useCallback(
    async (email: string, password: string) => {
      setIsLoading(true)
      try {
        const res = await apiClient.post<LoginResponse>('/auth/login', {
          email,
          password,
        })
        setAccessToken(res.data.access_token)
        setRefreshToken(res.data.refresh_token)
        await fetchCurrentUser()
      } catch (err) {
        clearTokens()
        if (err instanceof ApiError) throw err
        throw new ApiError('Unable to sign in. Please try again.')
      } finally {
        setIsLoading(false)
      }
    },
    [fetchCurrentUser],
  )

  const loginWithGoogle = React.useCallback(
    async (idToken: string) => {
      setIsLoading(true)
      try {
        const res = await apiClient.post<LoginResponse>('/auth/google', {
          id_token: idToken,
        })
        setAccessToken(res.data.access_token)
        setRefreshToken(res.data.refresh_token)
        await fetchCurrentUser()
      } catch (err) {
        clearTokens()
        if (err instanceof ApiError) throw err
        throw new ApiError('Unable to sign in with Google. Please try again.')
      } finally {
        setIsLoading(false)
      }
    },
    [fetchCurrentUser],
  )

  // When a role is "active", restrict to just that role's own grants
  // instead of the full union — see setActiveRole's docstring above.
  const permissions =
    activeRole && user ? (user.role_permissions[activeRole] ?? []) : (user?.permissions ?? [])

  const hasPermission = React.useCallback(
    (permission: string) => permissions.includes(permission),
    [permissions],
  )

  const refreshUser = React.useCallback(async () => {
    await fetchCurrentUser()
  }, [fetchCurrentUser])

  const value: AuthContextValue = {
    user,
    isLoading,
    isAuthenticated: user !== null,
    login,
    loginWithGoogle,
    logout,
    refreshUser,
    permissions,
    hasPermission,
    activeRole,
    setActiveRole,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuthContext(): AuthContextValue {
  const ctx = React.useContext(AuthContext)
  if (!ctx) {
    throw new Error('useAuthContext must be used within an AuthProvider')
  }
  return ctx
}
