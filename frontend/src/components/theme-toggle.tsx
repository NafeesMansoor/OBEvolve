import { Check, Monitor, Moon, Sun } from 'lucide-react'
import { useTheme } from 'next-themes'

import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'

const OPTIONS = [
  { value: 'light', label: 'Light', icon: Sun },
  { value: 'dark', label: 'Dark', icon: Moon },
  { value: 'system', label: 'System', icon: Monitor },
] as const

/**
 * Meant to be rendered as extra items inside an existing account
 * DropdownMenuContent (see app/layout.tsx) — not a standalone trigger, so it
 * shares the one menu instead of adding a second floating control next to
 * the avatar.
 */
export function ThemeMenuItems() {
  return (
    <>
      <DropdownMenuLabel>Appearance</DropdownMenuLabel>
      <ThemeMenuItemsInner />
      <DropdownMenuSeparator />
    </>
  )
}

/**
 * Self-contained icon-button trigger + menu, for chrome that doesn't already
 * have an account dropdown to fold ThemeMenuItems into (the platform-admin
 * header renders its own "Log out" button rather than a DropdownMenu).
 */
export function ThemeToggleButton() {
  const { theme, resolvedTheme } = useTheme()
  // `theme`/`resolvedTheme` are briefly undefined until next-themes reads
  // localStorage on mount — harmless here (no SSR, so no hydration mismatch
  // to guard against), just falls back to Monitor for one render.
  const ActiveIcon =
    theme === 'system' || theme === undefined ? Monitor : resolvedTheme === 'dark' ? Moon : Sun

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" aria-label="Change theme">
          <ActiveIcon className="size-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-40">
        <ThemeMenuItemsInner />
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

function ThemeMenuItemsInner() {
  const { theme, setTheme } = useTheme()

  return (
    <>
      {OPTIONS.map((opt) => (
        <DropdownMenuItem
          key={opt.value}
          onClick={() => setTheme(opt.value)}
          className="flex items-center justify-between"
        >
          <span className="flex items-center gap-2">
            <opt.icon className="size-4" />
            {opt.label}
          </span>
          {theme === opt.value && <Check className="size-4" />}
        </DropdownMenuItem>
      ))}
    </>
  )
}
