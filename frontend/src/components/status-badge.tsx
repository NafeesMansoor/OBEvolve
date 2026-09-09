import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

/** Shared workflow status enum used across program versions, course versions,
 * PEOs, program/course outcomes, questions, and assessments (backend
 * app/db/base.py WorkflowStatus). */
export type WorkflowStatus = 'draft' | 'submitted' | 'reviewed' | 'approved' | 'published'

// Ink & Neon categorical recipe (docs/DESIGN_SYSTEM.md §4.3): a fixed hue per
// status, reused everywhere WorkflowStatus appears. `reviewed` uses purple
// (not the brand green) deliberately — green is the brand primary, so
// reusing it here would read as "this status is the same thing as the
// primary action."
const STYLES: Record<WorkflowStatus, string> = {
  draft: 'bg-muted text-muted-foreground border-transparent',
  submitted: 'bg-blue-100 text-blue-800 border-transparent dark:bg-blue-950 dark:text-blue-300',
  reviewed:
    'bg-purple-100 text-purple-800 border-transparent dark:bg-purple-950 dark:text-purple-300',
  approved:
    'bg-emerald-100 text-emerald-800 border-transparent dark:bg-emerald-950 dark:text-emerald-300',
  published:
    'bg-teal-100 text-teal-800 border-transparent dark:bg-teal-950 dark:text-teal-300',
}

export const WORKFLOW_NEXT: Record<WorkflowStatus, WorkflowStatus | null> = {
  draft: 'submitted',
  submitted: 'reviewed',
  reviewed: 'approved',
  approved: 'published',
  published: null,
}

export function StatusBadge({ status }: { status: string }) {
  const key = status as WorkflowStatus
  const style = STYLES[key] ?? 'bg-muted text-muted-foreground border-transparent'
  return (
    <Badge variant="outline" className={cn('font-normal capitalize', style)}>
      {status}
    </Badge>
  )
}
