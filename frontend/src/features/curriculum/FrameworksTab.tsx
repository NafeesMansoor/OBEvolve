import * as React from 'react'
import { Inbox, Layers } from 'lucide-react'

import type {
  AccreditationFramework,
  EngineeringActivity,
  FrameworkDetail,
  KnowledgeProfile,
  ProblemAttribute,
} from '@/features/curriculum/types'
import { useEntityGet, useEntityList } from '@/lib/crud-hooks'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Skeleton } from '@/components/ui/skeleton'

/** Read-only accreditation framework viewer — POs, Knowledge Profiles,
 * Problem Attributes, and Engineering Activities for the selected
 * framework (e.g. BAETE v3.0). */
export function FrameworksTab() {
  const { data: frameworks, isLoading } = useEntityList<AccreditationFramework>(
    ['curriculum', 'frameworks'],
    '/curriculum/frameworks',
  )
  const [frameworkId, setFrameworkId] = React.useState('')

  // Default to the first framework once the list loads. Adjusted directly
  // during render (React's documented pattern) rather than in an effect —
  // this only fires once since frameworkId becomes truthy immediately.
  if (!frameworkId && frameworks && frameworks.length > 0) {
    setFrameworkId(frameworks[0].id)
  }

  const { data: detail } = useEntityGet<FrameworkDetail>(
    ['curriculum', 'frameworks', frameworkId],
    `/curriculum/frameworks/${frameworkId}`,
    { enabled: Boolean(frameworkId) },
  )
  const { data: knowledgeProfiles } = useEntityList<KnowledgeProfile>(
    ['curriculum', 'frameworks', frameworkId, 'knowledge-profiles'],
    `/curriculum/frameworks/${frameworkId}/knowledge-profiles`,
    undefined,
    { enabled: Boolean(frameworkId) },
  )
  const { data: problemAttributes } = useEntityList<ProblemAttribute>(
    ['curriculum', 'frameworks', frameworkId, 'problem-attributes'],
    `/curriculum/frameworks/${frameworkId}/problem-attributes`,
    undefined,
    { enabled: Boolean(frameworkId) },
  )
  const { data: engineeringActivities } = useEntityList<EngineeringActivity>(
    ['curriculum', 'frameworks', frameworkId, 'engineering-activities'],
    `/curriculum/frameworks/${frameworkId}/engineering-activities`,
    undefined,
    { enabled: Boolean(frameworkId) },
  )

  if (isLoading) {
    return (
      <div className="flex flex-col gap-4">
        <Skeleton className="h-9 w-full max-w-sm" />
        <Skeleton className="h-9 w-full max-w-md" />
        <Skeleton className="h-64 w-full" />
      </div>
    )
  }

  if (!frameworks || frameworks.length === 0) {
    return (
      <div className="flex flex-col items-center gap-2 rounded-md border border-dashed py-12 text-muted-foreground">
        <Layers className="size-6 opacity-50" />
        <span className="text-sm">No accreditation frameworks configured.</span>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="w-full max-w-sm">
          <Select value={frameworkId} onValueChange={setFrameworkId}>
            <SelectTrigger>
              <SelectValue placeholder="Select a framework" />
            </SelectTrigger>
            <SelectContent>
              {frameworks.map((f) => (
                <SelectItem key={f.id} value={f.id}>
                  {f.name} v{f.version}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        {detail && (
          <Badge variant={detail.is_active ? 'secondary' : 'outline'} className="font-normal">
            {detail.is_active ? 'Active' : 'Inactive'} · effective {detail.effective_date}
          </Badge>
        )}
      </div>

      {detail?.description && <p className="text-sm text-muted-foreground">{detail.description}</p>}

      <Tabs defaultValue="pos">
        <TabsList>
          <TabsTrigger value="pos">Program Outcomes (POs)</TabsTrigger>
          <TabsTrigger value="wk">Knowledge Profiles (WK)</TabsTrigger>
          <TabsTrigger value="wp">Problem Attributes (WP)</TabsTrigger>
          <TabsTrigger value="ea">Engineering Activities (EA)</TabsTrigger>
        </TabsList>

        <TabsContent value="pos">
          <FrameworkTable
            rows={(detail?.framework_pos ?? []).map((r) => ({
              code: r.code,
              text: r.statement,
              key: r.id,
            }))}
          />
        </TabsContent>
        <TabsContent value="wk">
          <FrameworkTable
            rows={(knowledgeProfiles ?? []).map((r) => ({
              code: r.code,
              text: r.title ? `${r.title} — ${r.description}` : r.description,
              key: r.id,
            }))}
          />
        </TabsContent>
        <TabsContent value="wp">
          <FrameworkTable
            rows={(problemAttributes ?? []).map((r) => ({
              code: r.code,
              text: r.title ? `${r.title} — ${r.description}` : r.description,
              key: r.id,
            }))}
          />
        </TabsContent>
        <TabsContent value="ea">
          <FrameworkTable
            rows={(engineeringActivities ?? []).map((r) => ({
              code: r.code,
              text: r.title ? `${r.title} — ${r.description}` : r.description,
              key: r.id,
            }))}
          />
        </TabsContent>
      </Tabs>
    </div>
  )
}

function FrameworkTable({ rows }: { rows: { key: string; code: string; text: string }[] }) {
  return (
    <Card>
      <CardHeader className="py-3">
        <CardTitle className="text-sm text-muted-foreground">{rows.length} entries</CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-20">Code</TableHead>
              <TableHead>Statement</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {rows.length === 0 ? (
              <TableRow>
                <TableCell colSpan={2} className="py-8 text-center">
                  <div className="flex flex-col items-center gap-1.5 text-muted-foreground">
                    <Inbox className="size-5 opacity-50" />
                    <span className="text-sm">Nothing to show.</span>
                  </div>
                </TableCell>
              </TableRow>
            ) : (
              rows.map((r) => (
                <TableRow key={r.key}>
                  <TableCell className="font-medium">{r.code}</TableCell>
                  <TableCell>{r.text}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}
