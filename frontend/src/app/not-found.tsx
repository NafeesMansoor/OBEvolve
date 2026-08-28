import { Link } from 'react-router-dom'

import { Footer } from '@/components/footer'
import { Button } from '@/components/ui/button'

export function NotFoundPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <div className="flex flex-1 flex-col items-center justify-center gap-4 px-4 text-center">
        <p className="font-display text-sm font-semibold text-primary">404</p>
        <h1 className="font-display text-2xl font-semibold tracking-tight">Page not found</h1>
        <p className="max-w-sm text-sm text-muted-foreground">
          The page you're looking for doesn't exist or hasn't been built yet.
        </p>
        <Button asChild>
          <Link to="/">Back to dashboard</Link>
        </Button>
      </div>

      <Footer />
    </div>
  )
}
