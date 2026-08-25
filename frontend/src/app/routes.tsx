import { Navigate, Route, Routes } from 'react-router-dom'

import { AppLayout } from '@/app/layout'
import { NotFoundPage } from '@/app/not-found'
import { ProtectedRoute } from '@/app/protected-route'
import { LoginPage } from '@/features/auth/LoginPage'
import { DashboardPage } from '@/features/dashboard/DashboardPage'
import { useAuth } from '@/features/auth/useAuth'

function LoginRoute() {
  const { isAuthenticated, isLoading } = useAuth()

  if (!isLoading && isAuthenticated) {
    return <Navigate to="/" replace />
  }

  return <LoginPage />
}

/**
 * Top-level route table. Phase 1 only wires /login and the dashboard;
 * future phases add nested routes under the protected layout for
 * curriculum, outcomes, assessments, attainment, surveys, and accreditation
 * (their sidebar entries already exist in app/layout.tsx, disabled until
 * then).
 */
export function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginRoute />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/" element={<DashboardPage />} />
        </Route>
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
