import * as React from 'react'
import { UserPlus } from 'lucide-react'
import { toast } from 'sonner'
import { z } from 'zod'

import type { ProgramRoster } from '@/features/organization/types'
import { ApiError, apiClient } from '@/lib/api-client'
import { useEntityGet } from '@/lib/crud-hooks'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { EntityFormDialog, type EntityField } from '@/components/entity-form-dialog'
import { Input } from '@/components/ui/input'
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'

interface FacultyCreateResult {
  user_id: string
  email: string
  full_name: string
  temporary_password: string
}

const createFacultySchema = z.object({
  full_name: z.string().min(1, 'Full name is required'),
  email: z.string().min(1, 'Email is required').email('Enter a valid email'),
  employee_code: z.string().min(1, 'Employee code is required'),
  designation: z.string().optional(),
  contract_type: z.enum(['full_time', 'part_time', '']).optional(),
})

const ROLES_NEEDING_COURSE_PICKER = new Set(['Section Coordinator'])

/** Program Administrator/Coordinator's own scoped counterpart to the
 * institution-wide Role matrix (RoleMatrixTab) — same checkbox-matrix
 * idea, but backed by `/program-roles/*` (app.api.v1.endpoints.
 * program_roles), which only ever shows/grants within this one program:
 * Faculty (program-wide) and Section Coordinator (per
 * course, multi-select popup), never any other role. */
export function ProgramRoleMatrixTab() {
  const [search, setSearch] = React.useState('')
  const [coursePopup, setCoursePopup] = React.useState<{
    userId: string
    userName: string
    roleId: string
    roleName: string
  } | null>(null)
  const [addFacultyOpen, setAddFacultyOpen] = React.useState(false)
  const [createdFaculty, setCreatedFaculty] = React.useState<FacultyCreateResult | null>(null)

  const { data: roster, isLoading, refetch } = useEntityGet<ProgramRoster>(
    ['program-roles', 'roster'],
    '/program-roles/roster',
  )

  const filteredFaculty = React.useMemo(() => {
    const q = search.trim().toLowerCase()
    const list = roster?.faculty ?? []
    if (!q) return list
    return list.filter(
      (f) => f.full_name.toLowerCase().includes(q) || f.email.toLowerCase().includes(q),
    )
  }, [roster, search])

  function grantsFor(userId: string, roleId: string) {
    return (roster?.grants ?? []).filter((g) => g.user_id === userId && g.role_id === roleId)
  }

  async function grantProgramWide(userId: string, roleId: string, roleName: string, userName: string) {
    try {
      await apiClient.post('/program-roles/user-roles', {
        user_id: userId, role_id: roleId, scope_type: 'program',
      })
      await refetch()
      toast.success(`${roleName} granted to ${userName}`)
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Unable to grant role.')
    }
  }

  async function revokeAll(userId: string, roleId: string, roleName: string, userName: string) {
    const existing = grantsFor(userId, roleId)
    try {
      await Promise.all(
        existing.map((g) => apiClient.delete(`/program-roles/user-roles/${g.id}`)),
      )
      await refetch()
      toast.success(`${roleName} revoked from ${userName}`)
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Unable to revoke role.')
    }
  }

  function toggle(
    userId: string, userName: string, roleId: string, roleName: string, checked: boolean,
  ) {
    if (!checked) {
      void revokeAll(userId, roleId, roleName, userName)
      return
    }
    if (ROLES_NEEDING_COURSE_PICKER.has(roleName)) {
      setCoursePopup({ userId, userName, roleId, roleName })
      return
    }
    void grantProgramWide(userId, roleId, roleName, userName)
  }

  const roles = roster?.assignable_roles ?? []

  return (
    <div className="flex flex-col gap-4">
      <p className="text-sm text-muted-foreground">
        Grant or revoke Faculty and Section Coordinator roles for people in
        this program. Checking Section Coordinator lets you pick one or more
        courses at once.
      </p>
      <div className="flex items-center justify-between gap-2">
        <Input
          placeholder="Search faculty…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="max-w-sm"
        />
        <Button size="sm" onClick={() => setAddFacultyOpen(true)}>
          <UserPlus className="size-4" /> Add new faculty
        </Button>
      </div>

      {isLoading || !roster ? (
        <p className="text-sm text-muted-foreground">Loading…</p>
      ) : (
        <div className="overflow-x-auto rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="sticky left-0 bg-background">Faculty</TableHead>
                {roles.map((r) => (
                  <TableHead key={r.id} className="whitespace-nowrap text-center">
                    {r.name}
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredFaculty.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={roles.length + 1} className="text-center text-muted-foreground">
                    No faculty found. Faculty must first be assigned to a section (Academic
                    Operations → Faculty Assignments) before they appear here.
                  </TableCell>
                </TableRow>
              ) : (
                filteredFaculty.map((f) => (
                  <TableRow key={f.id}>
                    <TableCell className="sticky left-0 bg-background">
                      <div className="flex flex-col">
                        <span className="font-medium">{f.full_name}</span>
                        <span className="text-xs text-muted-foreground">{f.email}</span>
                      </div>
                    </TableCell>
                    {roles.map((r) => {
                      const held = grantsFor(f.id, r.id)
                      const courseCodes =
                        r.name === 'Section Coordinator'
                          ? held.map(
                              (g) =>
                                (roster.courses ?? []).find((c) => c.id === g.scope_id)?.code ?? '?',
                            )
                          : []
                      const checkbox = (
                        <Checkbox
                          checked={held.length > 0}
                          onCheckedChange={(checked) =>
                            toggle(f.id, f.full_name, r.id, r.name, checked === true)
                          }
                        />
                      )
                      return (
                        <TableCell key={r.id} className="text-center">
                          {courseCodes.length > 0 ? (
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <span className="inline-flex">{checkbox}</span>
                              </TooltipTrigger>
                              <TooltipContent>{courseCodes.join(', ')}</TooltipContent>
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

      {coursePopup && (
        <CoursePickerDialog
          userName={coursePopup.userName}
          roleName={coursePopup.roleName}
          courses={roster?.courses ?? []}
          alreadyGranted={
            new Set(
              grantsFor(coursePopup.userId, coursePopup.roleId).map((g) => g.scope_id ?? ''),
            )
          }
          onClose={() => setCoursePopup(null)}
          onConfirm={async (courseIds) => {
            try {
              await Promise.all(
                courseIds.map((courseId) =>
                  apiClient.post('/program-roles/user-roles', {
                    user_id: coursePopup.userId, role_id: coursePopup.roleId,
                    scope_type: 'course', course_id: courseId,
                  }),
                ),
              )
              await refetch()
              toast.success(
                `${coursePopup.roleName} granted to ${coursePopup.userName} for ${courseIds.length} course${courseIds.length === 1 ? '' : 's'}`,
              )
              setCoursePopup(null)
            } catch (err) {
              toast.error(err instanceof ApiError ? err.detail : 'Unable to grant role.')
            }
          }}
        />
      )}

      <EntityFormDialog
        open={addFacultyOpen}
        onOpenChange={setAddFacultyOpen}
        title="Add new faculty"
        description="Creates a brand-new faculty account and grants the Faculty role for this program — spec §30."
        fields={[
          { name: 'full_name', label: 'Full name', type: 'text' },
          { name: 'email', label: 'Email', type: 'text' },
          { name: 'employee_code', label: 'Employee code', type: 'text' },
          { name: 'designation', label: 'Designation (optional)', type: 'text' },
          {
            name: 'contract_type',
            label: 'Contract type (optional)',
            type: 'select',
            options: [
              { label: 'Full time', value: 'full_time' },
              { label: 'Part time', value: 'part_time' },
            ],
          },
        ] as EntityField[]}
        schema={createFacultySchema}
        defaultValues={{
          full_name: '',
          email: '',
          employee_code: '',
          designation: '',
          contract_type: '',
        }}
        onSubmit={async (values) => {
          try {
            const { data } = await apiClient.post<FacultyCreateResult>('/program-roles/faculty', {
              full_name: values.full_name,
              email: values.email,
              employee_code: values.employee_code,
              designation: values.designation || null,
              contract_type: values.contract_type || null,
            })
            await refetch()
            setCreatedFaculty(data)
          } catch (err) {
            throw err instanceof ApiError ? err : new ApiError('Unable to create faculty account.')
          }
        }}
      />

      {createdFaculty && (
        <Dialog open onOpenChange={(open) => !open && setCreatedFaculty(null)}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Faculty account created</DialogTitle>
              <DialogDescription>
                Share this temporary password with {createdFaculty.full_name} — it will not be shown
                again. They must change it after signing in for the first time.
              </DialogDescription>
            </DialogHeader>
            <div className="flex flex-col gap-2 rounded-md border bg-muted/30 p-3">
              <p className="text-sm">
                <span className="font-medium">Email:</span> {createdFaculty.email}
              </p>
              <p className="font-mono text-sm">
                <span className="font-sans font-medium">Temporary password:</span>{' '}
                {createdFaculty.temporary_password}
              </p>
            </div>
            <DialogFooter>
              <Button onClick={() => setCreatedFaculty(null)}>Done</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </div>
  )
}

function CoursePickerDialog({
  userName,
  roleName,
  courses,
  alreadyGranted,
  onClose,
  onConfirm,
}: {
  userName: string
  roleName: string
  courses: { id: string; code: string; title: string }[]
  alreadyGranted: Set<string>
  onClose: () => void
  onConfirm: (courseIds: string[]) => void | Promise<void>
}) {
  const [selected, setSelected] = React.useState<Set<string>>(new Set())
  const [submitting, setSubmitting] = React.useState(false)
  const selectable = courses.filter((c) => !alreadyGranted.has(c.id))

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
          <DialogTitle>{roleName} — select courses</DialogTitle>
          <DialogDescription>
            {userName} will be granted {roleName} for every course selected below. You can select
            more than one.
          </DialogDescription>
        </DialogHeader>
        <div className="flex max-h-72 flex-col gap-1 overflow-y-auto">
          {selectable.length === 0 ? (
            <p className="py-4 text-center text-sm text-muted-foreground">
              Already granted for every course in this program.
            </p>
          ) : (
            selectable.map((c) => (
              <label
                key={c.id}
                className="flex cursor-pointer items-center gap-2 rounded-md p-2 text-sm hover:bg-muted"
              >
                <Checkbox checked={selected.has(c.id)} onCheckedChange={() => toggleOption(c.id)} />
                {c.code} — {c.title}
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
