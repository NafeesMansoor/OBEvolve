import * as React from 'react'
import {
  BarChart3,
  BookOpen,
  ClipboardCheck,
  Database,
  Info,
  LayoutDashboard,
  LineChart,
  LogOut,
  Menu,
  ShieldCheck,
  Target,
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
import { Logo } from '@/components/logo'
import { ProgramSwitcher } from '@/components/program-switcher'
import { RoleSwitcher } from '@/components/role-switcher'
import { ThemeMenuItems } from '@/components/theme-toggle'
import { Sheet, SheetContent, SheetTitle } from '@/components/ui/sheet'

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
    label: 'Course Level Settings',
    to: '/course-settings',
    icon: BookOpen,
    sectionKey: 'courseSettings',
    anyOfPermissions: ['curriculum.view'],
  },
  {
    label: 'Program Level Setting',
    to: '/program-settings',
    icon: Target,
    sectionKey: 'programSettings',
    anyOfPermissions: ['curriculum.view', 'program.view'],
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
      'academic_calendar.view',
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
    label: 'Analytics',
    to: '/analytics',
    icon: LineChart,
    sectionKey: 'analytics',
    anyOfPermissions: ['program.view', 'attainment.calculate', 'assessment.approve', 'assessment.view'],
  },
  {
    label: 'Institute Settings',
    to: '/organization',
    icon: ShieldCheck,
    sectionKey: 'organization',
    anyOfPermissions: ['org.view', 'program.view', 'user.view', 'institution.view'],
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
  {
    label: 'About',
    to: '/about',
    icon: Info,
    sectionKey: 'about',
    anyOfPermissions: [],
  },
]

function initials(fullName: string): string {
  const parts = fullName.trim().split(/\s+/)
  const first = parts[0]?.[0] ?? ''
  const last = parts.length > 1 ? (parts[parts.length - 1]?.[0] ?? '') : ''
  return (first + last).toUpperCase() || 'U'
}

function BrandMark() {
  return (
    <div className="flex items-center gap-2.5">
      <div className="flex size-8 items-center justify-center rounded-md bg-primary text-primary-foreground">
        <Logo className="size-5" />
      </div>
      <span className="font-display text-sm font-semibold tracking-tight">OBEvolve</span>
    </div>
  )
}

function NavLinks({
  items,
  isDeemphasized,
  onNavigate,
}: {
  items: NavItem[]
  isDeemphasized: (item: NavItem) => boolean
  onNavigate?: () => void
}) {
  const location = useLocation()

  return (
    <nav className="flex-1 space-y-0.5 overflow-y-auto px-3 py-4">
      {items.map((item) => {
        const isActive = location.pathname === item.to
        const deemphasized = isDeemphasized(item)

        return (
          <Link
            key={item.to}
            to={item.to}
            onClick={onNavigate}
            className={cn(
              'flex w-full items-center gap-3 rounded-md border-l-2 border-transparent px-3 py-2 text-sm font-medium transition-colors',
              isActive
                ? 'border-primary bg-primary/10 text-primary'
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
  )
}

export function AppLayout() {
  const { user, hasPermission, logout } = useAuth()
  const { activeRole } = useActiveRole()
  const navigate = useNavigate()
  const location = useLocation()
  const [mobileNavOpen, setMobileNavOpen] = React.useState(false)

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

  const accountMenu = (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" className="flex items-center gap-2 px-2">
          <Avatar className="size-8">
            <AvatarFallback>{initials(user?.full_name ?? 'U')}</AvatarFallback>
          </Avatar>
          <span className="hidden text-sm font-medium sm:inline">{user?.full_name}</span>
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel className="flex flex-col gap-0.5">
          <span className="flex items-center gap-1.5 font-medium">
            <UserIcon className="size-3.5" /> {user?.full_name}
          </span>
          <span className="text-xs font-normal text-muted-foreground">{user?.email}</span>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={() => navigate('/profile')}>
          <UserIcon className="size-4" />
          Your profile
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <ThemeMenuItems />
        <DropdownMenuItem
          onClick={handleLogout}
          className="text-destructive focus:text-destructive"
        >
          <LogOut className="size-4" />
          Log out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )

  return (
    <div className="flex min-h-screen bg-background">
      <aside className="hidden w-64 shrink-0 border-r bg-card md:flex md:flex-col">
        <div className="flex h-16 items-center border-b px-6">
          <BrandMark />
        </div>
        <NavLinks items={visibleItems} isDeemphasized={isDeemphasized} />
        <div className="border-t p-3">
          <p className="px-3 py-2 text-xs text-muted-foreground">
            {user?.full_name} · {user?.roles.length ?? 0} role
            {(user?.roles.length ?? 0) === 1 ? '' : 's'}
          </p>
        </div>
      </aside>

      <Sheet open={mobileNavOpen} onOpenChange={setMobileNavOpen}>
        <SheetContent side="left" className="flex w-72 flex-col p-0">
          <SheetTitle className="sr-only">Navigation</SheetTitle>
          <div className="flex h-16 items-center border-b px-6">
            <BrandMark />
          </div>
          <NavLinks
            items={visibleItems}
            isDeemphasized={isDeemphasized}
            onNavigate={() => setMobileNavOpen(false)}
          />
          <div className="border-t p-3">
            <p className="px-3 py-2 text-xs text-muted-foreground">
              {user?.full_name} · {user?.roles.length ?? 0} role
              {(user?.roles.length ?? 0) === 1 ? '' : 's'}
            </p>
          </div>
        </SheetContent>
      </Sheet>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 shrink-0 items-center justify-between gap-2 border-b bg-card px-4 md:px-6">
          <div className="flex min-w-0 items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              className="shrink-0 md:hidden"
              aria-label="Open navigation menu"
              onClick={() => setMobileNavOpen(true)}
            >
              <Menu className="size-5" />
            </Button>
            <span className="truncate text-sm font-medium text-foreground">
              {navItems.find((i) => i.to === location.pathname)?.label ?? 'OBEvolve'}
            </span>
          </div>

          <div className="flex shrink-0 items-center gap-1.5 sm:gap-2">
            <div className="hidden items-center gap-1.5 sm:flex sm:gap-2">
              <ProgramSwitcher />
              <RoleSwitcher />
            </div>
            {accountMenu}
          </div>
        </header>

        <main className="flex-1 overflow-y-auto p-4 md:p-8">
          <div className="mx-auto w-full max-w-7xl">
            <Outlet />
          </div>
        </main>

        <Footer />
      </div>
    </div>
  )
}
