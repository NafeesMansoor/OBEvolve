import * as React from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { ChevronDown, ChevronRight, ClipboardList, Save } from 'lucide-react'
import { toast } from 'sonner'

import { useAuth } from '@/features/auth/useAuth'
import type { ProgramAttainmentConfig, ProgramAttainmentReport } from '@/features/assessment/types'
import type { ProgramVersion } from '@/features/organization/types'
import { ApiError, apiClient } from '@/lib/api-client'
import { useEntityGet, useEntityList } from '@/lib/crud-hooks'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'

/** PO attainment rolled up from every course_section currently offered
 * under a program version — see app.services.attainment's docstring for the
 * methodology (weighted average of mapped COs' attainment %, weighted by
 * mapping strength; cohort/student-level PO status are out of scope for
 * this pass). Calculated fresh on every view, no stored "run" history. */
export function POAttainmentTab() {
  const { hasPermission } = useAuth()
  const canConfig = hasPermission('program.manage') || hasPermission('attainment.calculate')

  const { data: versions } = useEntityList<ProgramVersion>(
    ['org', 'program-versions'],
    '/org/program-versions',
  )
  const [versionId, setVersionId] = React.useState('')
  const activeVersionId = versionId || versions?.[0]?.id || ''

  const versionOptions = React.useMemo(
    () => (versions ?? []).map((v) => ({ label: `${v.version_label} (${v.status})`, value: v.id })),
    [versions],
  )

  const { data: config, isLoading: configLoading } = useEntityGet<ProgramAttainmentConfig | null>(
    ['marks', 'program-attainment-config', activeVersionId],
    `/marks/program-attainment-config?program_version_id=${activeVersionId}`,
    { enabled: Boolean(activeVersionId) },
  )

  const {
    data: report,
    isLoading: reportLoading,
    error: reportError,
  } = useEntityGet<ProgramAttainmentReport>(
    ['marks', 'program-attainment-report', activeVersionId],
    `/marks/program-attainment-report?program_version_id=${activeVersionId}`,
    { enabled: Boolean(activeVersionId) },
  )

  return (
    <div className="flex flex-col gap-4">
      <div className="w-full max-w-md">
        <Select value={activeVersionId} onValueChange={setVersionId}>
          <SelectTrigger>
            <SelectValue placeholder="Select a curriculum version" />
          </SelectTrigger>
          <SelectContent>
            {versionOptions.map((o) => (
              <SelectItem key={o.value} value={o.value}>
                {o.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {!activeVersionId ? (
        <p className="text-sm text-muted-foreground">Select a curriculum version to see PO attainment.</p>
      ) : (
        <>
          {configLoading ? (
            <Skeleton className="h-20 w-full max-w-md" />
          ) : (
            <ConfigPanel
              key={activeVersionId}
              programVersionId={activeVersionId}
              config={config ?? null}
              canConfig={canConfig}
            />
          )}

          {reportLoading ? (
            <div className="flex flex-col gap-2">
              <Skeleton className="h-4 w-72" />
              <Skeleton className="h-64 w-full" />
            </div>
          ) : reportError ? (
            <p className="text-sm text-destructive">
              {reportError instanceof ApiError ? reportError.detail : 'Unable to load PO attainment.'}
            </p>
          ) : report ? (
            <div className="flex flex-col gap-2">
              <p className="text-sm text-muted-foreground">
                Rolled up from {report.sections_included} course section
                {report.sections_included === 1 ? '' : 's'} currently offered under this curriculum
                version · threshold:{' '}
                <span className="font-medium text-foreground tabular-nums">
                  {report.min_po_attainment_percent}%
                </span>
              </p>
              <ReportTable outcomes={report.outcomes} />
            </div>
          ) : null}
        </>
      )}
    </div>
  )
}

function ConfigPanel({
  programVersionId,
  config,
  canConfig,
}: {
  programVersionId: string
  config: ProgramAttainmentConfig | null
  canConfig: boolean
}) {
  const queryClient = useQueryClient()
  const [minPercent, setMinPercent] = React.useState(config?.min_po_attainment_percent ?? '60')
  const [saving, setSaving] = React.useState(false)

  async function save() {
    setSaving(true)
    try {
      await apiClient.put('/marks/program-attainment-config', {
        program_version_id: programVersionId,
        min_po_attainment_percent: minPercent,
      })
      await queryClient.invalidateQueries({
        queryKey: ['marks', 'program-attainment-config', programVersionId],
      })
      toast.success('PO attainment threshold saved')
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Unable to save threshold.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Card className="max-w-md">
      <CardContent className="flex flex-wrap items-end gap-3 py-4">
        <div>
          <Label htmlFor="min-po-attainment" className="text-xs text-muted-foreground">
            Min PO attainment %
          </Label>
          <Input
            id="min-po-attainment"
            type="number"
            step="1"
            min={0}
            max={100}
            value={minPercent}
            onChange={(e) => setMinPercent(e.target.value)}
            disabled={!canConfig}
            className="mt-1 h-9 w-28 tabular-nums"
          />
        </div>
        {canConfig && (
          <Button size="sm" onClick={() => void save()} disabled={saving}>
            <Save className="size-4" /> {saving ? 'Saving…' : 'Save threshold'}
          </Button>
        )}
        {!config && <p className="text-xs text-muted-foreground">Using default 60% until saved.</p>}
      </CardContent>
    </Card>
  )
}

function ReportTable({ outcomes }: { outcomes: ProgramAttainmentReport['outcomes'] }) {
  const [expanded, setExpanded] = React.useState<Set<string>>(new Set())

  function toggle(id: string) {
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  if (outcomes.length === 0) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center gap-2 py-12 text-center text-muted-foreground">
          <ClipboardList className="size-6 opacity-50" />
          <p className="text-sm">No program outcomes defined for this curriculum version yet.</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardContent className="overflow-x-auto p-0">
        <table className="w-full text-sm">
        <thead className="bg-muted">
          <tr>
            <th className="w-8 px-2 py-2" />
            <th className="px-3 py-2 text-left font-semibold">PO</th>
            <th className="px-3 py-2 text-left font-semibold">Statement</th>
            <th className="px-3 py-2 text-left font-semibold">Attainment %</th>
            <th className="px-3 py-2 text-left font-semibold">Result</th>
          </tr>
        </thead>
        <tbody>
          {outcomes.map((po) => {
            const isOpen = expanded.has(po.program_outcome_id)
            return (
              <React.Fragment key={po.program_outcome_id}>
                <tr
                  className="cursor-pointer border-t hover:bg-muted/30"
                  onClick={() => toggle(po.program_outcome_id)}
                >
                  <td className="px-2 py-2 text-muted-foreground">
                    {isOpen ? <ChevronDown className="size-4" /> : <ChevronRight className="size-4" />}
                  </td>
                  <td className="px-3 py-2 font-medium whitespace-nowrap">{po.code}</td>
                  <td className="px-3 py-2">{po.statement}</td>
                  <td className="px-3 py-2 whitespace-nowrap font-medium tabular-nums">
                    {po.assessed ? `${Number(po.attainment_percent).toFixed(1)}%` : '—'}
                  </td>
                  <td className="px-3 py-2">
                    {!po.assessed ? (
                      <Badge variant="outline" className="font-normal">
                        Not assessed
                      </Badge>
                    ) : (
                      <Badge variant={po.is_attained ? 'secondary' : 'destructive'} className="font-normal">
                        {po.is_attained ? 'Attained' : 'Not attained'}
                      </Badge>
                    )}
                  </td>
                </tr>
                {isOpen && (
                  <tr className="border-t bg-muted/10">
                    <td colSpan={5} className="px-3 py-3">
                      {po.contributions.length === 0 ? (
                        <p className="text-xs text-muted-foreground">No COs mapped to this PO.</p>
                      ) : (
                        <table className="w-full text-xs">
                          <thead>
                            <tr className="text-muted-foreground">
                              <th className="px-2 py-1 text-left font-medium">Course</th>
                              <th className="px-2 py-1 text-left font-medium">CO</th>
                              <th className="px-2 py-1 text-left font-medium">Mapping strength</th>
                              <th className="px-2 py-1 text-left font-medium">CO attainment %</th>
                            </tr>
                          </thead>
                          <tbody>
                            {po.contributions.map((c) => (
                              <tr key={c.course_outcome_id} className="border-t border-border/50">
                                <td className="px-2 py-1">{c.course_code}</td>
                                <td className="px-2 py-1">{c.co_code}</td>
                                <td className="px-2 py-1">{c.mapping_strength}</td>
                                <td className="px-2 py-1">
                                  {c.co_attainment_percent === null
                                    ? 'not assessed'
                                    : `${Number(c.co_attainment_percent).toFixed(1)}%`}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      )}
                    </td>
                  </tr>
                )}
              </React.Fragment>
            )
          })}
        </tbody>
        </table>
      </CardContent>
    </Card>
  )
}
