import * as React from 'react'
import { AlertCircle, Inbox, Plus, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { z } from 'zod'

import { useAuth } from '@/features/auth/useAuth'
import type { GradingBand, GradingPolicy } from '@/features/grading/types'
import { useProgramVersionOptions } from '@/features/curriculum/useProgramVersionOptions'
import { ApiError } from '@/lib/api-client'
import { useEntityCreate, useEntityDelete, useEntityList } from '@/lib/crud-hooks'
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { ConfirmAction } from '@/components/confirm-action'
import { PageHeader } from '@/components/page-header'
import { RequirePermission } from '@/components/require-permission'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { EntityFormDialog, type EntityField } from '@/components/entity-form-dialog'
import { Skeleton } from '@/components/ui/skeleton'

const policySchema = z.object({
  name: z.string().min(1, 'Name is required').max(255),
  program_version_id: z.string().optional(),
  is_default: z.boolean().optional(),
  description: z.string().optional(),
})

const bandSchema = z.object({
  letter_grade: z.string().min(1, 'Letter grade is required').max(5),
  min_percentage: z.coerce.number(),
  max_percentage: z.coerce.number(),
  grade_point: z.union([z.coerce.number(), z.literal('')]).optional(),
  sequence: z.coerce.number().int(),
})

export function GradingPage() {
  const { hasPermission } = useAuth()
  const canManage = hasPermission('grading.manage')
  const { options: pvOptions } = useProgramVersionOptions()
  const [createPolicyOpen, setCreatePolicyOpen] = React.useState(false)

  const {
    data: policies,
    isLoading,
    error,
  } = useEntityList<GradingPolicy>(['grading', 'policies'], '/grading/policies')
  const createPolicy = useEntityCreate<Record<string, unknown>, GradingPolicy>(
    '/grading/policies',
    [['grading', 'policies']],
  )

  const policyFields: EntityField[] = [
    { name: 'name', label: 'Name', type: 'text' },
    {
      name: 'program_version_id',
      label: 'Program version (optional — leave blank for institution-wide)',
      type: 'select',
      options: pvOptions,
    },
    { name: 'is_default', label: 'Default policy', type: 'checkbox' },
    { name: 'description', label: 'Description', type: 'textarea' },
  ]

  return (
    <RequirePermission anyOf={['grading.view']}>
      <PageHeader
        title="Grading"
        description="Grading policies and their letter-grade bands."
        actions={
          canManage ? (
            <Button size="sm" onClick={() => setCreatePolicyOpen(true)}>
              <Plus className="size-4" /> New policy
            </Button>
          ) : undefined
        }
      />

      {isLoading ? (
        <div className="flex flex-col gap-2 rounded-md border p-4">
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
          <Skeleton className="h-10 w-full" />
        </div>
      ) : error ? (
        <div className="flex items-center gap-2 rounded-md border border-destructive/30 bg-destructive/5 px-4 py-3 text-sm text-destructive">
          <AlertCircle className="size-4 shrink-0" />
          Failed to load grading policies.
        </div>
      ) : !policies || policies.length === 0 ? (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center gap-3 py-12 text-center">
            <div className="flex size-12 items-center justify-center rounded-full bg-muted">
              <Inbox className="size-6 text-muted-foreground" />
            </div>
            <div className="space-y-1">
              <p className="font-medium">No grading policies yet</p>
              <p className="max-w-sm text-sm text-muted-foreground">
                {canManage
                  ? 'Create a policy to define letter-grade bands for your programs.'
                  : 'Grading policies will appear here once they are created.'}
              </p>
            </div>
          </CardContent>
        </Card>
      ) : (
        <Accordion type="multiple" className="rounded-md border px-4">
          {policies.map((policy) => (
            <PolicyItem key={policy.id} policy={policy} canManage={canManage} />
          ))}
        </Accordion>
      )}

      <EntityFormDialog
        open={createPolicyOpen}
        onOpenChange={setCreatePolicyOpen}
        title="New grading policy"
        fields={policyFields}
        schema={policySchema}
        defaultValues={{
          name: '',
          program_version_id: '',
          is_default: false,
          description: '',
        }}
        onSubmit={async (values) => {
          try {
            await createPolicy.mutateAsync({
              name: values.name,
              program_version_id: values.program_version_id || null,
              is_default: Boolean(values.is_default),
              description: values.description || null,
            })
            toast.success('Grading policy created')
          } catch (err) {
            throw err instanceof ApiError
              ? err
              : new ApiError('Unable to create grading policy.')
          }
        }}
      />
    </RequirePermission>
  )
}

function PolicyItem({
  policy,
  canManage,
}: {
  policy: GradingPolicy
  canManage: boolean
}) {
  const [createBandOpen, setCreateBandOpen] = React.useState(false)
  const { data: bands, isLoading } = useEntityList<GradingBand>(
    ['grading', 'bands', policy.id],
    '/grading/bands',
    { grading_policy_id: policy.id },
  )
  const createBand = useEntityCreate<Record<string, unknown>, GradingBand>(
    '/grading/bands',
    [['grading', 'bands', policy.id]],
  )
  const removeBand = useEntityDelete(
    (id) => `/grading/bands/${id}`,
    [['grading', 'bands', policy.id]],
  )

  const bandFields: EntityField[] = [
    { name: 'letter_grade', label: 'Letter grade', type: 'text', placeholder: 'e.g. A+' },
    { name: 'min_percentage', label: 'Min %', type: 'number', step: '0.01' },
    { name: 'max_percentage', label: 'Max %', type: 'number', step: '0.01' },
    { name: 'grade_point', label: 'Grade point', type: 'number', step: '0.01' },
    { name: 'sequence', label: 'Sequence', type: 'number' },
  ]

  const sortedBands = [...(bands ?? [])].sort((a, b) => a.sequence - b.sequence)

  return (
    <AccordionItem value={policy.id}>
      <AccordionTrigger>
        <div className="flex flex-1 items-center gap-2 pr-2 text-left">
          <span className="font-display font-semibold">{policy.name}</span>
          {policy.is_default && (
            <Badge variant="secondary" className="font-normal">
              Default
            </Badge>
          )}
          {policy.description && (
            <span className="truncate text-xs text-muted-foreground">
              {policy.description}
            </span>
          )}
        </div>
      </AccordionTrigger>
      <AccordionContent>
        <div className="flex flex-col gap-3 pb-2">
          <div className="flex justify-end">
            {canManage && (
              <Button size="sm" variant="outline" onClick={() => setCreateBandOpen(true)}>
                <Plus className="size-4" /> Add band
              </Button>
            )}
          </div>

          {isLoading ? (
            <div className="flex flex-col gap-1.5">
              <Skeleton className="h-8 w-full" />
              <Skeleton className="h-8 w-full" />
              <Skeleton className="h-8 w-full" />
            </div>
          ) : sortedBands.length === 0 ? (
            <div className="flex flex-col items-center gap-2 rounded-md border border-dashed py-8 text-center text-muted-foreground">
              <Inbox className="size-5 opacity-50" />
              <span className="text-sm">No bands defined yet.</span>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Grade</TableHead>
                  <TableHead>Min %</TableHead>
                  <TableHead>Max %</TableHead>
                  <TableHead>Grade point</TableHead>
                  {canManage && <TableHead className="w-px" />}
                </TableRow>
              </TableHeader>
              <TableBody>
                {sortedBands.map((b) => {
                  // Administrative grades (I/W/AW) use a -1/-1 sentinel
                  // range — they're assigned instead of a mark, not earned
                  // within one — see the seed script that created them.
                  const isAdministrative = Number(b.min_percentage) < 0
                  return (
                    <TableRow key={b.id}>
                      <TableCell className="font-medium">{b.letter_grade}</TableCell>
                      <TableCell>{isAdministrative ? '—' : b.min_percentage}</TableCell>
                      <TableCell>{isAdministrative ? '—' : b.max_percentage}</TableCell>
                      <TableCell>{b.grade_point ?? '—'}</TableCell>
                      {canManage && (
                        <TableCell>
                          <ConfirmAction
                            trigger={
                              <Button
                                size="sm"
                                variant="ghost"
                                aria-label={`Delete band ${b.letter_grade}`}
                                className="text-muted-foreground hover:text-destructive"
                              >
                                <Trash2 className="size-4" />
                              </Button>
                            }
                            title={`Delete band ${b.letter_grade}?`}
                            onConfirm={async () => {
                              try {
                                await removeBand.mutateAsync(b.id)
                                toast.success('Band deleted')
                              } catch (err) {
                                toast.error(
                                  err instanceof ApiError
                                    ? err.detail
                                    : 'Unable to delete band.',
                                )
                              }
                            }}
                          />
                        </TableCell>
                      )}
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          )}
        </div>

        <EntityFormDialog
          open={createBandOpen}
          onOpenChange={setCreateBandOpen}
          title={`New band for ${policy.name}`}
          fields={bandFields}
          schema={bandSchema}
          defaultValues={{
            letter_grade: '',
            min_percentage: '',
            max_percentage: '',
            grade_point: '',
            sequence: (sortedBands.length ?? 0) + 1,
          }}
          onSubmit={async (values) => {
            try {
              await createBand.mutateAsync({
                grading_policy_id: policy.id,
                letter_grade: values.letter_grade,
                min_percentage: values.min_percentage,
                max_percentage: values.max_percentage,
                grade_point: values.grade_point === '' ? null : values.grade_point,
                sequence: values.sequence,
              })
              toast.success('Band created')
            } catch (err) {
              throw err instanceof ApiError ? err : new ApiError('Unable to create band.')
            }
          }}
        />
      </AccordionContent>
    </AccordionItem>
  )
}
