import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

/** Shared workflow status enum used across program versions, course versions,
 * PEOs, program/course outcomes, questions, and assessments (backend
 * app/db/base.py WorkflowStatus). */
export type WorkflowStatus = 'draft' | 'submitted' | 'reviewed' | 'approved' | 'published'

const STYLES: Record<WorkflowStatus, string> = {
  draft: 'bg-muted text-muted-foreground border-transparent',
  submitted: 'bg-blue-100 text-blue-800 border-transparent dark:bg-blue-950 dark:text-blue-300',
  reviewed:
    'bg-amber-100 text-amber-800 border-transparent dark:bg-amber-950 dark:text-amber-300',
  approved:
    'bg-emerald-100 text-emerald-800 border-transparent dark:bg-emerald-950 dark:text-emerald-300',
  published:
    'bg-violet-100 text-violet-800 border-transparent dark:bg-violet-950 dark:text-violet-300',
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
