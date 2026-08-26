import * as React from 'react'
import { Plus, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { z } from 'zod'

import { useAuth } from '@/features/auth/useAuth'
import type { AssessmentType } from '@/features/assessment/types'
import { ApiError } from '@/lib/api-client'
import { useEntityCreate, useEntityDelete, useEntityList } from '@/lib/crud-hooks'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ConfirmAction } from '@/components/confirm-action'
import { DataTable, type DataTableColumn } from '@/components/data-table'
import { EntityFormDialog, type EntityField } from '@/components/entity-form-dialog'

const schema = z.object({ name: z.string().min(1, 'Name is required').max(100) })
const fields: EntityField[] = [{ name: 'name', label: 'Name', type: 'text' }]

/** 13 defaults (Quiz, Class Test, Assignment, ...) are seeded per tenant and
 * blocked from deletion server-side — the delete button stays visible for
 * everything (including defaults) and just surfaces the server's error
 * message if it 4xxs, per the task brief. */
export function TypesTab() {
  const { hasPermission } = useAuth()
  const canManage = hasPermission('assessment.create')
  const [createOpen, setCreateOpen] = React.useState(false)

  const { data, isLoading, error } = useEntityList<AssessmentType>(
    ['assessment', 'types'],
    '/assessment/types',
  )
  const create = useEntityCreate<Record<string, unknown>, AssessmentType>('/assessment/types', [
    ['assessment', 'types'],
  ])
  const remove = useEntityDelete((id) => `/assessment/types/${id}`, [['assessment', 'types']])

  const columns: DataTableColumn<AssessmentType>[] = [
    { key: 'name', header: 'Name', render: (r) => r.name, searchValue: (r) => r.name },
    {
      key: 'is_custom',
      header: 'Origin',
      render: (r) => (
        <Badge variant={r.is_custom ? 'secondary' : 'outline'} className="font-normal">
          {r.is_custom ? 'Custom' : 'Default'}
        </Badge>
      ),
    },
  ]

  return (
    <div className="flex flex-col gap-4">
      <div className="flex justify-end">
        {canManage && (
          <Button size="sm" onClick={() => setCreateOpen(true)}>
            <Plus className="size-4" /> New type
          </Button>
        )}
      </div>

      <DataTable
        data={data}
        columns={columns}
        rowKey={(r) => r.id}
        isLoading={isLoading}
        error={error}
        searchable
        emptyMessage="No assessment types yet."
        actions={
          canManage
            ? (r) => (
                <ConfirmAction
                  trigger={
                    <Button size="sm" variant="ghost">
                      <Trash2 className="size-4" />
                    </Button>
                  }
                  title={`Delete assessment type "${r.name}"?`}
                  onConfirm={async () => {
                    try {
                      await remove.mutateAsync(r.id)
                      toast.success('Assessment type deleted')
                    } catch (err) {
                      toast.error(
                        err instanceof ApiError
                          ? err.detail
                          : 'Unable to delete this assessment type.',
                      )
                    }
                  }}
                />
              )
            : undefined
        }
      />

      <EntityFormDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        title="New assessment type"
        fields={fields}
        schema={schema}
        defaultValues={{ name: '' }}
        onSubmit={async (values) => {
          try {
            await create.mutateAsync(values)
            toast.success('Assessment type created')
          } catch (err) {
            throw err instanceof ApiError ? err : new ApiError('Unable to create assessment type.')
          }
        }}
      />
    </div>
  )
}
