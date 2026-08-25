import * as React from 'react'
import {
  BarChart3,
  BookOpen,
  ClipboardCheck,
  LayoutDashboard,
  LogOut,
  MessagesSquare,
  Network,
  ShieldCheck,
  User as UserIcon,
} from 'lucide-react'
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom'

import { useAuth } from '@/features/auth/useAuth'
import { cn } from '@/lib/utils'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Separator } from '@/components/ui/separator'

interface NavItem {
  label: string
  to: string
  icon: React.ComponentType<{ className?: string }>
  /** Phase in which this module ships; undefined means it's live now. */
  comingInPhase?: number
}

const navItems: NavItem[] = [
  { label: 'Dashboard', to: '/', icon: LayoutDashboard },
  { label: 'Curriculum', to: '/curriculum', icon: BookOpen, comingInPhase: 3 },
  { label: 'Outcomes & Mapping', to: '/outcomes', icon: Network, comingInPhase: 3 },
  { label: 'Assessments', to: '/assessments', icon: ClipboardCheck, comingInPhase: 5 },
  { label: 'Attainment', to: '/attainment', icon: BarChart3, comingInPhase: 6 },
  { label: 'Surveys', to: '/surveys', icon: MessagesSquare, comingInPhase: 7 },
  { label: 'Accreditation', to: '/accreditation', icon: ShieldCheck, comingInPhase: 8 },
]

function initials(fullName: string): string {
  const parts = fullName.trim().split(/\s+/)
  const first = parts[0]?.[0] ?? ''
  const last = parts.length > 1 ? (parts[parts.length - 1]?.[0] ?? '') : ''
  return (first + last).toUpperCase() || 'U'
}

export function AppLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  function handleLogout() {
    logout()
    navigate('/login', { replace: true })
  }

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
          {navItems.map((item) => {
            const isActive = location.pathname === item.to
            const isDisabled = item.comingInPhase !== undefined

            const content = (
              <>
                <item.icon className="size-4 shrink-0" />
                <span className="flex-1 truncate text-left">{item.label}</span>
                {isDisabled ? (
                  <Badge variant="outline" className="ml-auto shrink-0 text-[10px] font-normal">
                    Phase {item.comingInPhase}
                  </Badge>
                ) : null}
              </>
            )

            const className = cn(
              'flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
              isActive && !isDisabled
                ? 'bg-primary/10 text-primary'
                : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground',
              isDisabled && 'cursor-not-allowed opacity-50 hover:bg-transparent hover:text-muted-foreground',
            )

            if (isDisabled) {
              return (
                <div key={item.to} className={className} aria-disabled="true" title={`Coming in Phase ${item.comingInPhase}`}>
                  {content}
                </div>
              )
            }

            return (
              <Link key={item.to} to={item.to} className={className}>
                {content}
              </Link>
            )
          })}
        </nav>

        <div className="border-t p-3">
          <p className="px-3 py-2 text-xs text-muted-foreground">
            Phase 1 — Foundation. Additional modules unlock as later phases ship.
          </p>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 shrink-0 items-center justify-between border-b bg-card px-4 md:px-6">
          {/* Breadcrumbs slot: empty in Phase 1 (single-level nav), reserved
              for deeper hierarchy (e.g. Program > Course > Outcome) once
              those modules exist. */}
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <span className="font-medium text-foreground">
              {navItems.find((i) => i.to === location.pathname)?.label ?? 'OBEvolve'}
            </span>
          </div>

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
              <DropdownMenuItem onClick={handleLogout} className="text-destructive focus:text-destructive">
                <LogOut className="size-4" />
                Log out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </header>

        <Separator className="md:hidden" />

        <main className="flex-1 overflow-y-auto p-4 md:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
