import * as React from 'react'
import { Download, Pencil, Plus } from 'lucide-react'
import { toast } from 'sonner'

import type { Permission, Role, RoleTemplate } from '@/features/organization/types'
import { ApiError, apiClient } from '@/lib/api-client'
import { useEntityList } from '@/lib/crud-hooks'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { RoleFormDialog } from '@/features/organization/RoleFormDialog'

function FetchDefaultRolesDialog({
  existingNames,
  onClose,
  onAdopted,
}: {
  existingNames: Set<string>
  onClose: () => void
  onAdopted: () => void
}) {
  const { data: templates, isLoading } = useEntityList<RoleTemplate>(
    ['role-templates', 'tenant-browse'],
    '/users/role-templates',
  )
  const [adoptingId, setAdoptingId] = React.useState<string | null>(null)

  async function adopt(template: RoleTemplate) {
    setAdoptingId(template.id)
    try {
      await apiClient.post(`/users/roles/from-template/${template.id}`)
      toast.success(`${template.name} added`)
      onAdopted()
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Unable to add role.')
    } finally {
      setAdoptingId(null)
    }
  }

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Default roles</DialogTitle>
          <DialogDescription>
            The platform's standard role catalogue. Add one your institution doesn't currently
            have — it becomes a normal, editable role here afterwards.
          </DialogDescription>
        </DialogHeader>
        <div className="flex max-h-96 flex-col gap-2 overflow-y-auto">
          {isLoading ? (
            <p className="py-4 text-center text-sm text-muted-foreground">Loading…</p>
          ) : (
            (templates ?? []).map((t) => {
              const already = existingNames.has(t.name)
              return (
                <div
                  key={t.id}
                  className="flex items-start justify-between gap-3 rounded-md border p-3"
                >
                  <div>
                    <p className="text-sm font-medium">{t.name}</p>
                    {t.description && (
                      <p className="text-xs text-muted-foreground">{t.description}</p>
                    )}
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={already || adoptingId === t.id}
                    onClick={() => adopt(t)}
                  >
                    {already ? 'Already added' : 'Add'}
                  </Button>
                </div>
              )
            })
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}

/** "Institute admin can fetch the default roles also" + "current roles with
 * description which is also editable" (Institute Settings feedback) — the
 * second tab under "Role matrix" (see UserManagementPage), a plainer
 * roles-first view alongside the users×roles checkbox grid: one row per
 * role, its description editable in place, plus browsing/adopting from the
 * platform's default catalogue (`public.role_templates`, otherwise
 * platform-admin-only — see `GET /users/role-templates`). */
export function RolesListTab() {
  const [creatingRole, setCreatingRole] = React.useState(false)
  const [editingRole, setEditingRole] = React.useState<Role | null>(null)
  const [browsingDefaults, setBrowsingDefaults] = React.useState(false)

  const { data: roles, isLoading, refetch } = useEntityList<Role>(['roles'], '/users/roles/all')
  const { data: permissions } = useEntityList<Permission>(['permissions'], '/users/permissions')

  const existingNames = React.useMemo(() => new Set((roles ?? []).map((r) => r.name)), [roles])

  return (
    <div className="flex flex-col gap-4">
      <div className="flex justify-end gap-2">
        <Button size="sm" variant="outline" onClick={() => setBrowsingDefaults(true)}>
          <Download className="size-4" /> Fetch default roles
        </Button>
        <Button size="sm" onClick={() => setCreatingRole(true)}>
          <Plus className="size-4" /> New role
        </Button>
      </div>

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : (
        <div className="overflow-x-auto rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Description</TableHead>
                <TableHead>Permissions</TableHead>
                <TableHead className="w-px" />
              </TableRow>
            </TableHeader>
            <TableBody>
              {(roles ?? []).length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} className="text-center text-muted-foreground">
                    No roles yet.
                  </TableCell>
                </TableRow>
              ) : (
                (roles ?? []).map((r) => (
                  <TableRow key={r.id}>
                    <TableCell className="font-medium">
                      <div className="flex items-center gap-2">
                        {r.name}
                        {r.is_system_role && (
                          <Badge variant="outline" className="font-normal">
                            Default
                          </Badge>
                        )}
                      </div>
                    </TableCell>
                    <TableCell className="max-w-sm text-sm text-muted-foreground">
                      {r.description || '—'}
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {r.permission_codes.length}
                    </TableCell>
                    <TableCell>
                      {!r.is_system_role && (
                        <Button
                          size="sm"
                          variant="ghost"
                          aria-label={`Edit ${r.name}`}
                          onClick={() => setEditingRole(r)}
                        >
                          <Pencil className="size-4" />
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      )}

      {creatingRole && (
        <RoleFormDialog permissions={permissions ?? []} onClose={() => setCreatingRole(false)} />
      )}
      {editingRole && (
        <RoleFormDialog
          role={editingRole}
          permissions={permissions ?? []}
          onClose={() => setEditingRole(null)}
        />
      )}
      {browsingDefaults && (
        <FetchDefaultRolesDialog
          existingNames={existingNames}
          onClose={() => setBrowsingDefaults(false)}
          onAdopted={() => void refetch()}
        />
      )}
    </div>
  )
}
