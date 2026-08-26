import { Check, UserCog } from 'lucide-react'

import { useAuth } from '@/features/auth/useAuth'
import { useActiveRole } from '@/lib/active-role-context'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

/**
 * Presentational role switcher — picking a role only changes which sidebar
 * sections are emphasized (see lib/active-role-context.tsx); the user keeps
 * every permission they hold regardless of which role is "active" here.
 * Hidden entirely if the user has 0 or 1 roles, since there's nothing to
 * switch between.
 */
export function RoleSwitcher() {
  const { user } = useAuth()
  const { activeRole, setActiveRole } = useActiveRole()

  if (!user || user.roles.length < 2) return null

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm" className="gap-1.5">
          <UserCog className="size-4" />
          {activeRole ?? 'All roles'}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel>Viewing as</DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem onClick={() => setActiveRole(null)} className="flex items-center justify-between">
          All roles (everything you have access to)
          {activeRole === null && <Check className="size-4" />}
        </DropdownMenuItem>
        {user.roles.map((role) => (
          <DropdownMenuItem
            key={role}
            onClick={() => setActiveRole(role)}
            className="flex items-center justify-between"
          >
            {role}
            {activeRole === role && <Check className="size-4" />}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
