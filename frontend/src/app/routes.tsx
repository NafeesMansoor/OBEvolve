import { Navigate, Route, Routes } from 'react-router-dom'

import { AppLayout } from '@/app/layout'
import { NotFoundPage } from '@/app/not-found'
import { ProtectedRoute } from '@/app/protected-route'
import { LoginPage } from '@/features/auth/LoginPage'
import { useAuth } from '@/features/auth/useAuth'
import { AcademicOpsPage } from '@/features/academic-ops/AcademicOpsPage'
import { AssessmentPage } from '@/features/assessment/AssessmentPage'
import { CurriculumPage } from '@/features/curriculum/CurriculumPage'
import { DashboardPage } from '@/features/dashboard/DashboardPage'
import { GradingPage } from '@/features/grading/GradingPage'
import { OrganizationPage } from '@/features/organization/OrganizationPage'
import { ProfilePage } from '@/features/profile/ProfilePage'

function LoginRoute() {
  const { isAuthenticated, isLoading } = useAuth()

  if (!isLoading && isAuthenticated) {
    return <Navigate to="/" replace />
  }

  return <LoginPage />
}

/** Top-level route table. Every module below the dashboard now has a real
 * page (see app/layout.tsx's navItems for the gating permissions). */
export function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginRoute />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/curriculum" element={<CurriculumPage />} />
          <Route path="/academic" element={<AcademicOpsPage />} />
          <Route path="/grading" element={<GradingPage />} />
          <Route path="/assessment" element={<AssessmentPage />} />
          <Route path="/organization" element={<OrganizationPage />} />
        </Route>
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
