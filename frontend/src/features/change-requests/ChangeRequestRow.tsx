import * as React from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { useAuth } from '@/features/auth/useAuth'
import {
  STATUS_LABELS,
  TARGET_FIELD_LABELS,
  type ChangeRequestStatus,
  type CourseChangeRequest,
} from '@/features/change-requests/types'
import { ApiError, apiClient } from '@/lib/api-client'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { TableCell, TableRow } from '@/components/ui/table'

const STATUS_STYLE: Record<ChangeRequestStatus, string> = {
  draft: 'bg-muted text-muted-foreground',
  pending_admin: 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300',
  pending_program_coordinator: 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300',
  approved: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300',
  rejected: 'bg-destructive/10 text-destructive',
  returned: 'bg-orange-100 text-orange-800 dark:bg-orange-950 dark:text-orange-300',
}

/** `proposed_value_json`/`edited_value_json` shapes vary by `target_field`
 * (see app.services.course_type_config's appliers) — this renders the two
 * common shapes (a scalar `{value}` or `{outcomes: [...]}`) readably and
 * falls back to raw JSON for the rest (enrollment/assessment actions),
 * rather than building a bespoke editor per shape. */
function summarize(value: Record<string, unknown> | null): string {
  if (!value) return '—'
  if ('value' in value) return String(value.value ?? '—')
  if ('outcomes' in value && Array.isArray(value.outcomes)) {
    return value.outcomes.map((o: Record<string, unknown>) => `${o.code}: ${o.statement}`).join('; ') || '—'
  }
  return JSON.stringify(value)
}

function valueToText(value: Record<string, unknown> | null): string {
  if (!value) return ''
  if ('value' in value) return String(value.value ?? '')
  return JSON.stringify(value, null, 2)
}

function textToValue(original: Record<string, unknown> | null, text: string): Record<string, unknown> {
  if (original && 'value' in original) return { value: text }
  try {
    return JSON.parse(text) as Record<string, unknown>
  } catch {
    return { value: text }
  }
}

/** The stage a given status is awaiting action at, and the permission code
 * that gates acting on it (docs/course_level_settings_and_approval_workflow.md
 * §5-§6) — Course Administrator/Course Coordinator act on pending_admin,
 * Program Coordinator on pending_program_coordinator. */
function requiredPermission(status: ChangeRequestStatus): string | null {
  if (status === 'pending_admin') return 'course_change_request.review_admin'
  if (status === 'pending_program_coordinator') return 'course_change_request.review_program'
  return null
}

export function ChangeRequestRow({ request }: { request: CourseChangeRequest }) {
  const { hasPermission } = useAuth()
  const queryClient = useQueryClient()
  const [dialogAction, setDialogAction] = React.useState<'approved' | 'rejected' | 'returned' | null>(
    null,
  )
  const [editedText, setEditedText] = React.useState('')
  const [reviewNote, setReviewNote] = React.useState('')
  const [submitting, setSubmitting] = React.useState(false)

  const required = requiredPermission(request.status)
  const canActOnThisStage = required !== null && hasPermission(required)

  function openDialog(action: 'approved' | 'rejected' | 'returned') {
    setEditedText(valueToText(request.edited_value_json ?? request.proposed_value_json))
    setReviewNote('')
    setDialogAction(action)
  }

  async function submitReview() {
    if (!dialogAction) return
    setSubmitting(true)
    try {
      const body: Record<string, unknown> = { status: dialogAction, review_note: reviewNote || null }
      if (dialogAction === 'approved') {
        body.edited_value_json = textToValue(request.proposed_value_json, editedText)
      }
      await apiClient.post(`/course-change-requests/${request.id}/review`, body)
      await queryClient.invalidateQueries({ queryKey: ['course-change-requests'] })
      toast.success(`Request ${dialogAction}`)
      setDialogAction(null)
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Review failed')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <>
      <TableRow>
        <TableCell>{TARGET_FIELD_LABELS[request.target_field]}</TableCell>
        <TableCell className="max-w-[16rem] truncate" title={summarize(request.current_value_json)}>
          {summarize(request.current_value_json)}
        </TableCell>
        <TableCell className="max-w-[16rem] truncate" title={summarize(request.proposed_value_json)}>
          {summarize(request.proposed_value_json)}
        </TableCell>
        <TableCell className="max-w-[16rem] truncate" title={summarize(request.edited_value_json)}>
          {request.edited_value_json ? summarize(request.edited_value_json) : '—'}
        </TableCell>
        <TableCell className="max-w-xs truncate" title={request.reason}>
          {request.reason}
        </TableCell>
        <TableCell>
          <Badge className={STATUS_STYLE[request.status]} variant="outline">
            {STATUS_LABELS[request.status]}
          </Badge>
          {request.apply_status === 'failed' && (
            <Badge variant="outline" className="ml-1 bg-destructive/10 text-destructive">
              Apply failed
            </Badge>
          )}
        </TableCell>
        <TableCell className="text-muted-foreground">
          {new Date(request.created_at).toLocaleDateString()}
        </TableCell>
        <TableCell className="text-right">
          {canActOnThisStage && (
            <div className="flex justify-end gap-2">
              <Button size="sm" variant="outline" onClick={() => openDialog('approved')}>
                Edit / Approve
              </Button>
              <Button size="sm" variant="outline" onClick={() => openDialog('rejected')}>
                Reject
              </Button>
              <Button size="sm" variant="outline" onClick={() => openDialog('returned')}>
                Return
              </Button>
            </div>
          )}
        </TableCell>
      </TableRow>

      <Dialog open={dialogAction !== null} onOpenChange={(open) => !open && setDialogAction(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {dialogAction === 'approved' && 'Approve change request'}
              {dialogAction === 'rejected' && 'Reject change request'}
              {dialogAction === 'returned' && 'Return for revision'}
            </DialogTitle>
            <DialogDescription>
              {TARGET_FIELD_LABELS[request.target_field]} — original request: {request.reason}
            </DialogDescription>
          </DialogHeader>
          <div className="flex flex-col gap-3">
            {dialogAction === 'approved' && (
              <div className="flex flex-col gap-1.5">
                <Label>Value to apply (edit before approving if needed)</Label>
                <Textarea
                  value={editedText}
                  onChange={(e) => setEditedText(e.target.value)}
                  rows={4}
                />
              </div>
            )}
            <div className="flex flex-col gap-1.5">
              <Label>Note (optional)</Label>
              <Textarea
                value={reviewNote}
                onChange={(e) => setReviewNote(e.target.value)}
                rows={2}
                placeholder="Visible to the requester and other reviewers"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogAction(null)} disabled={submitting}>
              Cancel
            </Button>
            <Button onClick={() => void submitReview()} disabled={submitting}>
              Confirm
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
