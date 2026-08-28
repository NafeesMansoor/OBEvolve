import * as React from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { CheckCircle2, Inbox, Plus, Trash2, XCircle } from 'lucide-react'
import { toast } from 'sonner'
import { z } from 'zod'

import { useAuth } from '@/features/auth/useAuth'
import { useAcademicTermLookup } from '@/features/academic-ops/useLookups'
import { PROPOSED_ACTIONS, type ImprovementPlan } from '@/features/improvement/types'
import type { AppUser } from '@/features/organization/types'
import { ApiError, apiClient } from '@/lib/api-client'
import { useEntityCreate, useEntityDelete, useEntityList } from '@/lib/crud-hooks'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ConfirmAction } from '@/components/confirm-action'
import { EntityFormDialog, type EntityField } from '@/components/entity-form-dialog'
import { Skeleton } from '@/components/ui/skeleton'

const schema = z.object({
  problem_observation: z.string().min(1, 'Required'),
  proposed_action: z.string().min(1, 'Required'),
  proposed_action_detail: z.string().optional(),
  reason: z.string().min(1, 'Required'),
  expected_improvement: z.string().min(1, 'Required'),
  implementation_term_id: z.string().optional(),
  responsible_user_id: z.string().optional(),
  evidence: z.string().optional(),
})

const STATUS_VARIANT: Record<ImprovementPlan['status'], 'outline' | 'secondary' | 'destructive'> = {
  proposed: 'outline',
  approved: 'secondary',
  rejected: 'destructive',
  implemented: 'secondary',
}

/** CO-failure -> continuous-improvement workflow (spec §5): propose an
 * action plan against a CO within one course section, get it reviewed, and
 * mark it implemented. Embedded in AttainmentTab so it sits right next to
 * the "Not attained" result it responds to. */
export function ImprovementPlansPanel({
  courseSectionId,
  courseOutcomeId,
}: {
  courseSectionId: string
  /** Scopes both the list and the "New plan" button to one CO — this panel
   * is meant to be embedded per-CO (e.g. in an expandable row), not shared
   * across a whole section's worth of COs. */
  courseOutcomeId: string
}) {
  const { hasPermission, user } = useAuth()
  const canPropose =
    hasPermission('marks.enter') || hasPermission('assessment.create') || hasPermission('assessment.approve')
  const canReview = hasPermission('assessment.approve')

  const queryClient = useQueryClient()
  const { options: termOptions } = useAcademicTermLookup()
  // Only fetched when the current user can actually see the user directory
  // (`user.view`) — Faculty/Course Coordinator can propose plans but don't
  // hold that permission, and /users is a real directory listing (emails
  // included), unlike the open-to-everyone lookups (programs, terms), so
  // it isn't opened up the same way; the field is optional either way.
  const canSeeUsers = hasPermission('user.view')
  const { data: users } = useEntityList<AppUser>(['users'], '/users', undefined, {
    enabled: canSeeUsers,
  })
  const userOptions = React.useMemo(
    () => (users ?? []).map((u) => ({ label: `${u.full_name} (${u.email})`, value: u.id })),
    [users],
  )

  const [createOpen, setCreateOpen] = React.useState(false)

  const { data: plans, isLoading } = useEntityList<ImprovementPlan>(
    ['improvement-plans', courseSectionId, courseOutcomeId],
    '/improvement-plans',
    {
      course_section_id: courseSectionId,
      course_outcome_id: courseOutcomeId,
    },
    { enabled: Boolean(courseSectionId) },
  )

  const create = useEntityCreate<Record<string, unknown>, ImprovementPlan>('/improvement-plans', [
    ['improvement-plans', courseSectionId, courseOutcomeId],
  ])
  const remove = useEntityDelete((id) => `/improvement-plans/${id}`, [
    ['improvement-plans', courseSectionId, courseOutcomeId],
  ])

  async function review(planId: string, approve: boolean) {
    try {
      await apiClient.post(`/improvement-plans/${planId}/review`, { approve })
      await queryClient.invalidateQueries({
        queryKey: ['improvement-plans', courseSectionId, courseOutcomeId],
      })
      toast.success(approve ? 'Plan approved' : 'Plan rejected')
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Unable to review plan.')
    }
  }

  async function implement(planId: string) {
    try {
      await apiClient.post(`/improvement-plans/${planId}/implement`)
      await queryClient.invalidateQueries({
        queryKey: ['improvement-plans', courseSectionId, courseOutcomeId],
      })
      toast.success('Marked implemented')
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Unable to mark implemented.')
    }
  }

  const fields: EntityField[] = [
    { name: 'problem_observation', label: 'Problem / observation', type: 'textarea' },
    {
      name: 'proposed_action',
      label: 'Proposed action',
      type: 'select',
      options: PROPOSED_ACTIONS.map((a) => ({ label: a.label, value: a.value })),
    },
    {
      name: 'proposed_action_detail',
      label: 'Detail (required if "Other")',
      type: 'textarea',
    },
    { name: 'reason', label: 'Reason for action', type: 'textarea' },
    { name: 'expected_improvement', label: 'Expected improvement', type: 'textarea' },
    {
      name: 'implementation_term_id',
      label: 'Implementation term',
      type: 'select',
      options: termOptions,
    },
    {
      name: 'responsible_user_id',
      label: 'Responsible person',
      type: 'select',
      options: userOptions,
    },
    { name: 'evidence', label: 'Evidence (optional)', type: 'textarea' },
  ]

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <h4 className="font-display text-sm font-semibold">Improvement plans</h4>
        {canPropose && (
          <Button size="sm" variant="outline" onClick={() => setCreateOpen(true)}>
            <Plus className="size-3.5" /> New plan
          </Button>
        )}
      </div>

      {isLoading ? (
        <div className="flex flex-col gap-2">
          <Skeleton className="h-16 w-full" />
          <Skeleton className="h-16 w-full" />
        </div>
      ) : !plans?.length ? (
        <div className="flex flex-col items-center gap-2 rounded-md border border-dashed py-6 text-center text-muted-foreground">
          <Inbox className="size-5 opacity-50" />
          <span className="text-xs">No improvement plans yet.</span>
        </div>
      ) : (
        <div className="flex flex-col gap-2">
          {plans.map((p) => (
            <div key={p.id} className="rounded-md border p-3 text-sm">
              <div className="flex items-start justify-between gap-2">
                <div className="flex flex-col gap-1">
                  <div className="flex items-center gap-2">
                    <Badge variant={STATUS_VARIANT[p.status]} className="font-normal capitalize">
                      {p.status}
                    </Badge>
                    <span className="font-medium">
                      {PROPOSED_ACTIONS.find((a) => a.value === p.proposed_action)?.label ??
                        p.proposed_action}
                    </span>
                  </div>
                  <p className="text-muted-foreground">{p.problem_observation}</p>
                  <p className="text-xs text-muted-foreground">
                    Expected improvement: {p.expected_improvement}
                  </p>
                </div>
                <div className="flex shrink-0 items-center gap-1">
                  {canReview && p.status === 'proposed' && (
                    <>
                      <Button size="sm" variant="outline" onClick={() => void review(p.id, true)}>
                        <CheckCircle2 className="size-3.5" /> Approve
                      </Button>
                      <Button
                        size="sm"
                        variant="destructive"
                        className="ml-1"
                        onClick={() => void review(p.id, false)}
                      >
                        <XCircle className="size-3.5" /> Reject
                      </Button>
                    </>
                  )}
                  {canPropose && p.status === 'approved' && (
                    <Button size="sm" variant="outline" onClick={() => void implement(p.id)}>
                      Mark implemented
                    </Button>
                  )}
                  {canPropose && p.created_by === user?.id && p.status === 'proposed' && (
                    <ConfirmAction
                      trigger={
                        <Button
                          size="sm"
                          variant="ghost"
                          aria-label="Delete improvement plan"
                          className="ml-1 border-l pl-2 text-muted-foreground hover:text-destructive"
                        >
                          <Trash2 className="size-4" />
                        </Button>
                      }
                      title="Delete this improvement plan?"
                      onConfirm={async () => {
                        try {
                          await remove.mutateAsync(p.id)
                          toast.success('Plan deleted')
                        } catch (err) {
                          toast.error(err instanceof ApiError ? err.detail : 'Unable to delete plan.')
                        }
                      }}
                    />
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {createOpen && (
        <EntityFormDialog
          open={createOpen}
          onOpenChange={setCreateOpen}
          title="New improvement plan"
          fields={fields}
          schema={schema}
          defaultValues={{
            problem_observation: '',
            proposed_action: '',
            proposed_action_detail: '',
            reason: '',
            expected_improvement: '',
            implementation_term_id: '',
            responsible_user_id: '',
            evidence: '',
          }}
          onSubmit={async (values) => {
            try {
              await create.mutateAsync({
                course_section_id: courseSectionId,
                course_outcome_id: courseOutcomeId,
                problem_observation: values.problem_observation,
                proposed_action: values.proposed_action,
                proposed_action_detail: values.proposed_action_detail || null,
                reason: values.reason,
                expected_improvement: values.expected_improvement,
                implementation_term_id: values.implementation_term_id || null,
                responsible_user_id: values.responsible_user_id || null,
                evidence: values.evidence || null,
              })
              toast.success('Improvement plan created')
            } catch (err) {
              throw err instanceof ApiError ? err : new ApiError('Unable to create plan.')
            }
          }}
        />
      )}
    </div>
  )
}
