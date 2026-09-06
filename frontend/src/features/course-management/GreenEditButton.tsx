import { Pencil } from 'lucide-react'
import type { ReactNode } from 'react'

import { Button } from '@/components/ui/button'

/** Course-Level Settings spec §3/§12: a section that's enabled for a Course
 * Teacher's course type shows a green "Edit" button; a disabled section
 * shows no edit affordance at all (not a greyed-out one) — so this renders
 * nothing when `enabled` is false, rather than a disabled button. */
export function GreenEditButton({
  enabled,
  onClick,
  label = 'Edit',
  icon = <Pencil className="size-4" />,
}: {
  enabled: boolean
  onClick: () => void
  label?: string
  icon?: ReactNode
}) {
  if (!enabled) return null
  return (
    <Button
      size="sm"
      onClick={onClick}
      className="bg-emerald-600 text-white hover:bg-emerald-700 dark:bg-emerald-500 dark:hover:bg-emerald-600"
    >
      {icon} {label}
    </Button>
  )
}
