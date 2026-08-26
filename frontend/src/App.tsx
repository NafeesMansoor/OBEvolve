import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'

import { AppRoutes } from '@/app/routes'
import { Toaster } from '@/components/ui/sonner'
import { ActiveRoleProvider } from '@/lib/active-role-context'
import { AuthProvider } from '@/lib/auth-context'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <ActiveRoleProvider>
            <AppRoutes />
            <Toaster richColors closeButton position="top-right" />
          </ActiveRoleProvider>
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
