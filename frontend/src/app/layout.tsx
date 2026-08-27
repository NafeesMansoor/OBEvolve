import * as React from 'react'
import {
  BarChart3,
  BookOpen,
  ClipboardCheck,
  Database,
  LayoutDashboard,
  LogOut,
  ShieldCheck,
  User as UserIcon,
} from 'lucide-react'
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom'

import { useAuth } from '@/features/auth/useAuth'
import {
  NAV_SECTION_ROLES,
  sectionMatchesRole,
  useActiveRole,
} from '@/lib/active-role-context'
import { cn } from '@/lib/utils'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Footer } from '@/components/footer'
import { RoleSwitcher } from '@/components/role-switcher'
import { Separator } from '@/components/ui/separator'

interface NavItem {
  label: string
  to: string
  icon: React.ComponentType<{ className?: string }>
  /** Key into NAV_SECTION_ROLES for the active-role filter, and into
   * hasPermission checks below. */
  sectionKey: keyof typeof NAV_SECTION_ROLES
  /** Shown if the user holds ANY of these permissions. */
  anyOfPermissions: string[]
}

const navItems: NavItem[] = [
  {
    label: 'Dashboard',
    to: '/',
    icon: LayoutDashboard,
    sectionKey: 'dashboard',
    anyOfPermissions: [],
  },
  {
    label: 'Curriculum & Outcomes',
    to: '/curriculum',
    icon: BookOpen,
    sectionKey: 'curriculum',
    anyOfPermissions: ['curriculum.view'],
  },
  {
    label: 'Academic Operations',
    to: '/academic',
    icon: ClipboardCheck,
    sectionKey: 'academic',
    anyOfPermissions: [
      'section.view',
      'section.manage',
      'student.view',
      'student.manage',
    ],
  },
  {
    label: 'Grading',
    to: '/grading',
    icon: BarChart3,
    sectionKey: 'grading',
    anyOfPermissions: ['grading.view'],
  },
  {
    label: 'Assessment',
    to: '/assessment',
    icon: ClipboardCheck,
    sectionKey: 'assessment',
    anyOfPermissions: ['assessment.view'],
  },
  {
    label: 'Organization Admin',
    to: '/organization',
    icon: ShieldCheck,
    sectionKey: 'organization',
    anyOfPermissions: ['org.view', 'program.view', 'user.view', 'academic_calendar.view'],
  },
  {
    label: 'Raw Data Console',
    to: '/raw-data',
    icon: Database,
    sectionKey: 'rawData',
    anyOfPermissions: [
      'raw_data.manage_all',
      'raw_data.manage_institution',
      'raw_data.manage_scoped',
      'raw_data.propose_scoped',
    ],
  },
]

function initials(fullName: string): string {
  const parts = fullName.trim().split(/\s+/)
  const first = parts[0]?.[0] ?? ''
  const last = parts.length > 1 ? (parts[parts.length - 1]?.[0] ?? '') : ''
  return (first + last).toUpperCase() || 'U'
}

export function AppLayout() {
  const { user, hasPermission, logout } = useAuth()
  const { activeRole } = useActiveRole()
  const navigate = useNavigate()
  const location = useLocation()

  function handleLogout() {
    logout()
    navigate('/login', { replace: true })
  }

  const visibleItems = navItems.filter(
    (item) =>
      item.anyOfPermissions.length === 0 ||
      item.anyOfPermissions.some((p) => hasPermission(p)),
  )
  // Active-role filtering only de-emphasizes — every permitted item stays
  // visible, but items irrelevant to the selected role are dimmed rather
  // than hidden, so nothing the user can access disappears outright.
  const isDeemphasized = (item: NavItem) =>
    activeRole !== null && !sectionMatchesRole(item.sectionKey, activeRole)

  return (
    <div className="flex min-h-screen bg-background">
      <aside className="hidden w-64 shrink-0 border-r bg-card md:flex md:flex-col">
        <div className="flex h-16 items-center gap-2 border-b px-6">
          <div className="flex size-8 items-center justify-center rounded-md bg-primary text-sm font-semibold text-primary-foreground">
            OB
          </div>
          <span className="text-sm font-semibold tracking-tight">OBEvolve</span>
        </div>

        <nav className="flex-1 space-y-1 overflow-y-auto px-3 py-4">
          {visibleItems.map((item) => {
            const isActive = location.pathname === item.to
            const deemphasized = isDeemphasized(item)

            return (
              <Link
                key={item.to}
                to={item.to}
                className={cn(
                  'flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary/10 text-primary'
                    : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground',
                  deemphasized && !isActive && 'opacity-50',
                )}
              >
                <item.icon className="size-4 shrink-0" />
                <span className="flex-1 truncate text-left">{item.label}</span>
              </Link>
            )
          })}
        </nav>

        <div className="border-t p-3">
          <p className="px-3 py-2 text-xs text-muted-foreground">
            {user?.full_name} · {user?.roles.length ?? 0} role
            {(user?.roles.length ?? 0) === 1 ? '' : 's'}
          </p>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 shrink-0 items-center justify-between border-b bg-card px-4 md:px-6">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span className="font-medium text-foreground">
              {navItems.find((i) => i.to === location.pathname)?.label ?? 'OBEvolve'}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <RoleSwitcher />

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" className="flex items-center gap-2 px-2">
                  <Avatar className="size-8">
                    <AvatarFallback>{initials(user?.full_name ?? 'U')}</AvatarFallback>
                  </Avatar>
                  <span className="hidden text-sm font-medium sm:inline">
                    {user?.full_name}
                  </span>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel className="flex flex-col gap-0.5">
                  <span className="flex items-center gap-1.5 font-medium">
                    <UserIcon className="size-3.5" /> {user?.full_name}
                  </span>
                  <span className="text-xs font-normal text-muted-foreground">
                    {user?.email}
                  </span>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => navigate('/profile')}>
                  <UserIcon className="size-4" />
                  Your profile
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem
                  onClick={handleLogout}
                  className="text-destructive focus:text-destructive"
                >
                  <LogOut className="size-4" />
                  Log out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </header>

        <Separator className="md:hidden" />

        <main className="flex-1 overflow-y-auto p-4 md:p-8">
          <Outlet />
        </main>

        <Footer />
      </div>
    </div>
  )
}
