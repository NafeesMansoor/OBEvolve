import { toast } from 'sonner'
import { z } from 'zod'

import { ApiError } from '@/lib/api-client'
import { useEntityCreate } from '@/lib/crud-hooks'
import { EntityFormDialog, type EntityField } from '@/components/entity-form-dialog'

const schema = z.object({
  comment: z.string().min(1, 'Feedback is required'),
})

const fields: EntityField[] = [
  { name: 'comment', label: 'Feedback', type: 'textarea', placeholder: 'What should change and why?' },
]

/** Master_Architecture_Part1.md §25: Program Coordinator's one write action
 * on a read-only Program & Curriculum Level item — submit feedback for the
 * Program/Institution Administrator to review, never edit the item itself. */
export function CurriculumFeedbackDialog({
  open,
  onOpenChange,
  entityType,
  entityId,
  entityLabel,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  entityType: string
  entityId: string
  entityLabel: string
}) {
  const create = useEntityCreate<Record<string, unknown>>('/curriculum/curriculum-feedback', [
    ['curriculum', 'curriculum-feedback'],
  ])

  return (
    <EntityFormDialog
      open={open}
      onOpenChange={onOpenChange}
      title={`Provide feedback: ${entityLabel}`}
      description="Visible to the Program/Institution Administrator for review — you'll be notified once it's acted on."
      fields={fields}
      schema={schema}
      defaultValues={{ comment: '' }}
      onSubmit={async (values) => {
        try {
          await create.mutateAsync({
            entity_type: entityType,
            entity_id: entityId,
            comment: values.comment,
          })
          toast.success('Feedback submitted')
        } catch (err) {
          throw err instanceof ApiError ? err : new ApiError('Unable to submit feedback.')
        }
      }}
      submitLabel="Submit feedback"
    />
  )
}
