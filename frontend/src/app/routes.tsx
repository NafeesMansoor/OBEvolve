import { Navigate, Route, Routes } from 'react-router-dom'

import { AppLayout } from '@/app/layout'
import { NotFoundPage } from '@/app/not-found'
import { PlatformProtectedRoute } from '@/app/platform-protected-route'
import { ProtectedRoute } from '@/app/protected-route'
import { ForgotPasswordPage } from '@/features/auth/ForgotPasswordPage'
import { LoginPage } from '@/features/auth/LoginPage'
import { ResetPasswordPage } from '@/features/auth/ResetPasswordPage'
import { useAuth } from '@/features/auth/useAuth'
import { AcademicOpsPage } from '@/features/academic-ops/AcademicOpsPage'
import { AboutPage } from '@/features/about/AboutPage'
import { AnalyticsPage } from '@/features/analytics/AnalyticsPage'
import { AssessmentPage } from '@/features/assessment/AssessmentPage'
import { CourseManagementPage } from '@/features/course-management/CourseManagementPage'
import { MyCoursesPage } from '@/features/course-management/MyCoursesPage'
import { CourseSettingsPage } from '@/features/curriculum/CourseSettingsPage'
import { ProgramSettingsPage } from '@/features/curriculum/ProgramSettingsPage'
import { DashboardPage } from '@/features/dashboard/DashboardPage'
import { GradingPage } from '@/features/grading/GradingPage'
import { InstituteSettingsPage } from '@/features/organization/InstituteSettingsPage'
import { PlatformDashboardPage } from '@/features/platform/PlatformDashboardPage'
import { PlatformLoginPage } from '@/features/platform/PlatformLoginPage'
import { PlatformRawDataPage } from '@/features/platform/PlatformRawDataPage'
import { ProfilePage } from '@/features/profile/ProfilePage'
import { QuestionBankPage } from '@/features/question-bank/QuestionBankPage'
import { PendingChangesPage } from '@/features/raw-data/PendingChangesPage'
import { RawDataConsolePage } from '@/features/raw-data/RawDataConsolePage'

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
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />

      <Route path="/platform-login" element={<PlatformLoginPage />} />
      <Route element={<PlatformProtectedRoute />}>
        <Route path="/platform" element={<PlatformDashboardPage />} />
        <Route path="/platform/raw-data" element={<PlatformRawDataPage />} />
      </Route>

      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/courses" element={<MyCoursesPage />} />
          <Route path="/courses/:sectionId" element={<CourseManagementPage />} />
          <Route path="/question-bank" element={<QuestionBankPage />} />
          <Route path="/course-settings" element={<CourseSettingsPage />} />
          <Route path="/program-settings" element={<ProgramSettingsPage />} />
          <Route path="/academic" element={<AcademicOpsPage />} />
          <Route path="/grading" element={<GradingPage />} />
          <Route path="/assessment" element={<AssessmentPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/organization" element={<InstituteSettingsPage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="/raw-data" element={<RawDataConsolePage />} />
          <Route path="/raw-data/pending-changes" element={<PendingChangesPage />} />
        </Route>
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
