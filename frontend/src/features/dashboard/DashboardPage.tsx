import { LayoutDashboard, ShieldCheck } from 'lucide-react'

import { useAuth } from '@/features/auth/useAuth'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'

/**
 * Phase 1 placeholder dashboard. The product spec defines role-based
 * dashboards (institution / HOD / faculty / accreditation view) that surface
 * live attainment, curriculum, and survey data — none of that exists yet, so
 * this renders an honest empty state plus a summary of the signed-in user's
 * roles and permissions rather than any fabricated content.
 */
export function DashboardPage() {
  const { user } = useAuth()

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-8">
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold tracking-tight">
          Welcome{user?.full_name ? `, ${user.full_name}` : ''}
        </h1>
        <p className="text-muted-foreground">
          This is your OBEvolve dashboard. Role-specific views (institution,
          department, faculty, and accreditation dashboards) ship in later
          phases as the curriculum, outcomes, assessment, and attainment
          modules come online.
        </p>
      </div>

      <Card className="border-dashed">
        <CardContent className="flex flex-col items-center gap-3 py-16 text-center">
          <div className="flex size-12 items-center justify-center rounded-full bg-muted">
            <LayoutDashboard className="size-6 text-muted-foreground" />
          </div>
          <div className="space-y-1">
            <p className="font-medium">Nothing to show yet</p>
            <p className="max-w-sm text-sm text-muted-foreground">
              Phase 1 covers authentication, roles, and the application shell
              only. Curriculum design, outcome mapping, assessments,
              attainment, surveys, and accreditation reporting land in
              subsequent phases — see{' '}
              <code className="rounded bg-muted px-1 py-0.5 text-xs">
                docs/DATABASE_PLAN.md
              </code>{' '}
              for the full roadmap.
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <ShieldCheck className="size-4" />
            Your access
          </CardTitle>
          <CardDescription>
            Roles and permissions returned by <code>GET /auth/me</code> for
            your account. Permission resolution (including any per-department
            or per-program scoping) happens server-side — see
            <code className="mx-1 rounded bg-muted px-1 py-0.5 text-xs">
              app/services/rbac.py
            </code>
            — so this is already the flat, effective set for your account.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {user && user.roles.length > 0 ? (
            <div className="flex flex-col gap-4">
              <div>
                <p className="mb-2 text-sm font-medium">Roles</p>
                <div className="flex flex-wrap gap-1.5">
                  {user.roles.map((role) => (
                    <Badge key={role} variant="secondary" className="font-normal">
                      {role}
                    </Badge>
                  ))}
                </div>
              </div>
              <Separator />
              <div>
                <p className="mb-2 text-sm font-medium">Permissions</p>
                {user.permissions.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5">
                    {user.permissions.map((permission) => (
                      <Badge
                        key={permission}
                        variant="outline"
                        className="font-mono text-[11px] font-normal"
                      >
                        {permission}
                      </Badge>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">No permissions granted.</p>
                )}
              </div>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">
              No roles are assigned to your account yet. Contact your
              institution administrator.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
