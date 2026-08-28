import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ThemeProvider } from 'next-themes'
import { BrowserRouter } from 'react-router-dom'

import { AppRoutes } from '@/app/routes'
import { Toaster } from '@/components/ui/sonner'
import { ActiveProgramProvider } from '@/lib/active-program-context'
import { AuthProvider } from '@/lib/auth-context'
import { PlatformAuthProvider } from '@/lib/platform-auth-context'

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
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <AuthProvider>
            <PlatformAuthProvider>
              <ActiveProgramProvider>
                <AppRoutes />
                <Toaster richColors closeButton position="top-right" />
              </ActiveProgramProvider>
            </PlatformAuthProvider>
          </AuthProvider>
        </BrowserRouter>
      </QueryClientProvider>
    </ThemeProvider>
  )
}
