import { BrowserRouter } from 'react-router-dom'

import { AppRoutes } from '@/app/routes'
import { AuthProvider } from '@/lib/auth-context'

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  )
}
