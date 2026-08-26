import * as React from 'react'
import { Plus, X } from 'lucide-react'
import { toast } from 'sonner'
import { z } from 'zod'

import { useAuth } from '@/features/auth/useAuth'
import {
  addCachedGrant,
  getCachedGrantsForUser,
  removeCachedGrant,
} from '@/features/organization/role-grants-cache'
import type { AppUser, Role, UserRoleGrant } from '@/features/organization/types'
import { ApiError, apiClient } from '@/lib/api-client'
import { useEntityCreate, useEntityList, useEntityUpdate } from '@/lib/crud-hooks'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { DataTable, type DataTableColumn } from '@/components/data-table'
import { EntityFormDialog, type EntityField } from '@/components/entity-form-dialog'

const createSchema = z.object({
  full_name: z.string().min(1, 'Name is required').max(255),
  email: z.string().min(1, 'Email is required').email('Enter a valid email address'),
  password: z.string().min(8, 'Password must be at least 8 characters'),
})

const createFields: EntityField[] = [
  { name: 'full_name', label: 'Full name', type: 'text' },
  { name: 'email', label: 'Email', type: 'text' },
  { name: 'password', label: 'Temporary password', type: 'text', description: 'At least 8 characters.' },
]

const editSchema = z.object({
  full_name: z.string().min(1, 'Name is required').max(255),
  is_active: z.boolean(),
})

const editFields: EntityField[] = [
  { name: 'full_name', label: 'Full name', type: 'text' },
  { name: 'is_active', label: 'Active', type: 'checkbox' },
]

function RolesCell({
  user,
  roles,
  version,
}: {
  user: AppUser
  roles: Role[]
  version: number
}) {
  const roleById = React.useMemo(() => new Map(roles.map((r) => [r.id, r])), [roles])
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const grants = React.useMemo(() => getCachedGrantsForUser(user.id), [user.id, version])

  if (grants.length === 0) {
    return <span className="text-xs text-muted-foreground">No roles assigned here yet</span>
  }
  return (
    <div className="flex flex-wrap gap-1">
      {grants.map((g) => (
        <Badge key={g.id} variant="secondary" className="font-normal">
          {roleById.get(g.role_id)?.name ?? 'Unknown role'}
        </Badge>
      ))}
    </div>
  )
}

/** Users + role assignment. Note: the backend has POST/DELETE for role
 * grants but no GET to list existing ones (app/api/v1/endpoints/users.py),
 * so role badges reflect only grants made through this console in this
 * browser — see role-grants-cache.ts. */
export function UsersTab() {
  const { hasPermission, user: currentUser } = useAuth()
  const canManageUsers = hasPermission('user.manage')
  const canManageRoles = hasPermission('role.manage')

  const [createOpen, setCreateOpen] = React.useState(false)
  const [editUser, setEditUser] = React.useState<AppUser | null>(null)
  const [rolesUser, setRolesUser] = React.useState<AppUser | null>(null)
  const [cacheVersion, setCacheVersion] = React.useState(0)

  const { data: users, isLoading, error } = useEntityList<AppUser>(['users'], '/users')
  const { data: roles } = useEntityList<Role>(['roles'], '/users/roles/all', undefined, {
    enabled: hasPermission('role.view'),
  })

  const createUser = useEntityCreate<Record<string, unknown>, AppUser>('/users', [['users']])
  const updateUser = useEntityUpdate<Record<string, unknown>, AppUser>(
    (id) => `/users/${id}`,
    [['users']],
  )

  const columns: DataTableColumn<AppUser>[] = [
    { key: 'full_name', header: 'Name', render: (r) => r.full_name, searchValue: (r) => r.full_name },
    { key: 'email', header: 'Email', render: (r) => r.email, searchValue: (r) => r.email },
    {
      key: 'is_active',
      header: 'Status',
      render: (r) => (
        <Badge variant={r.is_active ? 'secondary' : 'outline'} className="font-normal">
          {r.is_active ? 'Active' : 'Inactive'}
        </Badge>
      ),
    },
    {
      key: 'roles',
      header: 'Roles',
      render: (r) => <RolesCell user={r} roles={roles ?? []} version={cacheVersion} />,
    },
  ]

  return (
    <div className="flex flex-col gap-4">
      <div className="flex justify-end">
        {canManageUsers && (
          <Button size="sm" onClick={() => setCreateOpen(true)}>
            <Plus className="size-4" /> Add user
          </Button>
        )}
      </div>

      <DataTable
        data={users}
        columns={columns}
        rowKey={(r) => r.id}
        isLoading={isLoading}
        error={error}
        searchable
        searchPlaceholder="Search users…"
        emptyMessage="No users yet."
        actions={(r) => (
          <>
            {canManageUsers && (
              <Button size="sm" variant="outline" onClick={() => setEditUser(r)}>
                Edit
              </Button>
            )}
            {canManageRoles && (
              <Button size="sm" variant="outline" onClick={() => setRolesUser(r)}>
                Roles
              </Button>
            )}
          </>
        )}
      />

      <EntityFormDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        title="Add user"
        description="Creates a new account — e.g. a faculty member or another administrator. Assign a role from the Roles action afterwards."
        fields={createFields}
        schema={createSchema}
        defaultValues={{ full_name: '', email: '', password: '' }}
        onSubmit={async (values) => {
          try {
            await createUser.mutateAsync(values)
            toast.success('User created')
          } catch (err) {
            throw err instanceof ApiError ? err : new ApiError('Unable to create user.')
          }
        }}
      />

      {editUser && (
        <EntityFormDialog
          open={Boolean(editUser)}
          onOpenChange={(open) => !open && setEditUser(null)}
          title={`Edit ${editUser.full_name}`}
          fields={editFields}
          schema={editSchema}
          defaultValues={{ full_name: editUser.full_name, is_active: editUser.is_active }}
          onSubmit={async (values) => {
            try {
              await updateUser.mutateAsync({ id: editUser.id, body: values })
              toast.success('User updated')
            } catch (err) {
              throw err instanceof ApiError ? err : new ApiError('Unable to update user.')
            }
          }}
        />
      )}

      {rolesUser && (
        <RolesDialog
          targetUser={rolesUser}
          roles={roles ?? []}
          currentUserId={currentUser?.id}
          onClose={() => setRolesUser(null)}
          onChanged={() => setCacheVersion((v) => v + 1)}
        />
      )}
    </div>
  )
}

function RolesDialog({
  targetUser,
  roles,
  currentUserId,
  onClose,
  onChanged,
}: {
  targetUser: AppUser
  roles: Role[]
  currentUserId: string | undefined
  onClose: () => void
  onChanged: () => void
}) {
  const [selectedRoleId, setSelectedRoleId] = React.useState<string>('')
  const [isSubmitting, setIsSubmitting] = React.useState(false)
  const [grants, setGrants] = React.useState<UserRoleGrant[]>(() =>
    getCachedGrantsForUser(targetUser.id),
  )
  const roleById = React.useMemo(() => new Map(roles.map((r) => [r.id, r])), [roles])

  async function assign() {
    if (!selectedRoleId) return
    setIsSubmitting(true)
    try {
      const res = await apiClient.post<UserRoleGrant>('/users/user-roles', {
        user_id: targetUser.id,
        role_id: selectedRoleId,
        scope_type: null,
        scope_id: null,
      })
      addCachedGrant(res.data)
      setGrants(getCachedGrantsForUser(targetUser.id))
      setSelectedRoleId('')
      onChanged()
      toast.success('Role assigned')
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Unable to assign role.')
    } finally {
      setIsSubmitting(false)
    }
  }

  async function revoke(grantId: string) {
    try {
      await apiClient.delete(`/users/user-roles/${grantId}`)
      removeCachedGrant(grantId)
      setGrants(getCachedGrantsForUser(targetUser.id))
      onChanged()
      toast.success('Role revoked')
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Unable to revoke role.')
    }
  }

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Roles for {targetUser.full_name}</DialogTitle>
          <DialogDescription>
            Assigned institution-wide (no department/program scoping in this pass).
            {targetUser.id === currentUserId
              ? ' This is your own account — changes apply immediately.'
              : ''}
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-3">
          {grants.length === 0 ? (
            <p className="text-sm text-muted-foreground">
              No roles assigned through this console yet.
            </p>
          ) : (
            <div className="flex flex-wrap gap-1.5">
              {grants.map((g) => (
                <Badge key={g.id} variant="secondary" className="gap-1 pr-1 font-normal">
                  {roleById.get(g.role_id)?.name ?? 'Unknown role'}
                  <button
                    type="button"
                    onClick={() => revoke(g.id)}
                    className="rounded-full p-0.5 hover:bg-muted-foreground/20"
                    aria-label="Revoke role"
                  >
                    <X className="size-3" />
                  </button>
                </Badge>
              ))}
            </div>
          )}

          <div className="flex items-end gap-2 border-t pt-3">
            <div className="flex-1">
              <Select value={selectedRoleId} onValueChange={setSelectedRoleId}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a role to assign" />
                </SelectTrigger>
                <SelectContent>
                  {roles.map((r) => (
                    <SelectItem key={r.id} value={r.id}>
                      {r.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Button onClick={assign} disabled={!selectedRoleId || isSubmitting}>
              Assign
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
