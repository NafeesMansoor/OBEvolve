import { Navigate, Outlet, useLocation } from 'react-router-dom'

import { usePlatformAuth } from '@/lib/platform-auth-context'

/** Gate for the platform-admin surface (/platform/*) — mirrors
 * app/protected-route.tsx but checks the separate platform-admin session
 * (lib/platform-auth-context.tsx), not a tenant user's. */
export function PlatformProtectedRoute() {
  const { isAuthenticated, isLoading } = usePlatformAuth()
  const location = useLocation()

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="flex flex-col items-center gap-3 text-muted-foreground">
          <div className="size-6 animate-spin rounded-full border-2 border-current border-t-transparent" />
          <p className="text-sm">Loading session…</p>
        </div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/platform-login" replace state={{ from: location.pathname }} />
  }

  return <Outlet />
}
