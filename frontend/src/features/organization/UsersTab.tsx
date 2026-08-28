import * as React from 'react'
import { Plus, X } from 'lucide-react'
import { toast } from 'sonner'
import { z } from 'zod'

import { useAuth } from '@/features/auth/useAuth'
import type { Course } from '@/features/curriculum/types'
import type { AppUser, Program, Role, UserRoleGrant } from '@/features/organization/types'
import { ApiError, apiClient } from '@/lib/api-client'
import { useEntityCreate, useEntityList, useEntityUpdate } from '@/lib/crud-hooks'
import { useResetOnChange } from '@/lib/use-reset-on-change'
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { DataTable, type DataTableColumn } from '@/components/data-table'
import { EntityFormDialog, type EntityField } from '@/components/entity-form-dialog'
import { RecordDetailSheet } from '@/components/record-detail-sheet'

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

function RolesCell({ user, roles, grants }: { user: AppUser; roles: Role[]; grants: UserRoleGrant[] }) {
  const roleById = React.useMemo(() => new Map(roles.map((r) => [r.id, r])), [roles])
  const userGrants = grants.filter((g) => g.user_id === user.id)

  if (userGrants.length === 0) {
    return <span className="text-xs text-muted-foreground">No roles assigned</span>
  }
  return (
    <div className="flex flex-wrap gap-1">
      {userGrants.map((g) => (
        <Badge key={g.id} variant="secondary" className="font-normal">
          {roleById.get(g.role_id)?.name ?? 'Unknown role'}
          {g.scope_type ? ` (${g.scope_type})` : ''}
        </Badge>
      ))}
    </div>
  )
}

/** Users + role assignment, including scoped grants (Program
 * Administrator/Coordinator, Course Administrator) — previously these
 * could only be created institution-wide from this console, since the
 * assign form never offered a scope_type/scope_id at all even though the
 * backend has always accepted them (app/schemas/identity.py
 * UserRoleCreate). See RolesDialog's secondary tabs below. */
export function UsersTab() {
  const { hasPermission, user: currentUser } = useAuth()
  const canManageUsers = hasPermission('user.manage')
  const canManageRoles = hasPermission('role.manage')

  const [createOpen, setCreateOpen] = React.useState(false)
  const [editUser, setEditUser] = React.useState<AppUser | null>(null)
  const [rolesUser, setRolesUser] = React.useState<AppUser | null>(null)
  const [viewUser, setViewUser] = React.useState<AppUser | null>(null)

  const { data: users, isLoading, error } = useEntityList<AppUser>(['users'], '/users')
  const { data: roles } = useEntityList<Role>(['roles'], '/users/roles/all', undefined, {
    enabled: hasPermission('role.view'),
  })
  const { data: grants, refetch: refetchGrants } = useEntityList<UserRoleGrant>(
    ['users', 'user-roles'],
    '/users/user-roles',
    undefined,
    { enabled: hasPermission('role.view') },
  )

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
      render: (r) => <RolesCell user={r} roles={roles ?? []} grants={grants ?? []} />,
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
        onRowClick={(r) => setViewUser(r)}
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

      {viewUser && (
        <RecordDetailSheet
          open={Boolean(viewUser)}
          onOpenChange={(open) => !open && setViewUser(null)}
          title={viewUser.full_name}
          subtitle={viewUser.email}
          badge={
            <Badge variant={viewUser.is_active ? 'secondary' : 'outline'} className="font-normal">
              {viewUser.is_active ? 'Active' : 'Inactive'}
            </Badge>
          }
          fields={[
            { label: 'Email', value: viewUser.email },
            { label: 'Status', value: viewUser.is_active ? 'Active' : 'Inactive' },
            {
              label: 'Roles',
              value: <RolesCell user={viewUser} roles={roles ?? []} grants={grants ?? []} />,
              full: true,
            },
          ]}
          onEdit={
            canManageUsers
              ? () => {
                  setEditUser(viewUser)
                  setViewUser(null)
                }
              : undefined
          }
        >
          {canManageRoles && (
            <Button
              size="sm"
              variant="outline"
              className="self-start"
              onClick={() => {
                setRolesUser(viewUser)
                setViewUser(null)
              }}
            >
              Manage roles
            </Button>
          )}
        </RecordDetailSheet>
      )}

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
          grants={(grants ?? []).filter((g) => g.user_id === rolesUser.id)}
          currentUserId={currentUser?.id}
          onClose={() => setRolesUser(null)}
          onChanged={() => void refetchGrants()}
        />
      )}
    </div>
  )
}

type ScopeCategory = 'institution' | 'program' | 'course'

function RolesDialog({
  targetUser,
  roles,
  grants,
  currentUserId,
  onClose,
  onChanged,
}: {
  targetUser: AppUser
  roles: Role[]
  grants: UserRoleGrant[]
  currentUserId: string | undefined
  onClose: () => void
  onChanged: () => void
}) {
  const roleById = React.useMemo(() => new Map(roles.map((r) => [r.id, r])), [roles])
  const { data: programs } = useEntityList<Program>(['org', 'programs'], '/org/programs')
  const { data: courses } = useEntityList<Course>(['curriculum', 'courses'], '/curriculum/courses')
  const programById = React.useMemo(() => new Map((programs ?? []).map((p) => [p.id, p])), [programs])
  const courseById = React.useMemo(() => new Map((courses ?? []).map((c) => [c.id, c])), [courses])

  function scopeLabel(g: UserRoleGrant): string | null {
    if (!g.scope_type) return null
    if (g.scope_type === 'program') return `Program: ${programById.get(g.scope_id ?? '')?.name ?? '?'}`
    if (g.scope_type === 'course') return `Course: ${courseById.get(g.scope_id ?? '')?.code ?? '?'}`
    return g.scope_type
  }

  async function revoke(grantId: string) {
    try {
      await apiClient.delete(`/users/user-roles/${grantId}`)
      onChanged()
      toast.success('Role revoked')
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Unable to revoke role.')
    }
  }

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Roles for {targetUser.full_name}</DialogTitle>
          <DialogDescription>
            Institution-wide roles apply everywhere; program/course-scoped roles apply only within
            that program or course.
            {targetUser.id === currentUserId
              ? ' This is your own account — changes apply immediately.'
              : ''}
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-3">
          {grants.length === 0 ? (
            <p className="text-sm text-muted-foreground">No roles assigned yet.</p>
          ) : (
            <div className="flex flex-wrap gap-1.5">
              {grants.map((g) => {
                const label = scopeLabel(g)
                return (
                  <Badge key={g.id} variant="secondary" className="gap-1 pr-1 font-normal">
                    {roleById.get(g.role_id)?.name ?? 'Unknown role'}
                    {label ? <span className="text-muted-foreground"> · {label}</span> : null}
                    <button
                      type="button"
                      onClick={() => revoke(g.id)}
                      className="cursor-pointer rounded-full p-0.5 hover:bg-destructive/15 hover:text-destructive focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                      aria-label="Revoke role"
                    >
                      <X className="size-3" />
                    </button>
                  </Badge>
                )
              })}
            </div>
          )}

          <Tabs defaultValue="institution" className="border-t pt-3">
            <TabsList>
              <TabsTrigger value="institution">Institution-wide</TabsTrigger>
              <TabsTrigger value="program">Program</TabsTrigger>
              <TabsTrigger value="course">Course</TabsTrigger>
            </TabsList>
            {(['institution', 'program', 'course'] as ScopeCategory[]).map((category) => (
              <TabsContent key={category} value={category}>
                <AssignForm
                  category={category}
                  targetUser={targetUser}
                  roles={roles}
                  programs={programs ?? []}
                  courses={courses ?? []}
                  onAssigned={onChanged}
                />
              </TabsContent>
            ))}
          </Tabs>
        </div>
      </DialogContent>
    </Dialog>
  )
}

function AssignForm({
  category,
  targetUser,
  roles,
  programs,
  courses,
  onAssigned,
}: {
  category: ScopeCategory
  targetUser: AppUser
  roles: Role[]
  programs: Program[]
  courses: Course[]
  onAssigned: () => void
}) {
  const [roleId, setRoleId] = React.useState('')
  // Reset the scope picker when switching categories — a program id
  // selected under "Program" is meaningless under "Course".
  const [scopeId, setScopeId] = useResetOnChange(category, '')
  const [isSubmitting, setIsSubmitting] = React.useState(false)

  const needsScope = category !== 'institution'
  const canAssign = roleId && (!needsScope || scopeId) && !isSubmitting

  async function assign() {
    setIsSubmitting(true)
    try {
      await apiClient.post('/users/user-roles', {
        user_id: targetUser.id,
        role_id: roleId,
        scope_type: category === 'institution' ? null : category,
        scope_id: category === 'institution' ? null : scopeId,
      })
      setRoleId('')
      setScopeId('')
      onAssigned()
      toast.success('Role assigned')
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Unable to assign role.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="flex flex-col gap-2 pt-2">
      <Select value={roleId} onValueChange={setRoleId}>
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

      {category === 'program' && (
        <Select value={scopeId} onValueChange={setScopeId}>
          <SelectTrigger>
            <SelectValue placeholder="Select a program" />
          </SelectTrigger>
          <SelectContent>
            {programs.map((p) => (
              <SelectItem key={p.id} value={p.id}>
                {p.name} ({p.code})
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}

      {category === 'course' && (
        <Select value={scopeId} onValueChange={setScopeId}>
          <SelectTrigger>
            <SelectValue placeholder="Select a course" />
          </SelectTrigger>
          <SelectContent>
            {courses.map((c) => (
              <SelectItem key={c.id} value={c.id}>
                {c.code} — {c.title}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      )}

      <Button onClick={assign} disabled={!canAssign} className="self-end">
        Assign
      </Button>
    </div>
  )
}
