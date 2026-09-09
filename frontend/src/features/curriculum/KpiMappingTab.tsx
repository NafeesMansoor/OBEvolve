import * as React from 'react'
import { Plus, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { z } from 'zod'

import { useAuth } from '@/features/auth/useAuth'
import type {
  AccreditationFramework,
  EngineeringActivity,
  KnowledgeProfile,
  MappingScale,
  ProblemAttribute,
  ProgramOutcome,
  ProgramOutcomeEngineeringActivityMapping,
  ProgramOutcomeKnowledgeProfileMapping,
  ProgramOutcomeProblemAttributeMapping,
} from '@/features/curriculum/types'
import { useProgramVersionOptions } from '@/features/curriculum/useProgramVersionOptions'
import { ApiError } from '@/lib/api-client'
import { useEntityCreate, useEntityDelete, useEntityList } from '@/lib/crud-hooks'
import { Button } from '@/components/ui/button'
import { EntityFormDialog, type EntityField } from '@/components/entity-form-dialog'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

const schema = z.object({
  target_id: z.string().min(1, 'Required'),
  mapping_scale_level_id: z.string().min(1, 'Required'),
  remarks: z.string().optional(),
})

interface MappingRow {
  id: string
  mapping_scale_level_id: string
  remarks: string | null
}

function MappingSection<T extends MappingRow>({
  title,
  endpoint,
  targetOptions,
  targetIdField,
  targetLabelById,
  scaleLevelOptions,
  mappings,
  programOutcomeId,
  canManage,
  queryKey,
}: {
  title: string
  endpoint: string
  targetOptions: { label: string; value: string }[]
  targetIdField: string
  targetLabelById: Map<string, string>
  scaleLevelOptions: { label: string; value: string }[]
  mappings: T[]
  programOutcomeId: string
  canManage: boolean
  queryKey: unknown[]
}) {
  const [open, setOpen] = React.useState(false)
  const create = useEntityCreate<Record<string, unknown>, T>(endpoint, [queryKey])
  const remove = useEntityDelete((id) => `${endpoint}/${id}`, [queryKey])

  const fields: EntityField[] = [
    { name: 'target_id', label: title, type: 'select', options: targetOptions },
    { name: 'mapping_scale_level_id', label: 'Correlation level', type: 'select', options: scaleLevelOptions },
    { name: 'remarks', label: 'Remarks (optional)', type: 'textarea' },
  ]

  return (
    <div className="flex flex-col gap-2 rounded-md border p-4">
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
                {targetLabelById.get((m as unknown as Record<string, string>)[targetIdField]) ?? 'Unknown'}
                {m.remarks ? <span className="text-muted-foreground"> — {m.remarks}</span> : null}
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
        title={`Map to a ${title}`}
        fields={fields}
        schema={schema}
        defaultValues={{ target_id: '', mapping_scale_level_id: '', remarks: '' }}
        onSubmit={async (values) => {
          try {
            await create.mutateAsync({
              program_outcome_id: programOutcomeId,
              [targetIdField]: values.target_id,
              mapping_scale_level_id: values.mapping_scale_level_id,
              remarks: values.remarks || null,
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

/** PO <-> Knowledge Profile / Complex Engineering Problem / Complex
 * Engineering Activity mapping (spec §17/§19). Scoped to a Program
 * Outcome — the same "exactly one of PO or PI" constraint the backend
 * enforces applies here too, but this view only ever submits program_outcome_id
 * (a parallel PI-scoped view can reuse the same MappingSection once PI
 * selection is wired in elsewhere). */
export function KpiMappingTab() {
  const { hasPermission } = useAuth()
  const canManage = hasPermission('program_outcome_framework.manage')
  const { options: pvOptions } = useProgramVersionOptions()
  const [programVersionId, setProgramVersionId] = React.useState('')
  const [programOutcomeId, setProgramOutcomeId] = React.useState('')

  const { data: outcomes } = useEntityList<ProgramOutcome>(
    ['curriculum', 'program-outcomes', programVersionId],
    '/curriculum/program-outcomes',
    { program_version_id: programVersionId || undefined },
    { enabled: Boolean(programVersionId) },
  )

  const { data: frameworks } = useEntityList<AccreditationFramework>(['curriculum', 'frameworks'], '/curriculum/frameworks')
  const frameworkId = frameworks?.[0]?.id ?? ''
  const { data: kps } = useEntityList<KnowledgeProfile>(
    ['curriculum', 'frameworks', frameworkId, 'knowledge-profiles'],
    `/curriculum/frameworks/${frameworkId}/knowledge-profiles`,
    undefined,
    { enabled: Boolean(frameworkId) },
  )
  const { data: ceps } = useEntityList<ProblemAttribute>(
    ['curriculum', 'frameworks', frameworkId, 'problem-attributes'],
    `/curriculum/frameworks/${frameworkId}/problem-attributes`,
    undefined,
    { enabled: Boolean(frameworkId) },
  )
  const { data: ceas } = useEntityList<EngineeringActivity>(
    ['curriculum', 'frameworks', frameworkId, 'engineering-activities'],
    `/curriculum/frameworks/${frameworkId}/engineering-activities`,
    undefined,
    { enabled: Boolean(frameworkId) },
  )
  const { data: scales } = useEntityList<MappingScale>(['curriculum', 'mapping-scales'], '/curriculum/mapping-scales')
  const scaleLevelOptions = React.useMemo(
    () =>
      (scales ?? []).flatMap((s) => s.levels.map((l) => ({ label: `${s.name}: ${l.label}`, value: l.id }))),
    [scales],
  )

  const { data: kpMappings } = useEntityList<ProgramOutcomeKnowledgeProfileMapping>(
    ['curriculum', 'po-knowledge-profile-mappings', programOutcomeId],
    '/curriculum/po-knowledge-profile-mappings',
    { program_outcome_id: programOutcomeId || undefined },
    { enabled: Boolean(programOutcomeId) },
  )
  const { data: cepMappings } = useEntityList<ProgramOutcomeProblemAttributeMapping>(
    ['curriculum', 'po-problem-attribute-mappings', programOutcomeId],
    '/curriculum/po-problem-attribute-mappings',
    { program_outcome_id: programOutcomeId || undefined },
    { enabled: Boolean(programOutcomeId) },
  )
  const { data: ceaMappings } = useEntityList<ProgramOutcomeEngineeringActivityMapping>(
    ['curriculum', 'po-engineering-activity-mappings', programOutcomeId],
    '/curriculum/po-engineering-activity-mappings',
    { program_outcome_id: programOutcomeId || undefined },
    { enabled: Boolean(programOutcomeId) },
  )

  const kpLabelById = React.useMemo(() => new Map((kps ?? []).map((k) => [k.id, `${k.code} — ${k.title ?? ''}`])), [kps])
  const cepLabelById = React.useMemo(() => new Map((ceps ?? []).map((k) => [k.id, `${k.code} — ${k.title ?? ''}`])), [ceps])
  const ceaLabelById = React.useMemo(() => new Map((ceas ?? []).map((k) => [k.id, `${k.code} — ${k.title ?? ''}`])), [ceas])

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center gap-2">
        <div className="w-full max-w-sm">
          <Select
            value={programVersionId}
            onValueChange={(v) => {
              setProgramVersionId(v)
              setProgramOutcomeId('')
            }}
          >
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
        {programVersionId && (
          <div className="w-full max-w-sm">
            <Select value={programOutcomeId} onValueChange={setProgramOutcomeId}>
              <SelectTrigger>
                <SelectValue placeholder="Select a program outcome" />
              </SelectTrigger>
              <SelectContent>
                {(outcomes ?? []).map((o) => (
                  <SelectItem key={o.id} value={o.id}>
                    {o.code}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}
      </div>

      {!programOutcomeId ? (
        <p className="text-sm text-muted-foreground">
          Select a program outcome to map it to Knowledge Profiles, Complex Engineering Problems,
          and Complex Engineering Activities.
        </p>
      ) : (
        <div className="grid gap-4 md:grid-cols-3">
          <MappingSection
            title="Knowledge Profile"
            endpoint="/curriculum/po-knowledge-profile-mappings"
            targetOptions={(kps ?? []).map((k) => ({ label: `${k.code} — ${k.title ?? ''}`, value: k.id }))}
            targetIdField="knowledge_profile_id"
            targetLabelById={kpLabelById}
            scaleLevelOptions={scaleLevelOptions}
            mappings={kpMappings ?? []}
            programOutcomeId={programOutcomeId}
            canManage={canManage}
            queryKey={['curriculum', 'po-knowledge-profile-mappings', programOutcomeId]}
          />
          <MappingSection
            title="Complex Engineering Problem"
            endpoint="/curriculum/po-problem-attribute-mappings"
            targetOptions={(ceps ?? []).map((k) => ({ label: `${k.code} — ${k.title ?? ''}`, value: k.id }))}
            targetIdField="problem_attribute_id"
            targetLabelById={cepLabelById}
            scaleLevelOptions={scaleLevelOptions}
            mappings={cepMappings ?? []}
            programOutcomeId={programOutcomeId}
            canManage={canManage}
            queryKey={['curriculum', 'po-problem-attribute-mappings', programOutcomeId]}
          />
          <MappingSection
            title="Complex Engineering Activity"
            endpoint="/curriculum/po-engineering-activity-mappings"
            targetOptions={(ceas ?? []).map((k) => ({ label: `${k.code} — ${k.title ?? ''}`, value: k.id }))}
            targetIdField="engineering_activity_id"
            targetLabelById={ceaLabelById}
            scaleLevelOptions={scaleLevelOptions}
            mappings={ceaMappings ?? []}
            programOutcomeId={programOutcomeId}
            canManage={canManage}
            queryKey={['curriculum', 'po-engineering-activity-mappings', programOutcomeId]}
          />
        </div>
      )}
    </div>
  )
}
