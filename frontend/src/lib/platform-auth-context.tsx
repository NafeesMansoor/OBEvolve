import * as React from 'react'

import { ApiError } from '@/lib/api-client'
import {
  clearPlatformTokens,
  getPlatformRefreshToken,
  platformApiClient,
  registerPlatformUnauthorizedHandler,
  setPlatformAccessToken,
  setPlatformRefreshToken,
} from '@/lib/platform-api-client'

export interface PlatformAdminUser {
  id: string
  email: string
  full_name: string
  is_active: boolean
}

interface PlatformLoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

interface PlatformAuthContextValue {
  admin: PlatformAdminUser | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => void
}

const PlatformAuthContext = React.createContext<PlatformAuthContextValue | undefined>(undefined)

export function PlatformAuthProvider({ children }: { children: React.ReactNode }) {
  const [admin, setAdmin] = React.useState<PlatformAdminUser | null>(null)
  const [isLoading, setIsLoading] = React.useState(true)

  const fetchCurrentAdmin = React.useCallback(async () => {
    const res = await platformApiClient.get<PlatformAdminUser>('/platform-auth/me')
    setAdmin(res.data)
    return res.data
  }, [])

  const logout = React.useCallback(() => {
    clearPlatformTokens()
    setAdmin(null)
  }, [])

  // On mount: silently restore a session from a stashed refresh token, same
  // pattern as lib/auth-context.tsx's tenant-user bootstrap.
  React.useEffect(() => {
    let cancelled = false

    async function bootstrap() {
      const refreshToken = getPlatformRefreshToken()
      if (!refreshToken) {
        setIsLoading(false)
        return
      }

      try {
        const res = await platformApiClient.post<{ access_token: string }>(
          '/platform-auth/refresh',
          { refresh_token: refreshToken },
        )
        if (cancelled) return
        setPlatformAccessToken(res.data.access_token)
        await fetchCurrentAdmin()
      } catch {
        clearPlatformTokens()
      } finally {
        if (!cancelled) setIsLoading(false)
      }
    }

    void bootstrap()
    return () => {
      cancelled = true
    }
  }, [fetchCurrentAdmin])

  React.useEffect(() => {
    registerPlatformUnauthorizedHandler(() => {
      clearPlatformTokens()
      setAdmin(null)
    })
  }, [])

  const login = React.useCallback(
    async (email: string, password: string) => {
      setIsLoading(true)
      try {
        const res = await platformApiClient.post<PlatformLoginResponse>('/platform-auth/login', {
          email,
          password,
        })
        setPlatformAccessToken(res.data.access_token)
        setPlatformRefreshToken(res.data.refresh_token)
        await fetchCurrentAdmin()
      } catch (err) {
        clearPlatformTokens()
        if (err instanceof ApiError) throw err
        throw new ApiError('Unable to sign in. Please try again.')
      } finally {
        setIsLoading(false)
      }
    },
    [fetchCurrentAdmin],
  )

  const value: PlatformAuthContextValue = {
    admin,
    isLoading,
    isAuthenticated: admin !== null,
    login,
    logout,
  }

  return <PlatformAuthContext.Provider value={value}>{children}</PlatformAuthContext.Provider>
}

export function usePlatformAuth(): PlatformAuthContextValue {
  const ctx = React.useContext(PlatformAuthContext)
  if (!ctx) {
    throw new Error('usePlatformAuth must be used within a PlatformAuthProvider')
  }
  return ctx
}
