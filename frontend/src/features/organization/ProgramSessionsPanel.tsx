import * as React from 'react'
import { Inbox, Pencil } from 'lucide-react'
import { toast } from 'sonner'
import { z } from 'zod'

import { useAuth } from '@/features/auth/useAuth'
import type { Department, Program } from '@/features/organization/types'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { EntityFormDialog, type EntityField } from '@/components/entity-form-dialog'
import { Skeleton } from '@/components/ui/skeleton'
import { useEntityList, useEntityUpdate } from '@/lib/crud-hooks'
import { ApiError } from '@/lib/api-client'

const schema = z.object({
  session_names: z.string().optional(),
})

/** How many sessions a program runs per year, and what to call them
 * (Fall/Spring/Summer, Semester 1/2, Trimester 1/2/3, ...) — decided
 * per-program, since one program can run semesters while another runs
 * trimesters. Feeds nothing else automatically yet (see migration 0029's
 * docstring): it's the program's own record of its convention, for admins
 * to align academic-calendar term names against by hand. */
export function ProgramSessionsPanel() {
  const { hasPermission } = useAuth()
  const canManage = hasPermission('program.manage')
  const [editProgram, setEditProgram] = React.useState<Program | null>(null)

  const { data: departments } = useEntityList<Department>(
    ['org', 'departments'],
    '/org/departments',
  )
  const { data: programs, isLoading, error } = useEntityList<Program>(
    ['org', 'programs'],
    '/org/programs',
  )
  const update = useEntityUpdate<Record<string, unknown>, Program>(
    (id) => `/org/programs/${id}`,
    [['org', 'programs']],
  )

  const deptById = React.useMemo(
    () => new Map((departments ?? []).map((d) => [d.id, d])),
    [departments],
  )

  const fields: EntityField[] = [
    {
      name: 'session_names',
      label: 'Session names',
      type: 'text',
      placeholder: 'e.g. Fall, Spring, Summer',
    },
  ]

  if (isLoading) {
    return (
      <div className="flex flex-col gap-2">
        <Skeleton className="h-16 w-full" />
        <Skeleton className="h-16 w-full" />
      </div>
    )
  }

  if (error) {
    return <p className="text-sm text-destructive">Failed to load programs.</p>
  }

  if (!programs || programs.length === 0) {
    return (
      <div className="flex flex-col items-center gap-2 rounded-md border border-dashed py-12 text-center text-muted-foreground">
        <Inbox className="size-5 opacity-50" />
        <p className="text-sm">Create a program first, then define its sessions here.</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-3">
      <p className="text-sm text-muted-foreground">
        How many sessions each program runs per year, and what to call them — used to align
        academic-calendar terms with the right program.
      </p>
      {programs.map((p) => (
        <Card key={p.id}>
          <CardHeader className="flex flex-row items-center justify-between py-3">
            <div>
              <CardTitle className="text-base">{p.name}</CardTitle>
              <p className="text-xs text-muted-foreground">
                {deptById.get(p.department_id)?.name ?? '—'} · {p.code}
              </p>
            </div>
            {canManage && (
              <Button size="sm" variant="outline" onClick={() => setEditProgram(p)}>
                <Pencil className="size-4" /> Edit sessions
              </Button>
            )}
          </CardHeader>
          <CardContent className="flex flex-wrap gap-1.5 pt-0">
            {p.session_names.length === 0 ? (
              <span className="text-sm text-muted-foreground">No sessions defined yet.</span>
            ) : (
              p.session_names.map((name, i) => (
                <Badge key={`${name}-${i}`} variant="secondary" className="font-normal">
                  {name}
                </Badge>
              ))
            )}
          </CardContent>
        </Card>
      ))}

      {editProgram && (
        <EntityFormDialog
          open={Boolean(editProgram)}
          onOpenChange={(open) => !open && setEditProgram(null)}
          title={`Sessions for ${editProgram.name}`}
          description="Comma-separated, in order (e.g. Fall, Spring, Summer)."
          fields={fields}
          schema={schema}
          defaultValues={{ session_names: editProgram.session_names.join(', ') }}
          onSubmit={async (values) => {
            try {
              const sessionNames = String(values.session_names ?? '')
                .split(',')
                .map((s) => s.trim())
                .filter(Boolean)
              await update.mutateAsync({
                id: editProgram.id,
                body: { session_names: sessionNames },
              })
              toast.success('Sessions updated')
              setEditProgram(null)
            } catch (err) {
              throw err instanceof ApiError ? err : new ApiError('Unable to update sessions.')
            }
          }}
        />
      )}
    </div>
  )
}
