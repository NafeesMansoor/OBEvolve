import * as React from 'react'
import { Pencil, Plus } from 'lucide-react'
import { toast } from 'sonner'

import type { Course } from '@/features/curriculum/types'
import type {
  AppUser,
  Permission,
  Program,
  Role,
  RoleCreateInput,
  RoleUpdateInput,
  UserRoleGrant,
} from '@/features/organization/types'
import { ApiError, apiClient } from '@/lib/api-client'
import { useEntityCreate, useEntityList, useEntityUpdate } from '@/lib/crud-hooks'
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'

/** Roles whose real-world meaning is "for one program" / "for one course"
 * (see app.seed.default_roles's per-role docstrings) — checking one of
 * these opens a multi-select popup instead of granting immediately,
 * because the grant is meaningless without a scope. Everything else grants
 * institution-wide on check / revokes on uncheck. */
const PROGRAM_SCOPED_ROLE_NAMES = new Set(['Program Administrator', 'Program Coordinator'])
const COURSE_SCOPED_ROLE_NAMES = new Set(['Section Coordinator'])

function scopeKindFor(roleName: string): 'program' | 'course' | 'institution' {
  if (PROGRAM_SCOPED_ROLE_NAMES.has(roleName)) return 'program'
  if (COURSE_SCOPED_ROLE_NAMES.has(roleName)) return 'course'
  return 'institution'
}

/** Institution Administrator's faculty/role management, as a checkbox
 * matrix (users x roles) rather than the per-user "Roles" dialog in
 * UsersTab — a quicker way to see and change who holds what across
 * everyone at once. Checking a program/course-scoped role (Program
 * Coordinator, Section Coordinator, ...) opens a popup to pick one or more
 * programs/courses in a single action; unchecking removes every grant of
 * that role for that user, scoped or not.
 *
 * Note: this is the institution-wide surface only — a Program
 * Administrator/Coordinator cannot yet manage roles scoped to just their
 * own program from here, because `role.manage`/`user.view` aren't granted
 * to those roles today and `require_permission` has no notion of "scoped
 * to the caller's own program" for this resource (see
 * app.services.rbac.require_permission's docstring on scope_type
 * matching). Extending that is a backend RBAC change, not a frontend one —
 * flagged separately rather than built here without that groundwork. */
export function RoleMatrixTab() {
  const [search, setSearch] = React.useState('')
  const [scopePopup, setScopePopup] = React.useState<{
    user: AppUser
    role: Role
    kind: 'program' | 'course'
  } | null>(null)
  const [creatingRole, setCreatingRole] = React.useState(false)
  const [editingRole, setEditingRole] = React.useState<Role | null>(null)

  const { data: users, isLoading } = useEntityList<AppUser>(['users'], '/users')
  const { data: roles } = useEntityList<Role>(['roles'], '/users/roles/all')
  const { data: permissions } = useEntityList<Permission>(['permissions'], '/users/permissions')
  const { data: grants, refetch: refetchGrants } = useEntityList<UserRoleGrant>(
    ['users', 'user-roles'],
    '/users/user-roles',
  )
  const { data: programs } = useEntityList<Program>(['org', 'programs'], '/org/programs')
  const { data: courses } = useEntityList<Course>(['curriculum', 'courses'], '/curriculum/courses')

  const programById = React.useMemo(() => new Map((programs ?? []).map((p) => [p.id, p])), [programs])
  const courseById = React.useMemo(() => new Map((courses ?? []).map((c) => [c.id, c])), [courses])

  const filteredUsers = React.useMemo(() => {
    const q = search.trim().toLowerCase()
    if (!q) return users ?? []
    return (users ?? []).filter(
      (u) => u.full_name.toLowerCase().includes(q) || u.email.toLowerCase().includes(q),
    )
  }, [users, search])

  function grantsFor(userId: string, roleId: string): UserRoleGrant[] {
    return (grants ?? []).filter((g) => g.user_id === userId && g.role_id === roleId)
  }

  async function grantUnscoped(user: AppUser, role: Role) {
    try {
      await apiClient.post('/users/user-roles', {
        user_id: user.id, role_id: role.id, scope_type: null, scope_id: null,
      })
      await refetchGrants()
      toast.success(`${role.name} granted to ${user.full_name}`)
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Unable to grant role.')
    }
  }

  async function revokeAll(user: AppUser, role: Role) {
    const existing = grantsFor(user.id, role.id)
    try {
      await Promise.all(existing.map((g) => apiClient.delete(`/users/user-roles/${g.id}`)))
      await refetchGrants()
      toast.success(`${role.name} revoked from ${user.full_name}`)
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Unable to revoke role.')
    }
  }

  function toggle(user: AppUser, role: Role, checked: boolean) {
    const kind = scopeKindFor(role.name)
    if (!checked) {
      void revokeAll(user, role)
      return
    }
    if (kind === 'institution') {
      void grantUnscoped(user, role)
      return
    }
    setScopePopup({ user, role, kind })
  }

  const columns = (roles ?? []).length

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between gap-3">
        <Input
          placeholder="Search users…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="max-w-sm"
        />
        <Button size="sm" onClick={() => setCreatingRole(true)}>
          <Plus className="size-4" />
          New role type
        </Button>
      </div>

      {isLoading || !roles ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : (
        <div className="overflow-x-auto rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="sticky left-0 bg-background">User</TableHead>
                {roles.map((r) => (
                  <TableHead key={r.id} className="whitespace-nowrap text-center">
                    <div className="flex items-center justify-center gap-1">
                      {r.name}
                      {!r.is_system_role && (
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <button
                              type="button"
                              aria-label={`Edit ${r.name}`}
                              className="text-muted-foreground hover:text-foreground"
                              onClick={() => setEditingRole(r)}
                            >
                              <Pencil className="size-3" />
                            </button>
                          </TooltipTrigger>
                          <TooltipContent>Edit this custom role</TooltipContent>
                        </Tooltip>
                      )}
                    </div>
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredUsers.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={columns + 1} className="text-center text-muted-foreground">
                    No users found.
                  </TableCell>
                </TableRow>
              ) : (
                filteredUsers.map((u) => (
                  <TableRow key={u.id}>
                    <TableCell className="sticky left-0 bg-background">
                      <div className="flex flex-col">
                        <span className="font-medium">{u.full_name}</span>
                        <span className="text-xs text-muted-foreground">{u.email}</span>
                      </div>
                    </TableCell>
                    {roles.map((r) => {
                      const held = grantsFor(u.id, r.id)
                      const kind = scopeKindFor(r.name)
                      const scopeLabels =
                        kind === 'program'
                          ? held.map((g) => programById.get(g.scope_id ?? '')?.name ?? '?')
                          : kind === 'course'
                            ? held.map((g) => courseById.get(g.scope_id ?? '')?.code ?? '?')
                            : []
                      const checkbox = (
                        <Checkbox
                          checked={held.length > 0}
                          onCheckedChange={(checked) => toggle(u, r, checked === true)}
                        />
                      )
                      return (
                        <TableCell key={r.id} className="text-center">
                          {scopeLabels.length > 0 ? (
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <span className="inline-flex">{checkbox}</span>
                              </TooltipTrigger>
                              <TooltipContent>{scopeLabels.join(', ')}</TooltipContent>
                            </Tooltip>
                          ) : (
                            checkbox
                          )}
                        </TableCell>
                      )
                    })}
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      )}

      {scopePopup && (
        <ScopePickerDialog
          user={scopePopup.user}
          role={scopePopup.role}
          kind={scopePopup.kind}
          options={
            scopePopup.kind === 'program'
              ? (programs ?? []).map((p) => ({ id: p.id, label: `${p.name} (${p.code})` }))
              : (courses ?? []).map((c) => ({ id: c.id, label: `${c.code} — ${c.title}` }))
          }
          alreadyGranted={
            new Set(grantsFor(scopePopup.user.id, scopePopup.role.id).map((g) => g.scope_id ?? ''))
          }
          onClose={() => setScopePopup(null)}
          onConfirm={async (selectedIds) => {
            try {
              await Promise.all(
                selectedIds.map((scopeId) =>
                  apiClient.post('/users/user-roles', {
                    user_id: scopePopup.user.id,
                    role_id: scopePopup.role.id,
                    scope_type: scopePopup.kind,
                    scope_id: scopeId,
                  }),
                ),
              )
              await refetchGrants()
              toast.success(
                `${scopePopup.role.name} granted to ${scopePopup.user.full_name} for ${selectedIds.length} ${scopePopup.kind}${selectedIds.length === 1 ? '' : 's'}`,
              )
              setScopePopup(null)
            } catch (err) {
              toast.error(err instanceof ApiError ? err.detail : 'Unable to grant role.')
            }
          }}
        />
      )}

      {creatingRole && (
        <RoleFormDialog
          permissions={permissions ?? []}
          onClose={() => setCreatingRole(false)}
        />
      )}

      {editingRole && (
        <RoleFormDialog
          role={editingRole}
          permissions={permissions ?? []}
          onClose={() => setEditingRole(null)}
        />
      )}
    </div>
  )
}

/** Create (no `role` prop) or edit (custom roles only — callers never pass a
 * system role here) a tenant-scoped "user type." Always institution-local:
 * `POST /users/roles` creates a plain row in THIS tenant's own `roles`
 * table, structurally invisible to every other institution and to the
 * platform-level default-role catalogue (schema-per-institution) — an
 * institution can compose its own role from the fixed permission
 * catalogue, but never touch what the platform seeds by default. */
function RoleFormDialog({
  role,
  permissions,
  onClose,
}: {
  role?: Role
  permissions: Permission[]
  onClose: () => void
}) {
  const [name, setName] = React.useState(role?.name ?? '')
  const [description, setDescription] = React.useState(role?.description ?? '')
  const [selectedCodes, setSelectedCodes] = React.useState<Set<string>>(
    new Set(role?.permission_codes ?? []),
  )
  const [submitting, setSubmitting] = React.useState(false)

  const createRole = useEntityCreate<RoleCreateInput, Role>('/users/roles', [['roles']])
  const updateRole = useEntityUpdate<RoleUpdateInput, Role>(
    (id) => `/users/roles/${id}`,
    [['roles']],
  )

  const modules = React.useMemo(() => {
    const byModule = new Map<string, Permission[]>()
    for (const p of permissions) {
      const list = byModule.get(p.module) ?? []
      list.push(p)
      byModule.set(p.module, list)
    }
    return Array.from(byModule.entries()).sort(([a], [b]) => a.localeCompare(b))
  }, [permissions])

  function toggleCode(code: string) {
    setSelectedCodes((prev) => {
      const next = new Set(prev)
      if (next.has(code)) next.delete(code)
      else next.add(code)
      return next
    })
  }

  async function handleSubmit() {
    if (!name.trim()) {
      toast.error('Name is required.')
      return
    }
    setSubmitting(true)
    try {
      if (role) {
        await updateRole.mutateAsync({
          id: role.id,
          body: {
            name: name.trim(),
            description: description.trim() || null,
            permission_codes: Array.from(selectedCodes),
          },
        })
        toast.success(`${name.trim()} updated.`)
      } else {
        await createRole.mutateAsync({
          name: name.trim(),
          description: description.trim() || null,
          permission_codes: Array.from(selectedCodes),
        })
        toast.success(`${name.trim()} created.`)
      }
      onClose()
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Unable to save role.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{role ? `Edit ${role.name}` : 'New role type'}</DialogTitle>
          <DialogDescription>
            {role
              ? 'Custom roles can be renamed and re-permissioned freely — system roles cannot.'
              : "A new user type scoped to this institution only — it won't appear for any other institution, and the platform's default role catalogue is unaffected."}
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-3">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="role-name">Name</Label>
            <Input
              id="role-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Lab Coordinator"
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="role-description">Description</Label>
            <Textarea
              id="role-description"
              value={description ?? ''}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What this role is for"
              rows={2}
            />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label>Permissions ({selectedCodes.size} selected)</Label>
            <div className="max-h-72 overflow-y-auto rounded-md border">
              <Accordion type="multiple" className="w-full">
                {modules.map(([moduleName, modulePermissions]) => (
                  <AccordionItem key={moduleName} value={moduleName}>
                    <AccordionTrigger className="px-3 text-sm capitalize">
                      {moduleName.replace(/_/g, ' ')}
                    </AccordionTrigger>
                    <AccordionContent className="flex flex-col gap-1 px-3">
                      {modulePermissions.map((p) => (
                        <label
                          key={p.code}
                          className="flex cursor-pointer items-start gap-2 rounded-md p-1.5 text-sm hover:bg-muted"
                        >
                          <Checkbox
                            checked={selectedCodes.has(p.code)}
                            onCheckedChange={() => toggleCode(p.code)}
                            className="mt-0.5"
                          />
                          <span className="flex flex-col">
                            <span className="font-mono text-xs">{p.code}</span>
                            <span className="text-xs text-muted-foreground">{p.description}</span>
                          </span>
                        </label>
                      ))}
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            </div>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={submitting}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={submitting}>
            {submitting ? 'Saving…' : role ? 'Save changes' : 'Create role'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function ScopePickerDialog({
  user,
  role,
  kind,
  options,
  alreadyGranted,
  onClose,
  onConfirm,
}: {
  user: AppUser
  role: Role
  kind: 'program' | 'course'
  options: { id: string; label: string }[]
  alreadyGranted: Set<string>
  onClose: () => void
  onConfirm: (selectedIds: string[]) => void | Promise<void>
}) {
  const [selected, setSelected] = React.useState<Set<string>>(new Set())
  const [submitting, setSubmitting] = React.useState(false)
  const selectable = options.filter((o) => !alreadyGranted.has(o.id))

  function toggleOption(id: string) {
    setSelected((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>
            {role.name} — select {kind === 'program' ? 'programs' : 'courses'}
          </DialogTitle>
          <DialogDescription>
            {user.full_name} will be granted {role.name} for every {kind} selected below. You can
            select more than one.
          </DialogDescription>
        </DialogHeader>
        <div className="flex max-h-72 flex-col gap-1 overflow-y-auto">
          {selectable.length === 0 ? (
            <p className="py-4 text-center text-sm text-muted-foreground">
              Already granted for every {kind}.
            </p>
          ) : (
            selectable.map((o) => (
              <label
                key={o.id}
                className="flex cursor-pointer items-center gap-2 rounded-md p-2 text-sm hover:bg-muted"
              >
                <Checkbox
                  checked={selected.has(o.id)}
                  onCheckedChange={() => toggleOption(o.id)}
                />
                {o.label}
              </label>
            ))
          )}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={submitting}>
            Cancel
          </Button>
          <Button
            disabled={selected.size === 0 || submitting}
            onClick={async () => {
              setSubmitting(true)
              await onConfirm(Array.from(selected))
              setSubmitting(false)
            }}
          >
            Grant ({selected.size})
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
