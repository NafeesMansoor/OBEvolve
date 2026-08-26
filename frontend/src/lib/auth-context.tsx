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
}

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
  logout: () => void
  /** Re-fetches /auth/me — call after a self-service profile edit
   * (PATCH /auth/me) so the topbar/profile page reflect the new values. */
  refreshUser: () => Promise<void>
  /** All permission codes the user holds across every role/scope. */
  permissions: string[]
  hasPermission: (permission: string) => boolean
}

const AuthContext = React.createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = React.useState<AuthUser | null>(null)
  const [isLoading, setIsLoading] = React.useState(true)

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

  const permissions = user?.permissions ?? []

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
    logout,
    refreshUser,
    permissions,
    hasPermission,
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
