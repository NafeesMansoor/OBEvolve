import * as React from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'
import { z } from 'zod'

import { useAuth } from '@/features/auth/useAuth'
import { apiClient, ApiError } from '@/lib/api-client'
import { useEntityList } from '@/lib/crud-hooks'
import { Button } from '@/components/ui/button'
import { DataTable, type DataTableColumn } from '@/components/data-table'
import { EntityFormDialog, type EntityField } from '@/components/entity-form-dialog'
import { StatusBadge } from '@/components/status-badge'

interface CurriculumFeedback {
  id: string
  entity_type: string
  entity_id: string
  comment: string
  status: string
  submitted_by: string
  reviewed_by: string | null
  review_note: string | null
  reviewed_at: string | null
  created_at: string
}

const reviewSchema = z.object({
  status: z.enum(['accepted', 'ignored', 'resolved']),
  review_note: z.string().optional(),
})

/** Program/Institution Administrator's inbox for Program Coordinator
 * feedback (spec §25-26) — the reverse side of the "Provide Feedback"
 * action on PEOsTab/ProgramOutcomesTab. Anyone with `curriculum.view` can
 * see the list (shared visibility); only `program_outcome_framework.manage`
 * holders get the review action. */
export function CurriculumFeedbackTab() {
  const { hasPermission } = useAuth()
  const canReview = hasPermission('program_outcome_framework.manage')
  const [reviewing, setReviewing] = React.useState<CurriculumFeedback | null>(null)
  const queryClient = useQueryClient()

  const {
    data: feedback,
    isLoading,
    error,
  } = useEntityList<CurriculumFeedback>(
    ['curriculum', 'curriculum-feedback'],
    '/curriculum/curriculum-feedback',
  )

  const review = useMutation<CurriculumFeedback, unknown, { id: string; body: Record<string, unknown> }>({
    mutationFn: async ({ id, body }) => {
      const res = await apiClient.post<CurriculumFeedback>(`/curriculum/curriculum-feedback/${id}/review`, body)
      return res.data
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['curriculum', 'curriculum-feedback'] }),
  })

  const columns: DataTableColumn<CurriculumFeedback>[] = [
    { key: 'entity_type', header: 'Item', render: (r) => <span className="capitalize">{r.entity_type.replace(/_/g, ' ')}</span> },
    { key: 'comment', header: 'Feedback', render: (r) => r.comment, className: 'max-w-md' },
    { key: 'status', header: 'Status', render: (r) => <StatusBadge status={r.status} /> },
    {
      key: 'created_at',
      header: 'Submitted',
      render: (r) => new Date(r.created_at).toLocaleString(),
    },
  ]

  const reviewFields: EntityField[] = [
    {
      name: 'status',
      label: 'Decision',
      type: 'select',
      options: [
        { label: 'Accept', value: 'accepted' },
        { label: 'Ignore', value: 'ignored' },
        { label: 'Mark resolved', value: 'resolved' },
      ],
    },
    { name: 'review_note', label: 'Note (optional)', type: 'textarea' },
  ]

  return (
    <div className="flex flex-col gap-4">
      <DataTable
        data={feedback}
        columns={columns}
        rowKey={(r) => r.id}
        isLoading={isLoading}
        error={error}
        emptyMessage="No curriculum feedback submitted yet."
        actions={(r) => {
          if (!canReview || r.status !== 'open') return null
          return (
            <Button size="sm" variant="outline" onClick={() => setReviewing(r)}>
              Review
            </Button>
          )
        }}
      />

      {reviewing && (
        <EntityFormDialog
          open={Boolean(reviewing)}
          onOpenChange={(open) => !open && setReviewing(null)}
          title={`Review feedback: ${reviewing.entity_type.replace(/_/g, ' ')}`}
          description={reviewing.comment}
          fields={reviewFields}
          schema={reviewSchema}
          defaultValues={{ status: 'accepted', review_note: '' }}
          submitLabel="Save decision"
          onSubmit={async (values) => {
            try {
              await review.mutateAsync({
                id: reviewing.id,
                body: { status: values.status, review_note: values.review_note || null },
              })
              toast.success('Feedback reviewed')
            } catch (err) {
              throw err instanceof ApiError ? err : new ApiError('Unable to review feedback.')
            }
          }}
        />
      )}
    </div>
  )
}
