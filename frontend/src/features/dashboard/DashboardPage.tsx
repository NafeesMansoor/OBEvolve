import { BarChart3, BookOpen, ClipboardCheck, ShieldCheck } from 'lucide-react'
import { Link } from 'react-router-dom'

import { useAuth } from '@/features/auth/useAuth'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'

const QUICK_LINKS = [
  { to: '/curriculum', label: 'Curriculum & Outcomes', icon: BookOpen, permission: 'curriculum.view' },
  { to: '/academic', label: 'Academic Operations', icon: ClipboardCheck, permission: 'section.view' },
  { to: '/grading', label: 'Grading', icon: BarChart3, permission: 'grading.view' },
  { to: '/assessment', label: 'Assessment', icon: ClipboardCheck, permission: 'assessment.view' },
  { to: '/organization', label: 'Organization Admin', icon: ShieldCheck, permission: 'org.view' },
]

/**
 * A role-specific attainment/curriculum dashboard (per the product spec) is
 * still future work — this renders a summary of the signed-in user's
 * roles/permissions plus quick links into whichever modules they can
 * access, rather than any fabricated attainment data.
 */
export function DashboardPage() {
  const { user, hasPermission } = useAuth()

  const links = QUICK_LINKS.filter((l) => hasPermission(l.permission))

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-8">
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold tracking-tight">
          Welcome{user?.full_name ? `, ${user.full_name}` : ''}
        </h1>
        <p className="text-muted-foreground">
          This is your OBEvolve dashboard. Attainment and reporting views are still future work —
          use the sections below or the sidebar to manage curriculum, academic operations,
          grading, assessment, and organization data.
        </p>
      </div>

      {links.length > 0 && (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
          {links.map((l) => (
            <Link key={l.to} to={l.to}>
              <Card className="transition-colors hover:border-primary/50 hover:bg-accent/50">
                <CardContent className="flex items-center gap-3 py-5">
                  <div className="flex size-9 items-center justify-center rounded-full bg-primary/10 text-primary">
                    <l.icon className="size-4" />
                  </div>
                  <span className="font-medium">{l.label}</span>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}

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
