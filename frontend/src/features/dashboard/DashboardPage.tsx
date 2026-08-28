import {
  AlertTriangle,
  BarChart3,
  BookOpen,
  ClipboardCheck,
  GraduationCap,
  LineChart,
  ShieldCheck,
  Target,
  Users,
} from 'lucide-react'
import { Link } from 'react-router-dom'

import { useAuth } from '@/features/auth/useAuth'
import { MyAttainmentPanel } from '@/features/dashboard/MyAttainmentPanel'
import type { Student } from '@/features/academic-ops/types'
import type { PendingAssessmentDocument } from '@/features/assessment/types'
import type { Course } from '@/features/curriculum/types'
import type { Program } from '@/features/organization/types'
import { useActiveProgram } from '@/lib/active-program-context'
import { useEntityList } from '@/lib/crud-hooks'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { Skeleton } from '@/components/ui/skeleton'

const QUICK_LINKS = [
  { to: '/course-settings', label: 'Course Level Settings', icon: BookOpen, permission: 'curriculum.view' },
  { to: '/program-settings', label: 'Program Level Setting', icon: Target, permission: 'program.view' },
  { to: '/academic', label: 'Academic Operations', icon: ClipboardCheck, permission: 'section.view' },
  { to: '/grading', label: 'Grading', icon: BarChart3, permission: 'grading.view' },
  { to: '/assessment', label: 'Assessment', icon: ClipboardCheck, permission: 'assessment.view' },
  { to: '/analytics', label: 'Analytics', icon: LineChart, permission: 'program.view' },
  { to: '/organization', label: 'Organization Admin', icon: ShieldCheck, permission: 'org.view' },
]

/**
 * Students get their own attainment view (spec §14, MyAttainmentPanel)
 * right on the dashboard, since it's the one thing a student-only account
 * actually wants to see day to day. Program/course-level dashboards for
 * admin/coordinator/faculty roles live under Analytics ("Program Analytics",
 * "PO Attainment", "Course Attainment") instead — this page stays a
 * lightweight landing page for those roles.
 */
function greeting(): string {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good morning'
  if (hour < 17) return 'Good afternoon'
  return 'Good evening'
}

export function DashboardPage() {
  const { user, hasPermission } = useAuth()
  const isStudent = Boolean(user?.roles.includes('Student'))

  const links = QUICK_LINKS.filter((l) => hasPermission(l.permission))

  return (
    <div className="mx-auto flex max-w-4xl flex-col gap-8">
      <div className="flex flex-col gap-2">
        <p className="text-sm font-medium text-primary">{greeting()}</p>
        <h1 className="text-3xl font-semibold tracking-tight">
          {user?.full_name ?? 'Welcome'}
        </h1>
        <p className="text-muted-foreground">
          {user?.roles.length
            ? `Signed in as ${user.roles.join(' · ')}.`
            : "Here's your OBEvolve overview."}
        </p>
      </div>

      {isStudent && <MyAttainmentPanel />}

      {!isStudent && <PendingDocumentsCard />}

      {!isStudent && <OverviewStats />}

      {links.length > 0 && (
        <div className="flex flex-col gap-3">
          <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
            Jump to
          </h2>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {links.map((l) => (
              <Link
                key={l.to}
                to={l.to}
                className="block rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
              >
                <Card className="cursor-pointer transition-all hover:-translate-y-0.5 hover:border-primary/50 hover:shadow-md">
                  <CardContent className="flex items-center gap-3 py-5">
                    <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                      <l.icon className="size-4" />
                    </div>
                    <span className="font-medium">{l.label}</span>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
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

interface StatDef {
  label: string
  icon: typeof BookOpen
  permission: string
  to: string
}

const STAT_DEFS: StatDef[] = [
  { label: 'Programs', icon: Target, permission: 'program.view', to: '/organization' },
  { label: 'Courses', icon: BookOpen, permission: 'curriculum.view', to: '/course-settings' },
  { label: 'Students', icon: GraduationCap, permission: 'student.view', to: '/academic' },
  { label: 'Faculty & staff', icon: Users, permission: 'user.view', to: '/organization' },
]

/** A glanceable summary row above the quick-links grid — replaces the
 * previous bare greeting, which had nothing for an admin/coordinator to
 * actually look at before diving into a sub-page. Each metric fetches only
 * if the viewer holds the permission its source list requires, so this
 * never trips a 403 for a narrowly-scoped role. */
function OverviewStats() {
  const { hasPermission } = useAuth()

  const { data: programs, isLoading: programsLoading } = useEntityList<Program>(
    ['org', 'programs'],
    '/org/programs',
    undefined,
    { enabled: hasPermission('program.view') },
  )
  const { data: courses, isLoading: coursesLoading } = useEntityList<Course>(
    ['curriculum', 'courses'],
    '/curriculum/courses',
    undefined,
    { enabled: hasPermission('curriculum.view') },
  )
  const { data: students, isLoading: studentsLoading } = useEntityList<Student>(
    ['academic', 'students'],
    '/academic/students',
    undefined,
    { enabled: hasPermission('student.view') },
  )
  const { data: users, isLoading: usersLoading } = useEntityList<{ id: string }>(
    ['users'],
    '/users',
    undefined,
    { enabled: hasPermission('user.view') },
  )

  const values: Record<string, { count: number | undefined; loading: boolean }> = {
    'program.view': { count: programs?.length, loading: programsLoading },
    'curriculum.view': { count: courses?.length, loading: coursesLoading },
    'student.view': { count: students?.length, loading: studentsLoading },
    'user.view': { count: users?.length, loading: usersLoading },
  }

  const visible = STAT_DEFS.filter((s) => hasPermission(s.permission))
  if (visible.length === 0) return null

  return (
    <div className="flex flex-col gap-3">
      <h2 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
        Overview
      </h2>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {visible.map((s) => {
          const v = values[s.permission]
          return (
            <Link
              key={s.label}
              to={s.to}
              aria-label={`View ${s.label.toLowerCase()}`}
              className="block rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            >
              <Card className="cursor-pointer transition-all hover:-translate-y-0.5 hover:border-primary/50 hover:shadow-md">
                <CardContent className="flex items-center gap-3 py-5">
                  <div className="flex size-10 shrink-0 items-center justify-center rounded-full bg-primary/10 text-primary">
                    <s.icon className="size-5" />
                  </div>
                  <div className="flex flex-col gap-0.5">
                    {v.loading ? (
                      <Skeleton className="h-7 w-10" />
                    ) : (
                      <span className="font-display text-2xl font-semibold leading-none tabular-nums">
                        {v.count ?? '—'}
                      </span>
                    )}
                    <span className="text-xs text-muted-foreground">{s.label}</span>
                  </div>
                </CardContent>
              </Card>
            </Link>
          )
        })}
      </div>
    </div>
  )
}

/** Course Coordinators / Program Administrators (assessment.approve) get a
 * heads-up right on the dashboard when there's a document review queue —
 * the fuller list with Approve/Reject lives at Assessment > Pending
 * documents; this is just the "you have something to do" nudge. */
function PendingDocumentsCard() {
  const { hasPermission } = useAuth()
  const canReview = hasPermission('assessment.approve')
  // Program-scoped endpoint — must wait for ActiveProgramProvider to finish
  // auto-selecting a program (it starts null on a fresh login), or this 400s
  // before the X-Program-Code header is ever set. See
  // lib/active-program-context.tsx's activeProgramCode doc comment.
  const { activeProgramCode } = useActiveProgram()
  const { data: pending, isLoading } = useEntityList<PendingAssessmentDocument>(
    ['assessment', 'documents', 'pending'],
    '/assessment/documents/pending',
    undefined,
    { enabled: canReview && Boolean(activeProgramCode) },
  )

  if (!canReview || isLoading) return null
  if (!pending || pending.length === 0) return null

  return (
    <Link to="/assessment" className="block rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2">
      <Card className="cursor-pointer border-warning/30 bg-warning/5 transition-colors hover:border-warning/50">
        <CardContent className="flex items-center gap-3 py-4">
          <div className="flex size-9 shrink-0 items-center justify-center rounded-full bg-warning/15 text-warning">
            <AlertTriangle className="size-4" />
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-medium">
              {pending.length} assessment document{pending.length === 1 ? '' : 's'} awaiting your review
            </span>
            <span className="text-xs text-muted-foreground">
              Question papers, moderation/compliance forms, scripts, and CEP documents — see Assessment →
              Pending documents.
            </span>
          </div>
        </CardContent>
      </Card>
    </Link>
  )
}
