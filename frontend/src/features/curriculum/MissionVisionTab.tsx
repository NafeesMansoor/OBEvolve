import * as React from 'react'
import { Plus, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { z } from 'zod'

import { useAuth } from '@/features/auth/useAuth'
import type {
  InstitutionalMission,
  InstitutionalVision,
  InstitutionalVisionProgramVisionMapping,
  PeoVisionMapping,
  PEO,
  ProgramMission,
  ProgramVision,
} from '@/features/curriculum/types'
import { useProgramVersionOptions } from '@/features/curriculum/useProgramVersionOptions'
import { ApiError } from '@/lib/api-client'
import { useEntityCreate, useEntityDelete, useEntityList } from '@/lib/crud-hooks'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { DataTable, type DataTableColumn } from '@/components/data-table'
import { EntityFormDialog, type EntityField } from '@/components/entity-form-dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

interface SimpleMapping {
  id: string
}

/** A plain many-to-many link with no correlation-strength field (unlike
 * KpiMappingTab's MappingSection) — spec §9/§11 just want structured
 * mappings, not a scale. Reused for Institutional Vision<->Program Vision
 * and PEO<->Program Vision below. */
function SimpleMappingSection<T extends SimpleMapping>({
  title,
  endpoint,
  ownIdField,
  ownId,
  targetIdField,
  targetOptions,
  targetLabelById,
  mappings,
  canManage,
  queryKey,
}: {
  title: string
  endpoint: string
  ownIdField: string
  ownId: string
  targetIdField: string
  targetOptions: { label: string; value: string }[]
  targetLabelById: Map<string, string>
  mappings: T[]
  canManage: boolean
  queryKey: unknown[]
}) {
  const [open, setOpen] = React.useState(false)
  const create = useEntityCreate<Record<string, unknown>, T>(endpoint, [queryKey])
  const remove = useEntityDelete((id) => `${endpoint}/${id}`, [queryKey])
  const schema = z.object({ target_id: z.string().min(1, 'Required') })

  return (
    <div className="flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium">{title}</h4>
        {canManage && (
          <Button size="sm" variant="outline" onClick={() => setOpen(true)}>
            <Plus className="size-4" /> Map
          </Button>
        )}
      </div>
      {mappings.length === 0 ? (
        <p className="text-sm text-muted-foreground">No mappings yet.</p>
      ) : (
        <ul className="flex flex-col gap-1">
          {mappings.map((m) => (
            <li key={m.id} className="flex items-center justify-between text-sm">
              <span>
                {targetLabelById.get((m as unknown as Record<string, string>)[targetIdField]) ??
                  'Unknown'}
              </span>
              {canManage && (
                <Button
                  size="icon"
                  variant="ghost"
                  aria-label="Remove mapping"
                  onClick={async () => {
                    try {
                      await remove.mutateAsync(m.id)
                    } catch (err) {
                      toast.error(err instanceof ApiError ? err.detail : 'Unable to remove mapping.')
                    }
                  }}
                >
                  <Trash2 className="size-3.5" />
                </Button>
              )}
            </li>
          ))}
        </ul>
      )}
      <EntityFormDialog
        open={open}
        onOpenChange={setOpen}
        title={`Map to ${title}`}
        fields={[{ name: 'target_id', label: title, type: 'select', options: targetOptions }]}
        schema={schema}
        defaultValues={{ target_id: '' }}
        onSubmit={async (values) => {
          try {
            await create.mutateAsync({
              [ownIdField]: ownId,
              [targetIdField]: values.target_id,
            })
            toast.success('Mapping created')
          } catch (err) {
            throw err instanceof ApiError ? err : new ApiError('Unable to create mapping.')
          }
        }}
      />
    </div>
  )
}

const missionSchema = z.object({ statement: z.string().min(1, 'Statement is required') })
const visionSchema = z.object({
  label: z.string().min(1, 'Label is required').max(20),
  statement: z.string().min(1, 'Statement is required'),
  sequence: z.coerce.number().int(),
})

/** Institutional + Program Mission & Vision (spec §7-9) — the strategic
 * academic-identity layer that sits above PEOs/POs. Institutional entries
 * are institution-wide (no program-version selector); Program entries are
 * scoped to whichever program version is picked, same pattern as
 * PEOsTab/ProgramOutcomesTab. */
export function MissionVisionTab() {
  const { hasPermission } = useAuth()
  const canManage = hasPermission('program_outcome_framework.manage')
  const { options: pvOptions } = useProgramVersionOptions()
  const [programVersionId, setProgramVersionId] = React.useState('')
  const [missionDialogOpen, setMissionDialogOpen] = React.useState(false)
  const [visionDialogOpen, setVisionDialogOpen] = React.useState(false)
  const [progMissionDialogOpen, setProgMissionDialogOpen] = React.useState(false)
  const [progVisionDialogOpen, setProgVisionDialogOpen] = React.useState(false)
  const [selectedProgVisionId, setSelectedProgVisionId] = React.useState('')

  const { data: missions, isLoading: missionsLoading, error: missionsError } = useEntityList<InstitutionalMission>(
    ['curriculum', 'institutional-missions'],
    '/curriculum/institutional-missions',
  )
  const { data: visions, isLoading: visionsLoading, error: visionsError } = useEntityList<InstitutionalVision>(
    ['curriculum', 'institutional-visions'],
    '/curriculum/institutional-visions',
  )
  const { data: progMissions, isLoading: progMissionsLoading } = useEntityList<ProgramMission>(
    ['curriculum', 'program-missions', programVersionId],
    '/curriculum/program-missions',
    { program_version_id: programVersionId || undefined },
    { enabled: Boolean(programVersionId) },
  )
  const { data: progVisions, isLoading: progVisionsLoading } = useEntityList<ProgramVision>(
    ['curriculum', 'program-visions', programVersionId],
    '/curriculum/program-visions',
    { program_version_id: programVersionId || undefined },
    { enabled: Boolean(programVersionId) },
  )
  const { data: peos } = useEntityList<PEO>(
    ['curriculum', 'peos', programVersionId],
    '/curriculum/peos',
    { program_version_id: programVersionId || undefined },
    { enabled: Boolean(programVersionId) },
  )
  const { data: ivpvMappings } = useEntityList<InstitutionalVisionProgramVisionMapping>(
    ['curriculum', 'institutional-vision-program-vision-mappings', selectedProgVisionId],
    '/curriculum/institutional-vision-program-vision-mappings',
    { program_vision_id: selectedProgVisionId || undefined },
    { enabled: Boolean(selectedProgVisionId) },
  )
  const { data: peoVisionMappings } = useEntityList<PeoVisionMapping>(
    ['curriculum', 'peo-vision-mappings-by-vision', selectedProgVisionId],
    '/curriculum/peo-vision-mappings',
    { program_vision_id: selectedProgVisionId || undefined },
    { enabled: Boolean(selectedProgVisionId) },
  )

  const createMission = useEntityCreate<Record<string, unknown>, InstitutionalMission>(
    '/curriculum/institutional-missions',
    [['curriculum', 'institutional-missions']],
  )
  const createVision = useEntityCreate<Record<string, unknown>, InstitutionalVision>(
    '/curriculum/institutional-visions',
    [['curriculum', 'institutional-visions']],
  )
  const createProgMission = useEntityCreate<Record<string, unknown>, ProgramMission>(
    '/curriculum/program-missions',
    [['curriculum', 'program-missions', programVersionId]],
  )
  const createProgVision = useEntityCreate<Record<string, unknown>, ProgramVision>(
    '/curriculum/program-visions',
    [['curriculum', 'program-visions', programVersionId]],
  )

  const institutionalVisionOptions = React.useMemo(
    () => (visions ?? []).map((v) => ({ label: `${v.label} — ${v.statement}`, value: v.id })),
    [visions],
  )
  const institutionalVisionLabelById = React.useMemo(
    () => new Map((visions ?? []).map((v) => [v.id, `${v.label} — ${v.statement}`])),
    [visions],
  )
  const peoOptions = React.useMemo(
    () => (peos ?? []).map((p) => ({ label: `${p.code} — ${p.statement}`, value: p.id })),
    [peos],
  )
  const peoLabelById = React.useMemo(
    () => new Map((peos ?? []).map((p) => [p.id, `${p.code} — ${p.statement}`])),
    [peos],
  )

  const visionColumns: DataTableColumn<InstitutionalVision>[] = [
    { key: 'label', header: 'Label', render: (r) => <Badge variant="outline">{r.label}</Badge> },
    { key: 'statement', header: 'Statement', render: (r) => r.statement, className: 'max-w-lg' },
  ]
  const progVisionColumns: DataTableColumn<ProgramVision>[] = [
    { key: 'label', header: 'Label', render: (r) => <Badge variant="outline">{r.label}</Badge> },
    { key: 'statement', header: 'Statement', render: (r) => r.statement, className: 'max-w-lg' },
  ]

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Institutional mission</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          {missionsLoading ? (
            <p className="text-sm text-muted-foreground">Loading…</p>
          ) : missionsError ? (
            <p className="text-sm text-destructive">Unable to load.</p>
          ) : (missions ?? []).length === 0 ? (
            <p className="text-sm text-muted-foreground">No institutional mission defined yet.</p>
          ) : (
            (missions ?? []).map((m) => (
              <p key={m.id} className="text-sm">
                {m.statement}
              </p>
            ))
          )}
          {canManage && (
            <Button size="sm" variant="outline" className="w-fit" onClick={() => setMissionDialogOpen(true)}>
              <Plus className="size-4" /> Add mission statement
            </Button>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle className="text-base">Institutional visions</CardTitle>
          {canManage && (
            <Button size="sm" onClick={() => setVisionDialogOpen(true)}>
              <Plus className="size-4" /> New vision
            </Button>
          )}
        </CardHeader>
        <CardContent>
          <DataTable
            data={visions}
            columns={visionColumns}
            rowKey={(r) => r.id}
            isLoading={visionsLoading}
            error={visionsError}
            emptyMessage="No institutional visions yet."
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Program mission &amp; vision</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <div className="w-full max-w-sm">
            <Select value={programVersionId} onValueChange={setProgramVersionId}>
              <SelectTrigger>
                <SelectValue placeholder="Select a program version" />
              </SelectTrigger>
              <SelectContent>
                {pvOptions.map((o) => (
                  <SelectItem key={o.value} value={o.value}>
                    {o.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          {!programVersionId ? (
            <p className="text-sm text-muted-foreground">
              Select a program version to see its mission and visions.
            </p>
          ) : (
            <>
              <div className="flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-medium">Program mission</h4>
                  {canManage && (
                    <Button size="sm" variant="outline" onClick={() => setProgMissionDialogOpen(true)}>
                      <Plus className="size-4" /> Add
                    </Button>
                  )}
                </div>
                {progMissionsLoading ? (
                  <p className="text-sm text-muted-foreground">Loading…</p>
                ) : (progMissions ?? []).length === 0 ? (
                  <p className="text-sm text-muted-foreground">No program mission defined yet.</p>
                ) : (
                  (progMissions ?? []).map((m) => (
                    <p key={m.id} className="text-sm">
                      {m.statement}
                    </p>
                  ))
                )}
              </div>

              <div className="flex flex-col gap-2">
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-medium">Program visions</h4>
                  {canManage && (
                    <Button size="sm" variant="outline" onClick={() => setProgVisionDialogOpen(true)}>
                      <Plus className="size-4" /> New vision
                    </Button>
                  )}
                </div>
                <DataTable
                  data={progVisions}
                  columns={progVisionColumns}
                  rowKey={(r) => r.id}
                  isLoading={progVisionsLoading}
                  emptyMessage="No program visions yet."
                  onRowClick={(r) => setSelectedProgVisionId(r.id)}
                />
              </div>

              {selectedProgVisionId && (
                <div className="grid gap-4 rounded-md border p-4 md:grid-cols-2">
                  <p className="text-sm text-muted-foreground md:col-span-2">
                    Mappings for{' '}
                    <strong>
                      {(progVisions ?? []).find((v) => v.id === selectedProgVisionId)?.label}
                    </strong>{' '}
                    — click another row above to switch, or{' '}
                    <button
                      type="button"
                      className="underline"
                      onClick={() => setSelectedProgVisionId('')}
                    >
                      clear selection
                    </button>
                    .
                  </p>
                  <SimpleMappingSection
                    title="Institutional Vision"
                    endpoint="/curriculum/institutional-vision-program-vision-mappings"
                    ownIdField="program_vision_id"
                    ownId={selectedProgVisionId}
                    targetIdField="institutional_vision_id"
                    targetOptions={institutionalVisionOptions}
                    targetLabelById={institutionalVisionLabelById}
                    mappings={ivpvMappings ?? []}
                    canManage={canManage}
                    queryKey={[
                      'curriculum',
                      'institutional-vision-program-vision-mappings',
                      selectedProgVisionId,
                    ]}
                  />
                  <SimpleMappingSection
                    title="PEO"
                    endpoint="/curriculum/peo-vision-mappings"
                    ownIdField="program_vision_id"
                    ownId={selectedProgVisionId}
                    targetIdField="peo_id"
                    targetOptions={peoOptions}
                    targetLabelById={peoLabelById}
                    mappings={peoVisionMappings ?? []}
                    canManage={canManage}
                    queryKey={['curriculum', 'peo-vision-mappings-by-vision', selectedProgVisionId]}
                  />
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      <EntityFormDialog
        open={missionDialogOpen}
        onOpenChange={setMissionDialogOpen}
        title="Add institutional mission statement"
        fields={[{ name: 'statement', label: 'Statement', type: 'textarea' } as EntityField]}
        schema={missionSchema}
        defaultValues={{ statement: '' }}
        onSubmit={async (values) => {
          try {
            await createMission.mutateAsync({ statement: values.statement })
            toast.success('Mission statement added')
          } catch (err) {
            throw err instanceof ApiError ? err : new ApiError('Unable to add mission statement.')
          }
        }}
      />

      <EntityFormDialog
        open={visionDialogOpen}
        onOpenChange={setVisionDialogOpen}
        title="New institutional vision"
        fields={[
          { name: 'label', label: 'Label', type: 'text', placeholder: 'e.g. V1' },
          { name: 'statement', label: 'Statement', type: 'textarea' },
          { name: 'sequence', label: 'Sequence', type: 'number' },
        ]}
        schema={visionSchema}
        defaultValues={{ label: '', statement: '', sequence: (visions ?? []).length + 1 }}
        onSubmit={async (values) => {
          try {
            await createVision.mutateAsync(values)
            toast.success('Institutional vision created')
          } catch (err) {
            throw err instanceof ApiError ? err : new ApiError('Unable to create vision.')
          }
        }}
      />

      <EntityFormDialog
        open={progMissionDialogOpen}
        onOpenChange={setProgMissionDialogOpen}
        title="Add program mission statement"
        fields={[{ name: 'statement', label: 'Statement', type: 'textarea' } as EntityField]}
        schema={missionSchema}
        defaultValues={{ statement: '' }}
        onSubmit={async (values) => {
          try {
            await createProgMission.mutateAsync({
              program_version_id: programVersionId,
              statement: values.statement,
            })
            toast.success('Program mission statement added')
          } catch (err) {
            throw err instanceof ApiError ? err : new ApiError('Unable to add mission statement.')
          }
        }}
      />

      <EntityFormDialog
        open={progVisionDialogOpen}
        onOpenChange={setProgVisionDialogOpen}
        title="New program vision"
        fields={[
          { name: 'label', label: 'Label', type: 'text', placeholder: 'e.g. PV1' },
          { name: 'statement', label: 'Statement', type: 'textarea' },
          { name: 'sequence', label: 'Sequence', type: 'number' },
        ]}
        schema={visionSchema}
        defaultValues={{ label: '', statement: '', sequence: (progVisions ?? []).length + 1 }}
        onSubmit={async (values) => {
          try {
            await createProgVision.mutateAsync({ ...values, program_version_id: programVersionId })
            toast.success('Program vision created')
          } catch (err) {
            throw err instanceof ApiError ? err : new ApiError('Unable to create vision.')
          }
        }}
      />
    </div>
  )
}
