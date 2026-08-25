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

export interface Role {
  name: string
  permissions: string[]
  scope_type: string
  scope_id: string | null
}

export interface AuthUser {
  id: string
  email: string
  full_name: string
  roles: Role[]
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

  const permissions = React.useMemo(
    () =>
      user
        ? Array.from(new Set(user.roles.flatMap((role) => role.permissions)))
        : [],
    [user],
  )

  const hasPermission = React.useCallback(
    (permission: string) => permissions.includes(permission),
    [permissions],
  )

  const value: AuthContextValue = {
    user,
    isLoading,
    isAuthenticated: user !== null,
    login,
    logout,
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
