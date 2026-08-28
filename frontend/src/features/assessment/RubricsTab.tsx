import * as React from 'react'
import { Plus, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { z } from 'zod'

import { useAuth } from '@/features/auth/useAuth'
import type { Rubric, RubricCriterion, RubricLevel } from '@/features/assessment/types'
import { ApiError } from '@/lib/api-client'
import { useEntityCreate, useEntityDelete, useEntityList } from '@/lib/crud-hooks'
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ConfirmAction } from '@/components/confirm-action'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { EntityFormDialog, type EntityField } from '@/components/entity-form-dialog'
import { Skeleton } from '@/components/ui/skeleton'

const rubricSchema = z.object({
  name: z.string().min(1, 'Name is required').max(255),
  description: z.string().optional(),
  is_reusable: z.boolean().optional(),
})
const rubricFields: EntityField[] = [
  { name: 'name', label: 'Name', type: 'text' },
  { name: 'description', label: 'Description', type: 'textarea' },
  { name: 'is_reusable', label: 'Reusable across assessments', type: 'checkbox' },
]

const criterionSchema = z.object({
  criterion: z.string().min(1, 'Criterion is required'),
  weight: z.coerce.number(),
})

const levelSchema = z.object({
  label: z.string().min(1, 'Label is required').max(100),
  score: z.coerce.number(),
  description: z.string().optional(),
})

export function RubricsTab() {
  const { hasPermission } = useAuth()
  const canManage = hasPermission('assessment.create')
  const [createOpen, setCreateOpen] = React.useState(false)

  const { data: rubrics, isLoading, error } = useEntityList<Rubric>(
    ['assessment', 'rubrics'],
    '/assessment/rubrics',
  )
  const createRubric = useEntityCreate<Record<string, unknown>, Rubric>('/assessment/rubrics', [
    ['assessment', 'rubrics'],
  ])
  const removeRubric = useEntityDelete((id) => `/assessment/rubrics/${id}`, [
    ['assessment', 'rubrics'],
  ])

  return (
    <div className="flex flex-col gap-4">
      <div className="flex justify-end">
        {canManage && (
          <Button size="sm" onClick={() => setCreateOpen(true)}>
            <Plus className="size-4" /> New rubric
          </Button>
        )}
      </div>

      {isLoading ? (
        <Skeleton className="h-48 w-full" />
      ) : error ? (
        <p className="text-sm text-destructive">Failed to load rubrics.</p>
      ) : !rubrics || rubrics.length === 0 ? (
        <p className="text-sm text-muted-foreground">No rubrics yet.</p>
      ) : (
        <Accordion type="multiple" className="rounded-md border px-4">
          {rubrics.map((rubric) => (
            <RubricItem
              key={rubric.id}
              rubric={rubric}
              canManage={canManage}
              onDelete={async () => {
                try {
                  await removeRubric.mutateAsync(rubric.id)
                  toast.success('Rubric deleted')
                } catch (err) {
                  toast.error(err instanceof ApiError ? err.detail : 'Unable to delete rubric.')
                }
              }}
            />
          ))}
        </Accordion>
      )}

      <EntityFormDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        title="New rubric"
        fields={rubricFields}
        schema={rubricSchema}
        defaultValues={{ name: '', description: '', is_reusable: true }}
        onSubmit={async (values) => {
          try {
            await createRubric.mutateAsync({
              name: values.name,
              description: values.description || null,
              is_reusable: values.is_reusable ?? true,
            })
            toast.success('Rubric created')
          } catch (err) {
            throw err instanceof ApiError ? err : new ApiError('Unable to create rubric.')
          }
        }}
      />
    </div>
  )
}

function RubricItem({
  rubric,
  canManage,
  onDelete,
}: {
  rubric: Rubric
  canManage: boolean
  onDelete: () => void
}) {
  const [createCriterionOpen, setCreateCriterionOpen] = React.useState(false)
  const [levelsForCriterion, setLevelsForCriterion] = React.useState<RubricCriterion | null>(null)

  const { data: criteria, isLoading } = useEntityList<RubricCriterion>(
    ['assessment', 'rubric-criteria', rubric.id],
    '/assessment/rubric-criteria',
    { rubric_id: rubric.id },
  )
  const createCriterion = useEntityCreate<Record<string, unknown>, RubricCriterion>(
    '/assessment/rubric-criteria',
    [['assessment', 'rubric-criteria', rubric.id]],
  )
  const removeCriterion = useEntityDelete((id) => `/assessment/rubric-criteria/${id}`, [
    ['assessment', 'rubric-criteria', rubric.id],
  ])

  return (
    <AccordionItem value={rubric.id}>
      <AccordionTrigger>
        <div className="flex flex-1 items-center gap-2 pr-2 text-left">
          <span className="font-medium">{rubric.name}</span>
          {rubric.is_reusable && (
            <Badge variant="outline" className="font-normal">
              Reusable
            </Badge>
          )}
        </div>
      </AccordionTrigger>
      <AccordionContent>
        <div className="flex flex-col gap-3 pb-2">
          {rubric.description && <p className="text-sm text-muted-foreground">{rubric.description}</p>}
          <div className="flex justify-between">
            {canManage && (
              <ConfirmAction
                trigger={
                  <Button size="sm" variant="ghost" className="text-destructive">
                    <Trash2 className="size-4" /> Delete rubric
                  </Button>
                }
                title={`Delete rubric "${rubric.name}"?`}
                onConfirm={onDelete}
              />
            )}
            {canManage && (
              <Button size="sm" variant="outline" onClick={() => setCreateCriterionOpen(true)}>
                <Plus className="size-4" /> Add criterion
              </Button>
            )}
          </div>

          {isLoading ? (
            <Skeleton className="h-16 w-full" />
          ) : !criteria || criteria.length === 0 ? (
            <p className="text-sm text-muted-foreground">No criteria yet.</p>
          ) : (
            <div className="flex flex-col gap-2">
              {criteria.map((c) => (
                <div
                  key={c.id}
                  className="flex items-center justify-between rounded-md border px-3 py-2 text-sm"
                >
                  <span>
                    {c.criterion}{' '}
                    <span className="text-muted-foreground tabular-nums">(weight {c.weight})</span>
                  </span>
                  <div className="flex gap-1">
                    <Button size="sm" variant="outline" onClick={() => setLevelsForCriterion(c)}>
                      Levels
                    </Button>
                    {canManage && (
                      <ConfirmAction
                        trigger={
                          <Button size="sm" variant="ghost" aria-label={`Delete criterion "${c.criterion}"`}>
                            <Trash2 className="size-4 text-destructive" />
                          </Button>
                        }
                        title={`Delete criterion "${c.criterion}"?`}
                        onConfirm={async () => {
                          try {
                            await removeCriterion.mutateAsync(c.id)
                            toast.success('Criterion deleted')
                          } catch (err) {
                            toast.error(err instanceof ApiError ? err.detail : 'Unable to delete criterion.')
                          }
                        }}
                      />
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <EntityFormDialog
          open={createCriterionOpen}
          onOpenChange={setCreateCriterionOpen}
          title={`New criterion for ${rubric.name}`}
          fields={[
            { name: 'criterion', label: 'Criterion', type: 'text' },
            { name: 'weight', label: 'Weight', type: 'number', step: '0.01' },
          ]}
          schema={criterionSchema}
          defaultValues={{ criterion: '', weight: '' }}
          onSubmit={async (values) => {
            try {
              await createCriterion.mutateAsync({
                rubric_id: rubric.id,
                criterion: values.criterion,
                weight: values.weight,
              })
              toast.success('Criterion added')
            } catch (err) {
              throw err instanceof ApiError ? err : new ApiError('Unable to add criterion.')
            }
          }}
        />

        {levelsForCriterion && (
          <LevelsDialog
            criterion={levelsForCriterion}
            canManage={canManage}
            onClose={() => setLevelsForCriterion(null)}
          />
        )}
      </AccordionContent>
    </AccordionItem>
  )
}

function LevelsDialog({
  criterion,
  canManage,
  onClose,
}: {
  criterion: RubricCriterion
  canManage: boolean
  onClose: () => void
}) {
  const [createOpen, setCreateOpen] = React.useState(false)
  const { data: levels, isLoading } = useEntityList<RubricLevel>(
    ['assessment', 'rubric-levels', criterion.id],
    '/assessment/rubric-levels',
    { rubric_criterion_id: criterion.id },
  )
  const create = useEntityCreate<Record<string, unknown>, RubricLevel>('/assessment/rubric-levels', [
    ['assessment', 'rubric-levels', criterion.id],
  ])
  const remove = useEntityDelete((id) => `/assessment/rubric-levels/${id}`, [
    ['assessment', 'rubric-levels', criterion.id],
  ])

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Levels for &quot;{criterion.criterion}&quot;</DialogTitle>
        </DialogHeader>

        <div className="flex flex-col gap-2">
          {canManage && (
            <div className="flex justify-end">
              <Button size="sm" variant="outline" onClick={() => setCreateOpen(true)}>
                <Plus className="size-4" /> Add level
              </Button>
            </div>
          )}
          {isLoading ? (
            <Skeleton className="h-16 w-full" />
          ) : !levels || levels.length === 0 ? (
            <p className="text-sm text-muted-foreground">No levels yet.</p>
          ) : (
            levels
              .slice()
              .sort((a, b) => Number(b.score) - Number(a.score))
              .map((l) => (
                <div key={l.id} className="flex items-center justify-between rounded-md border px-3 py-2 text-sm">
                  <span>
                    {l.label} <span className="text-muted-foreground tabular-nums">({l.score} pts)</span>
                  </span>
                  {canManage && (
                    <ConfirmAction
                      trigger={
                        <Button size="sm" variant="ghost" aria-label={`Delete level "${l.label}"`}>
                          <Trash2 className="size-4 text-destructive" />
                        </Button>
                      }
                      title={`Delete level "${l.label}"?`}
                      onConfirm={async () => {
                        try {
                          await remove.mutateAsync(l.id)
                          toast.success('Level deleted')
                        } catch (err) {
                          toast.error(err instanceof ApiError ? err.detail : 'Unable to delete level.')
                        }
                      }}
                    />
                  )}
                </div>
              ))
          )}
        </div>

        <EntityFormDialog
          open={createOpen}
          onOpenChange={setCreateOpen}
          title={`New level for ${criterion.criterion}`}
          fields={[
            { name: 'label', label: 'Label', type: 'text', placeholder: 'e.g. Excellent' },
            { name: 'score', label: 'Score', type: 'number', step: '0.01' },
            { name: 'description', label: 'Description', type: 'textarea' },
          ]}
          schema={levelSchema}
          defaultValues={{ label: '', score: '', description: '' }}
          onSubmit={async (values) => {
            try {
              await create.mutateAsync({
                rubric_criterion_id: criterion.id,
                label: values.label,
                score: values.score,
                description: values.description || null,
              })
              toast.success('Level added')
            } catch (err) {
              throw err instanceof ApiError ? err : new ApiError('Unable to add level.')
            }
          }}
        />
      </DialogContent>
    </Dialog>
  )
}
