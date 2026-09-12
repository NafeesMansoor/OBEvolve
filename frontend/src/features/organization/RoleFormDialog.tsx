import * as React from 'react'
import { toast } from 'sonner'

import type { Permission, Role, RoleCreateInput, RoleUpdateInput } from '@/features/organization/types'
import { ApiError } from '@/lib/api-client'
import { useEntityCreate, useEntityUpdate } from '@/lib/crud-hooks'
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

/** Create (no `role` prop) or edit (custom roles only — callers never pass a
 * system role here) a tenant-scoped "user type." Always institution-local:
 * `POST /users/roles` creates a plain row in THIS tenant's own `roles`
 * table, structurally invisible to every other institution and to the
 * platform-level default-role catalogue (schema-per-institution) — an
 * institution can compose its own role from the fixed permission
 * catalogue, but never touch what the platform seeds by default.
 *
 * Its own file (not local to RoleMatrixTab.tsx) so both RoleMatrixTab and
 * RolesListTab can use it without an import cycle between them. */
export function RoleFormDialog({
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
