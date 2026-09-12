import * as React from 'react'
import { Pencil, Plus } from 'lucide-react'
import { toast } from 'sonner'

import type { Course } from '@/features/curriculum/types'
import type { AppUser, Permission, Program, Role, UserRoleGrant } from '@/features/organization/types'
import { ApiError, apiClient } from '@/lib/api-client'
import { useEntityList } from '@/lib/crud-hooks'
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
import { NestedTabs } from '@/components/nested-tabs'
import { RoleFormDialog } from '@/features/organization/RoleFormDialog'
import { RolesListTab } from '@/features/organization/RolesListTab'
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
function RoleMatrixGridPanel() {
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

/** The users×roles checkbox grid plus, as a second nested tab, a plainer
 * roles-first list (name/description/permission-count, editable, "fetch
 * default roles") — Institute Settings feedback: "Role matrix is ok,
 * however, a new tab as Roles ... needs to be introduced." Both tabs share
 * the same underlying `roles` data/cache key. */
export function RoleMatrixTab() {
  return (
    <NestedTabs
      items={[
        { value: 'matrix', label: 'Role matrix', content: <RoleMatrixGridPanel /> },
        { value: 'roles', label: 'Roles', content: <RolesListTab /> },
      ]}
    />
  )
}
