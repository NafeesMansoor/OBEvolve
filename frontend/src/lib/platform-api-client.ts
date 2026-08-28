import axios, { AxiosError, type AxiosRequestConfig } from 'axios'

import { API_BASE_URL, type ApiErrorShape, ApiError } from '@/lib/api-client'

/**
 * A separate axios instance for the platform-admin surface
 * (/platform-auth, /institutions) — deliberately not sharing state with
 * lib/api-client.ts's tenant-scoped client. Platform-admin tokens carry no
 * institution_slug and authenticate against `public.platform_admins`, a
 * different principal entirely from a tenant `User`; mixing their token
 * storage would let one silently clobber the other if both were ever open
 * in the same browser tab (e.g. a platform admin also has a personal
 * faculty login at some institution).
 */

const REFRESH_TOKEN_KEY = 'obevolve.platform_refresh_token'

let accessToken: string | null = null

export function getPlatformAccessToken(): string | null {
  return accessToken
}

export function setPlatformAccessToken(token: string | null): void {
  accessToken = token
}

export function getPlatformRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY)
}

export function setPlatformRefreshToken(token: string | null): void {
  if (token) {
    localStorage.setItem(REFRESH_TOKEN_KEY, token)
  } else {
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  }
}

export function clearPlatformTokens(): void {
  setPlatformAccessToken(null)
  setPlatformRefreshToken(null)
}

export const platformApiClient = axios.create({
  baseURL: API_BASE_URL,
})

platformApiClient.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.set('Authorization', `Bearer ${accessToken}`)
  }
  return config
})

let onUnauthorized: (() => void) | null = null
export function registerPlatformUnauthorizedHandler(handler: () => void): void {
  onUnauthorized = handler
}

let refreshPromise: Promise<string | null> | null = null

async function attemptPlatformRefresh(): Promise<string | null> {
  const refreshToken = getPlatformRefreshToken()
  if (!refreshToken) return null

  if (!refreshPromise) {
    refreshPromise = axios
      .post<{ access_token: string }>(`${API_BASE_URL}/platform-auth/refresh`, {
        refresh_token: refreshToken,
      })
      .then((res) => {
        setPlatformAccessToken(res.data.access_token)
        return res.data.access_token
      })
      .catch(() => {
        clearPlatformTokens()
        return null
      })
      .finally(() => {
        refreshPromise = null
      })
  }

  return refreshPromise
}

platformApiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiErrorShape>) => {
    const originalRequest = error.config as
      | (AxiosRequestConfig & { _retried?: boolean })
      | undefined

    const status = error.response?.status

    if (status === 401 && originalRequest && !originalRequest._retried) {
      originalRequest._retried = true
      const newToken = await attemptPlatformRefresh()

      if (newToken) {
        originalRequest.headers = {
          ...originalRequest.headers,
          Authorization: `Bearer ${newToken}`,
        }
        return platformApiClient.request(originalRequest)
      }

      onUnauthorized?.()
    }

    const detail =
      error.response?.data?.detail ?? error.message ?? 'An unexpected error occurred'
    return Promise.reject(new ApiError(detail, status))
  },
)
