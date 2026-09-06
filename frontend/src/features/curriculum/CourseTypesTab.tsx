import * as React from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus } from 'lucide-react'
import { toast } from 'sonner'
import { z } from 'zod'

import { useAuth } from '@/features/auth/useAuth'
import type { CourseType, SectionConfig, SectionKey } from '@/features/curriculum/types'
import { apiClient, ApiError } from '@/lib/api-client'
import { useEntityAction, useEntityCreate, useEntityGet, useEntityList } from '@/lib/crud-hooks'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { EntityFormDialog, type EntityField } from '@/components/entity-form-dialog'
import { Skeleton } from '@/components/ui/skeleton'
import { Switch } from '@/components/ui/switch'

const SECTION_LABELS: Record<SectionKey, string> = {
  overview: 'Course Overview',
  settings: 'Course Settings',
  students: 'Students / Enrollment',
  assessments: 'Assessments',
}
const SECTION_KEYS: SectionKey[] = ['overview', 'settings', 'students', 'assessments']

const schema = z.object({
  name: z.string().min(1, 'Name is required').max(100),
  description: z.string().optional(),
})

/** Course-Level Settings spec §1-§3: Program/Course Coordinators manage a
 * small, curated set of Course Types (distinct from the raw-text
 * `Course.course_type` catalog label — see the backend `CourseType` model's
 * docstring) and, per type, which of the four course-level sections a
 * Course Teacher may propose changes to. */
export function CourseTypesTab() {
  const { hasPermission } = useAuth()
  const canManage = hasPermission('course_type.manage')
  const [createOpen, setCreateOpen] = React.useState(false)
  const [includeInactive, setIncludeInactive] = React.useState(false)

  const { data: types, isLoading } = useEntityList<CourseType>(
    ['curriculum', 'course-types', includeInactive],
    '/course-types',
    { include_inactive: includeInactive ? 'true' : 'false' },
  )

  const create = useEntityCreate<Record<string, unknown>, CourseType>('/course-types', [
    ['curriculum', 'course-types'],
  ])
  const deactivate = useEntityAction<CourseType>(
    (id) => `/course-types/${id}/deactivate`,
    [['curriculum', 'course-types']],
  )
  const reactivate = useEntityAction<CourseType>(
    (id) => `/course-types/${id}/reactivate`,
    [['curriculum', 'course-types']],
  )

  const fields: EntityField[] = [
    { name: 'name', label: 'Name', type: 'text', placeholder: 'e.g. Theory, Lab, Capstone' },
    { name: 'description', label: 'Description (optional)', type: 'text' },
  ]

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between gap-2">
        <p className="text-sm text-muted-foreground">
          Course Types classify courses so you can control, per type, which sections a Course
          Teacher may propose changes to.
        </p>
        <div className="flex items-center gap-2">
          <Button size="sm" variant="outline" onClick={() => setIncludeInactive((v) => !v)}>
            {includeInactive ? 'Hide removed' : 'Show removed'}
          </Button>
          {canManage && (
            <Button size="sm" onClick={() => setCreateOpen(true)}>
              <Plus className="size-4" /> New course type
            </Button>
          )}
        </div>
      </div>

      {isLoading ? (
        <Skeleton className="h-40 w-full" />
      ) : !types || types.length === 0 ? (
        <p className="text-sm text-muted-foreground">No course types yet.</p>
      ) : (
        <div className="flex flex-col gap-3">
          {types.map((t) => (
            <Card key={t.id} className={t.is_active ? undefined : 'opacity-60'}>
              <CardHeader className="flex flex-row items-start justify-between gap-2 space-y-0">
                <div>
                  <CardTitle className="flex items-center gap-2 text-base">
                    {t.name}
                    {!t.is_active && (
                      <Badge variant="outline" className="font-normal">
                        Removed
                      </Badge>
                    )}
                  </CardTitle>
                  {t.description && <CardDescription>{t.description}</CardDescription>}
                </div>
                {canManage && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={async () => {
                      try {
                        if (t.is_active) {
                          await deactivate.mutateAsync(t.id)
                          toast.success(`${t.name} removed (historical courses are unaffected)`)
                        } else {
                          await reactivate.mutateAsync(t.id)
                          toast.success(`${t.name} restored`)
                        }
                      } catch (err) {
                        toast.error(err instanceof ApiError ? err.detail : 'Unable to update course type.')
                      }
                    }}
                  >
                    {t.is_active ? 'Remove' : 'Restore'}
                  </Button>
                )}
              </CardHeader>
              <CardContent>
                <SectionConfigGrid courseTypeId={t.id} canManage={canManage} />
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <EntityFormDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        title="New course type"
        fields={fields}
        schema={schema}
        defaultValues={{ name: '', description: '' }}
        onSubmit={async (values) => {
          try {
            await create.mutateAsync({
              name: values.name,
              description: values.description || undefined,
            })
            toast.success('Course type created')
          } catch (err) {
            throw err instanceof ApiError ? err : new ApiError('Unable to create course type.')
          }
        }}
      />
    </div>
  )
}

function SectionConfigGrid({
  courseTypeId,
  canManage,
}: {
  courseTypeId: string
  canManage: boolean
}) {
  const queryClient = useQueryClient()
  const queryKey = ['curriculum', 'course-types', courseTypeId, 'section-config']
  const { data: config, isLoading } = useEntityGet<SectionConfig[]>(
    queryKey,
    `/course-types/${courseTypeId}/section-config`,
  )
  const setEnabled = useMutation({
    mutationFn: async ({ sectionKey, isEnabled }: { sectionKey: SectionKey; isEnabled: boolean }) => {
      await apiClient.put(`/course-types/${courseTypeId}/section-config/${sectionKey}`, {
        is_enabled: isEnabled,
      })
    },
    onSuccess: () => void queryClient.invalidateQueries({ queryKey }),
  })

  const enabledByKey = React.useMemo(
    () => new Map((config ?? []).map((c) => [c.section_key, c.is_enabled])),
    [config],
  )

  if (isLoading) return <Skeleton className="h-16 w-full" />

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {SECTION_KEYS.map((key) => (
        <label
          key={key}
          className="flex items-center justify-between gap-2 rounded-md border px-3 py-2 text-sm"
        >
          <span>{SECTION_LABELS[key]}</span>
          <Switch
            checked={enabledByKey.get(key) ?? false}
            disabled={!canManage || setEnabled.isPending}
            onCheckedChange={async (checked) => {
              try {
                await setEnabled.mutateAsync({ sectionKey: key, isEnabled: checked })
              } catch (err) {
                toast.error(err instanceof ApiError ? err.detail : 'Unable to update section.')
              }
            }}
          />
        </label>
      ))}
    </div>
  )
}
