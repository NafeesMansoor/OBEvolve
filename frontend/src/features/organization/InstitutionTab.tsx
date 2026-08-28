import * as React from 'react'
import { Pencil } from 'lucide-react'
import { toast } from 'sonner'
import { z } from 'zod'

import { useAuth } from '@/features/auth/useAuth'
import { CampusesTab } from '@/features/organization/CampusesTab'
import { ApiError } from '@/lib/api-client'
import { useEntityGet, useEntityUpdate } from '@/lib/crud-hooks'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { EntityFormDialog, type EntityField } from '@/components/entity-form-dialog'
import { Skeleton } from '@/components/ui/skeleton'

interface InstitutionDetail {
  id: string
  name: string
  code: string
  slug: string
  schema_name: string
  status: string
  subscription_plan: string | null
  contact_email: string
  logo_url: string | null
  timezone: string
  created_at: string
  updated_at: string
}

const editSchema = z.object({
  name: z.string().min(1, 'Name is required').max(255),
  contact_email: z.string().min(1, 'Contact email is required').email('Enter a valid email'),
  timezone: z.string().min(1, 'Timezone is required'),
  logo_url: z.string().optional(),
})

const editFields: EntityField[] = [
  { name: 'name', label: 'Institution name', type: 'text' },
  { name: 'contact_email', label: 'Contact email', type: 'text' },
  { name: 'timezone', label: 'Timezone', type: 'text', placeholder: 'e.g. Asia/Dhaka' },
  { name: 'logo_url', label: 'Logo URL', type: 'text' },
]

/** "Institution" folds in what used to be two separate top-level admin
 * concerns: the institution's own identity/contact details (new — there
 * was no tenant-facing way to see or edit these before, only the
 * platform-admin-only /institutions surface) and Campuses, which
 * structurally sit directly under one institution and never needed their
 * own top-level tab to begin with. */
export function InstitutionTab() {
  const { hasPermission } = useAuth()
  const canManage = hasPermission('institution.manage')
  const [editOpen, setEditOpen] = React.useState(false)

  const { data: institution, isLoading, error } = useEntityGet<InstitutionDetail>(
    ['org', 'institution'],
    '/org/institution',
  )
  const update = useEntityUpdate<Record<string, unknown>, InstitutionDetail>(
    () => '/org/institution',
    [['org', 'institution']],
  )

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Institution</CardTitle>
          {canManage && institution && (
            <Button size="sm" variant="outline" onClick={() => setEditOpen(true)}>
              <Pencil className="size-4" /> Edit
            </Button>
          )}
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <dl className="grid grid-cols-2 gap-x-8 gap-y-3 text-sm">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="flex flex-col gap-1.5">
                  <Skeleton className="h-3 w-20" />
                  <Skeleton className="h-4 w-32" />
                </div>
              ))}
            </dl>
          ) : error || !institution ? (
            <p className="text-sm text-destructive">Failed to load institution details.</p>
          ) : (
            <dl className="grid grid-cols-2 gap-x-8 gap-y-3 text-sm">
              <div>
                <dt className="text-muted-foreground">Name</dt>
                <dd className="font-medium">{institution.name}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Code</dt>
                <dd className="font-medium">{institution.code}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Contact email</dt>
                <dd className="font-medium">{institution.contact_email}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Timezone</dt>
                <dd className="font-medium">{institution.timezone}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Status</dt>
                <dd className="font-medium capitalize">{institution.status}</dd>
              </div>
              <div>
                <dt className="text-muted-foreground">Subscription plan</dt>
                <dd className="font-medium">{institution.subscription_plan ?? '—'}</dd>
              </div>
            </dl>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Campuses</CardTitle>
        </CardHeader>
        <CardContent>
          <CampusesTab />
        </CardContent>
      </Card>

      {institution && (
        <EntityFormDialog
          open={editOpen}
          onOpenChange={setEditOpen}
          title="Edit institution"
          fields={editFields}
          schema={editSchema}
          defaultValues={{
            name: institution.name,
            contact_email: institution.contact_email,
            timezone: institution.timezone,
            logo_url: institution.logo_url ?? '',
          }}
          onSubmit={async (values) => {
            try {
              await update.mutateAsync({
                id: '',
                body: {
                  name: values.name,
                  contact_email: values.contact_email,
                  timezone: values.timezone,
                  logo_url: values.logo_url || null,
                },
              })
              toast.success('Institution updated')
            } catch (err) {
              throw err instanceof ApiError ? err : new ApiError('Unable to update institution.')
            }
          }}
        />
      )}
    </div>
  )
}
