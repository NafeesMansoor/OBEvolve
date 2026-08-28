import * as React from 'react'
import { Check, Inbox, X } from 'lucide-react'
import { toast } from 'sonner'

import { ApiError } from '@/lib/api-client'
import { useResetOnChange } from '@/lib/use-reset-on-change'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { PageHeader } from '@/components/page-header'
import { RequirePermission } from '@/components/require-permission'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
import { usePendingChanges, useReviewPendingChange } from '@/features/raw-data/api'
import type { ChangeRequestRead } from '@/features/raw-data/types'

function Json({ value }: { value: unknown }) {
  if (value === null || value === undefined) {
    return <span className="text-muted-foreground">—</span>
  }
  return (
    <pre className="max-h-64 overflow-auto rounded-md bg-muted p-2 text-xs">
      {JSON.stringify(value, null, 2)}
    </pre>
  )
}

function ChangeDiff({ change }: { change: ChangeRequestRead }) {
  if (change.operation === 'insert') {
    return (
      <div>
        <p className="mb-1 text-xs font-medium text-muted-foreground">New row (payload)</p>
        <Json value={change.payload_json} />
      </div>
    )
  }
  if (change.operation === 'delete') {
    return (
      <div>
        <p className="mb-1 text-xs font-medium text-muted-foreground">
          Row to be removed (row_pk: {change.row_pk})
        </p>
        <Json value={change.previous_json} />
      </div>
    )
  }
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
      <div>
        <p className="mb-1 text-xs font-medium text-muted-foreground">
          Before (row_pk: {change.row_pk})
        </p>
        <Json value={change.previous_json} />
      </div>
      <div>
        <p className="mb-1 text-xs font-medium text-muted-foreground">After (proposed)</p>
        <Json value={change.payload_json} />
      </div>
    </div>
  )
}

const OPERATION_VARIANT: Record<string, 'default' | 'secondary' | 'destructive' | 'outline'> = {
  insert: 'secondary',
  update: 'default',
  delete: 'destructive',
}

interface ReviewDialogState {
  change: ChangeRequestRead
  decision: 'approve' | 'reject'
}

function ReviewDialog({
  state,
  onOpenChange,
}: {
  state: ReviewDialogState | null
  onOpenChange: (open: boolean) => void
}) {
  // Resets whenever a different review is opened (or the dialog closes) —
  // render-time adjustment, see lib/use-reset-on-change.ts.
  const [note, setNote] = useResetOnChange(state, '')
  const [error, setError] = useResetOnChange<string | null>(state, null)
  const approve = useReviewPendingChange('approve')
  const reject = useReviewPendingChange('reject')
  const mutation = state?.decision === 'reject' ? reject : approve
  const [isSubmitting, setIsSubmitting] = React.useState(false)

  if (!state) return null

  async function handleConfirm() {
    if (!state) return
    setIsSubmitting(true)
    setError(null)
    try {
      await mutation.mutateAsync({ id: state.change.id, reviewNote: note })
      toast.success(state.decision === 'approve' ? 'Change approved and applied' : 'Change rejected')
      onOpenChange(false)
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : 'Something went wrong. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <Dialog open={Boolean(state)} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>
            {state.decision === 'approve' ? 'Approve' : 'Reject'} change to {state.change.table_name}
          </DialogTitle>
          <DialogDescription>
            {state.decision === 'approve'
              ? 'This will apply the proposed change immediately.'
              : 'This will discard the proposed change. It will not be applied.'}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-1.5">
          <label className="text-sm font-medium" htmlFor="review-note">
            Review note (optional)
          </label>
          <Textarea
            id="review-note"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            placeholder="Optional context for the requester…"
          />
        </div>

        {error ? (
          <p role="alert" className="rounded-md bg-destructive/10 px-3 py-2 text-sm text-destructive">
            {error}
          </p>
        ) : null}

        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            variant={state.decision === 'reject' ? 'destructive' : 'default'}
            className={
              state.decision === 'approve'
                ? 'bg-success text-success-foreground hover:bg-success/90'
                : undefined
            }
            disabled={isSubmitting}
            onClick={handleConfirm}
          >
            {isSubmitting ? 'Working…' : state.decision === 'approve' ? 'Approve' : 'Reject'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export function PendingChangesPage() {
  const { data, isLoading, error } = usePendingChanges()
  const [reviewState, setReviewState] = React.useState<ReviewDialogState | null>(null)

  return (
    <RequirePermission anyOf={['raw_data.approve']}>
      <PageHeader
        title="Pending raw-data changes"
        description="Course-level edits proposed by Program Coordinators, awaiting your review as Program Administrator."
      />

      {isLoading ? (
        <div className="flex flex-col gap-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-32 w-full" />
          ))}
        </div>
      ) : error ? (
        <p className="text-sm text-destructive">
          {error instanceof ApiError ? error.detail : 'Failed to load pending changes.'}
        </p>
      ) : (data ?? []).length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center gap-2 py-16 text-center">
            <Inbox className="size-8 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">No pending changes to review.</p>
          </CardContent>
        </Card>
      ) : (
        <div className="flex flex-col gap-3">
          {data?.map((change) => (
            <Card key={change.id}>
              <CardContent className="flex flex-col gap-3 p-4">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <Badge variant={OPERATION_VARIANT[change.operation] ?? 'default'}>
                      {change.operation}
                    </Badge>
                    <span className="font-mono text-sm font-medium">{change.table_name}</span>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    Requested by {change.requested_by} ·{' '}
                    {new Date(change.created_at).toLocaleString()}
                  </span>
                </div>

                <ChangeDiff change={change} />

                <div className="flex justify-end gap-3">
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => setReviewState({ change, decision: 'reject' })}
                  >
                    <X className="size-4" /> Reject
                  </Button>
                  <Button
                    size="sm"
                    className="bg-success text-success-foreground hover:bg-success/90"
                    onClick={() => setReviewState({ change, decision: 'approve' })}
                  >
                    <Check className="size-4" /> Approve
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <ReviewDialog state={reviewState} onOpenChange={(open) => !open && setReviewState(null)} />
    </RequirePermission>
  )
}
