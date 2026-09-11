import * as React from 'react'
import {
  AlertCircle,
  Database,
  LayoutDashboard,
  LogOut,
  Pencil,
  Plus,
  RefreshCw,
  ShieldCheck,
  Trash2,
} from 'lucide-react'
import { Link, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'

import { ApiError } from '@/lib/api-client'
import { usePlatformAuth } from '@/lib/platform-auth-context'
import { ConfirmAction } from '@/components/confirm-action'
import {
  useCreateRoleTemplate,
  useDeleteRoleTemplate,
  usePermissionCatalogue,
  useResyncRoleTemplates,
  useRoleTemplates,
  useUpdateRoleTemplate,
} from '@/features/platform/api'
import type { RoleTemplateRead } from '@/features/platform/types'
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import { Switch } from '@/components/ui/switch'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Textarea } from '@/components/ui/textarea'
import { Footer } from '@/components/footer'
import { Logo } from '@/components/logo'
import { PageHeader } from '@/components/page-header'
import { ThemeToggleButton } from '@/components/theme-toggle'

function RoleTemplateFormDialog({
  template,
  onClose,
}: {
  template?: RoleTemplateRead
  onClose: () => void
}) {
  const { data: permissions } = usePermissionCatalogue()
  const createTemplate = useCreateRoleTemplate()
  const updateTemplate = useUpdateRoleTemplate()

  const [name, setName] = React.useState(template?.name ?? '')
  const [description, setDescription] = React.useState(template?.description ?? '')
  const [allPermissions, setAllPermissions] = React.useState(template?.all_permissions ?? false)
  const [selectedCodes, setSelectedCodes] = React.useState<Set<string>>(
    new Set(template?.permission_codes ?? []),
  )
  const [submitting, setSubmitting] = React.useState(false)

  const modules = React.useMemo(() => {
    const byModule = new Map<string, typeof permissions>()
    for (const p of permissions ?? []) {
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
      if (template) {
        await updateTemplate.mutateAsync({
          id: template.id,
          body: {
            name: name.trim(),
            description: description.trim() || null,
            permission_codes: Array.from(selectedCodes),
            all_permissions: allPermissions,
          },
        })
        toast.success(`${name.trim()} updated.`)
      } else {
        await createTemplate.mutateAsync({
          name: name.trim(),
          description: description.trim() || null,
          permission_codes: Array.from(selectedCodes),
          all_permissions: allPermissions,
        })
        toast.success(`${name.trim()} created — every new institution will start with it.`)
      }
      onClose()
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Unable to save role template.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{template ? `Edit ${template.name}` : 'New default role template'}</DialogTitle>
          <DialogDescription>
            {template
              ? "Changes here don't retroactively touch institutions already provisioned — only new ones (or a manual re-seed)."
              : 'Every newly-provisioned institution starts with this user type. Institutions can add their own custom types alongside it, but can never edit this one.'}
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-3">
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="template-name">Name</Label>
            <Input id="template-name" value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div className="flex flex-col gap-1.5">
            <Label htmlFor="template-description">Description</Label>
            <Textarea
              id="template-description"
              value={description ?? ''}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
            />
          </div>
          <div className="flex items-center justify-between rounded-md border p-3">
            <div className="flex flex-col">
              <span className="text-sm font-medium">All permissions</span>
              <span className="text-xs text-muted-foreground">
                The ALL sentinel (only "Legacy Tenant Administrator" uses this today) — grants
                every permission that exists now or ever will, ignoring the checkboxes below.
              </span>
            </div>
            <Switch checked={allPermissions} onCheckedChange={setAllPermissions} />
          </div>
          {!allPermissions && (
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
                        {(modulePermissions ?? []).map((p) => (
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
                              <span className="text-xs text-muted-foreground">
                                {p.description}
                              </span>
                            </span>
                          </label>
                        ))}
                      </AccordionContent>
                    </AccordionItem>
                  ))}
                </Accordion>
              </div>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={submitting}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={submitting}>
            {submitting ? 'Saving…' : template ? 'Save changes' : 'Create template'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export function PlatformRoleTemplatesPage() {
  const { admin, logout } = usePlatformAuth()
  const navigate = useNavigate()
  const { data: templates, isLoading, isError } = useRoleTemplates()
  const updateTemplate = useUpdateRoleTemplate()
  const resyncTemplates = useResyncRoleTemplates()
  const deleteTemplate = useDeleteRoleTemplate()
  const [creating, setCreating] = React.useState(false)
  const [editing, setEditing] = React.useState<RoleTemplateRead | null>(null)

  function handleLogout() {
    logout()
    navigate('/platform-login', { replace: true })
  }

  async function handleDelete(template: RoleTemplateRead) {
    try {
      await deleteTemplate.mutateAsync(template.id)
      toast.success(`${template.name} deleted.`)
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Unable to delete role template.')
    }
  }

  async function toggleActive(template: RoleTemplateRead) {
    try {
      await updateTemplate.mutateAsync({
        id: template.id,
        body: { is_active: !template.is_active },
      })
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Unable to update role template.')
    }
  }

  async function handleResync() {
    try {
      const result = await resyncTemplates.mutateAsync()
      if (result.failed.length > 0) {
        toast.error(
          `Synced to ${result.succeeded.length} institution${result.succeeded.length === 1 ? '' : 's'}, failed for: ${result.failed.join(', ')}`,
        )
      } else {
        toast.success(
          `Synced to ${result.succeeded.length} institution${result.succeeded.length === 1 ? '' : 's'}.`,
        )
      }
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Unable to resync role templates.')
    }
  }

  return (
    <div className="flex min-h-screen flex-col bg-muted/40">
      <header className="flex h-16 shrink-0 items-center justify-between border-b bg-card px-4 md:px-6">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Logo className="text-lg" />
            <Badge variant="outline" className="font-normal text-muted-foreground">
              Platform Admin
            </Badge>
          </div>
        </div>
        <div className="flex items-center gap-2 sm:gap-4">
          <Button variant="outline" size="sm" asChild>
            <Link to="/platform">
              <LayoutDashboard className="size-4" />
              Dashboard
            </Link>
          </Button>
          <Button variant="outline" size="sm" asChild>
            <Link to="/platform/raw-data">
              <Database className="size-4" />
              Raw data console
            </Link>
          </Button>
          <span className="hidden text-sm text-muted-foreground sm:inline">{admin?.email}</span>
          <ThemeToggleButton />
          <Button variant="ghost" size="sm" onClick={handleLogout}>
            <LogOut className="size-4" />
            Log out
          </Button>
        </div>
      </header>

      <main className="flex-1 p-4 md:p-8">
        <div className="mx-auto w-full max-w-7xl">
          <PageHeader
            title="Role Templates"
            description="The default user types every newly-provisioned institution starts from. An institution can add its own custom types afterward, but can never edit these."
            actions={
              <>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleResync}
                  disabled={resyncTemplates.isPending}
                >
                  <RefreshCw className="size-4" />
                  {resyncTemplates.isPending ? 'Syncing…' : 'Resync to institutions'}
                </Button>
                <Button size="sm" onClick={() => setCreating(true)}>
                  <Plus className="size-4" />
                  New template
                </Button>
              </>
            }
          />

          <Card>
            <CardContent className="p-0">
              {isLoading ? (
                <div className="flex flex-col gap-3 p-4">
                  {Array.from({ length: 5 }).map((_, i) => (
                    <Skeleton key={i} className="h-8 w-full" />
                  ))}
                </div>
              ) : isError ? (
                <div className="flex flex-col items-center gap-2 py-16 text-center">
                  <AlertCircle className="size-8 text-destructive" />
                  <p className="text-sm text-destructive">Failed to load role templates.</p>
                </div>
              ) : templates && templates.length > 0 ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Name</TableHead>
                      <TableHead>Description</TableHead>
                      <TableHead>Permissions</TableHead>
                      <TableHead>Assignable by default</TableHead>
                      <TableHead className="w-10" />
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {templates.map((t) => (
                      <TableRow key={t.id}>
                        <TableCell className="font-medium">{t.name}</TableCell>
                        <TableCell className="max-w-md truncate text-sm text-muted-foreground">
                          {t.description}
                        </TableCell>
                        <TableCell>
                          {t.all_permissions ? (
                            <Badge variant="secondary">ALL</Badge>
                          ) : (
                            <span className="text-sm text-muted-foreground">
                              {t.permission_codes.length}
                            </span>
                          )}
                        </TableCell>
                        <TableCell>
                          <Switch checked={t.is_active} onCheckedChange={() => toggleActive(t)} />
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center justify-end gap-1">
                            <Button variant="ghost" size="icon" onClick={() => setEditing(t)}>
                              <Pencil className="size-4" />
                            </Button>
                            <ConfirmAction
                              trigger={
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  className="text-destructive hover:text-destructive"
                                >
                                  <Trash2 className="size-4" />
                                </Button>
                              }
                              title={`Delete ${t.name}?`}
                              description="This removes it from the default catalogue for institutions provisioned or resynced from now on. Institutions that already have this role keep it — this does not touch any tenant's own roles table."
                              confirmLabel="Delete"
                              onConfirm={() => handleDelete(t)}
                            />
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              ) : (
                <div className="flex flex-col items-center gap-2 py-16 text-center">
                  <ShieldCheck className="size-8 text-muted-foreground" />
                  <p className="font-medium">No role templates yet</p>
                  <p className="max-w-sm text-sm text-muted-foreground">
                    Create the first default user type — every newly-provisioned institution will
                    start with it.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </main>

      {creating && <RoleTemplateFormDialog onClose={() => setCreating(false)} />}
      {editing && <RoleTemplateFormDialog template={editing} onClose={() => setEditing(null)} />}

      <Footer />
    </div>
  )
}
