import axios, { AxiosError, type AxiosRequestConfig } from 'axios'

/**
 * Base URL for the OBEvolve backend API. Configured per-environment via
 * VITE_API_BASE_URL; defaults to the local dev backend port documented in
 * docs/ARCHITECTURE.md.
 */
export const API_BASE_URL: string =
  import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1'

/**
 * Local-dev tenant slug, sent as the X-Institution-Slug header on every
 * request. In production the backend resolves the tenant from the
 * subdomain instead (see docs/ARCHITECTURE.md §2), so this header is a
 * local-dev-only convenience — see also VITE_INSTITUTION_SLUG in .env.
 */
export const INSTITUTION_SLUG: string | undefined = import.meta.env
  .VITE_INSTITUTION_SLUG as string | undefined

/** Shape of error responses returned by the FastAPI backend. */
export interface ApiErrorShape {
  detail: string
}

/** Normalized error thrown by the api client for callers to catch. */
export class ApiError extends Error {
  status: number | undefined
  detail: string

  constructor(detail: string, status?: number) {
    super(detail)
    this.name = 'ApiError'
    this.detail = detail
    this.status = status
  }
}

// ---------------------------------------------------------------------------
// Token storage
//
// Tradeoff (documented per spec): this is a pure SPA with no same-origin
// backend proxy, so we cannot rely on httpOnly cookies for refresh tokens
// without backend cookie support. Access tokens are kept in memory only
// (never persisted) to minimize XSS exfiltration risk; the refresh token is
// persisted to localStorage so a page reload doesn't force a re-login. This
// is a known, accepted tradeoff for Phase 1 — a compromised page can still
// read the refresh token from localStorage. Revisit if/when the backend
// exposes a same-origin cookie-based refresh endpoint.
// ---------------------------------------------------------------------------

const REFRESH_TOKEN_KEY = 'obevolve.refresh_token'

let accessToken: string | null = null

export function getAccessToken(): string | null {
  return accessToken
}

export function setAccessToken(token: string | null): void {
  accessToken = token
}

export function getRefreshToken(): string | null {
  return localStorage.getItem(REFRESH_TOKEN_KEY)
}

export function setRefreshToken(token: string | null): void {
  if (token) {
    localStorage.setItem(REFRESH_TOKEN_KEY, token)
  } else {
    localStorage.removeItem(REFRESH_TOKEN_KEY)
  }
}

export function clearTokens(): void {
  setAccessToken(null)
  setRefreshToken(null)
}

// ---------------------------------------------------------------------------
// Active program (X-Program-Code)
//
// Program-specific endpoints (program versions, PEOs/POs, CO-PO mappings,
// course offerings/sections/faculty/enrollments, assessments — see
// docs/adr/0003-schema-per-program.md) require an X-Program-Code header so
// the backend knows which program's schema to bind the request to. Set by
// lib/active-program-context.tsx once the signed-in user's program list is
// known (and auto-selected when there's exactly one); read here so every
// request picks it up the same way X-Institution-Slug already does, without
// threading a program code through every individual API call site.
// ---------------------------------------------------------------------------

let activeProgramCode: string | null = null

export function getActiveProgramCode(): string | null {
  return activeProgramCode
}

export function setActiveProgramCode(code: string | null): void {
  activeProgramCode = code
}

// ---------------------------------------------------------------------------
// Axios instance
// ---------------------------------------------------------------------------

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
})

apiClient.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.set('Authorization', `Bearer ${accessToken}`)
  }
  if (INSTITUTION_SLUG) {
    config.headers.set('X-Institution-Slug', INSTITUTION_SLUG)
  }
  if (activeProgramCode) {
    config.headers.set('X-Program-Code', activeProgramCode)
  }
  return config
})

/**
 * Called by auth-context to perform the actual token refresh request
 * without creating an import cycle (auth-context owns login/refresh/logout
 * semantics; this module only owns the HTTP plumbing and the 401 retry).
 */
let onUnauthorized: (() => void) | null = null
export function registerUnauthorizedHandler(handler: () => void): void {
  onUnauthorized = handler
}

let refreshPromise: Promise<string | null> | null = null

async function attemptRefresh(): Promise<string | null> {
  const refreshToken = getRefreshToken()
  if (!refreshToken) return null

  if (!refreshPromise) {
    refreshPromise = axios
      .post<{ access_token: string }>(
        `${API_BASE_URL}/auth/refresh`,
        { refresh_token: refreshToken },
        {
          headers: INSTITUTION_SLUG ? { 'X-Institution-Slug': INSTITUTION_SLUG } : {},
        },
      )
      .then((res) => {
        setAccessToken(res.data.access_token)
        return res.data.access_token
      })
      .catch(() => {
        clearTokens()
        return null
      })
      .finally(() => {
        refreshPromise = null
      })
  }

  return refreshPromise
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiErrorShape>) => {
    const originalRequest = error.config as
      | (AxiosRequestConfig & { _retried?: boolean })
      | undefined

    const status = error.response?.status

    if (status === 401 && originalRequest && !originalRequest._retried) {
      originalRequest._retried = true
      const newToken = await attemptRefresh()

      if (newToken) {
        originalRequest.headers = {
          ...originalRequest.headers,
          Authorization: `Bearer ${newToken}`,
        }
        return apiClient.request(originalRequest)
      }

      // Refresh failed: the session is no longer valid.
      onUnauthorized?.()
    }

    const detail =
      error.response?.data?.detail ?? error.message ?? 'An unexpected error occurred'
    return Promise.reject(new ApiError(detail, status))
  },
)
