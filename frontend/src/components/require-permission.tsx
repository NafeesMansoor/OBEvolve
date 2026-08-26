import { ShieldAlert } from 'lucide-react'

import { useAuth } from '@/features/auth/useAuth'
import { Card, CardContent } from '@/components/ui/card'

interface RequirePermissionProps {
  /** Permission code(s) — page renders if the user holds at least one. */
  anyOf: string[]
  children: React.ReactNode
}

/** Gates an entire page on a permission. Used at the top of every
 * feature page per-module (org.view, curriculum.view, section.view, ...). */
export function RequirePermission({ anyOf, children }: RequirePermissionProps) {
  const { hasPermission } = useAuth()
  const allowed = anyOf.some((code) => hasPermission(code))

  if (!allowed) {
    return (
      <Card className="border-dashed">
        <CardContent className="flex flex-col items-center gap-3 py-16 text-center">
          <div className="flex size-12 items-center justify-center rounded-full bg-muted">
            <ShieldAlert className="size-6 text-muted-foreground" />
          </div>
          <div className="space-y-1">
            <p className="font-medium">You don&apos;t have access to this section</p>
            <p className="max-w-sm text-sm text-muted-foreground">
              Contact your institution administrator if you believe this is a mistake.
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return <>{children}</>
}
