import * as React from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { Lock, LockOpen } from 'lucide-react'
import { toast } from 'sonner'

import { useAcademicTermLookup } from '@/features/academic-ops/useLookups'
import type { TermCommitStatus } from '@/features/organization/types'
import { ApiError, apiClient } from '@/lib/api-client'
import { useEntityGet } from '@/lib/crud-hooks'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ConfirmAction } from '@/components/confirm-action'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Switch } from '@/components/ui/switch'

/** Final Commit (docs/course_level_settings_and_approval_workflow.md's
 * follow-up): once a Program Administrator commits a term, assessments/
 * marks/attainment for that term are permanently locked in this program —
 * see `app.services.term_commit`'s docstring. Before commit, faculty have
 * full write access regardless of assessment/grade-submission status
 * (published assessments un-publish on edit, submitted grades un-submit on
 * edit) — this panel is only about the one hard, permanent gate. */
export function FinalCommitTab() {
  const queryClient = useQueryClient()
  const { terms } = useAcademicTermLookup()
  const [manuallySelectedTermId, setManuallySelectedTermId] = React.useState('')
  // Defaults to the active term without needing an effect+setState round
  // trip — falls back to it (or the first term) whenever nothing's been
  // explicitly picked yet, and just as terms load asynchronously.
  const selectedTermId =
    manuallySelectedTermId || terms.find((t) => t.is_active)?.id || terms[0]?.id || ''

  const queryKey = ['term-commit', selectedTermId]
  const { data: commitStatus, isLoading } = useEntityGet<TermCommitStatus>(
    queryKey,
    `/term-commit/${selectedTermId}`,
    { enabled: Boolean(selectedTermId) },
  )

  async function toggleEarlyEnable(enabled: boolean) {
    try {
      await apiClient.post(`/term-commit/${selectedTermId}/enable-early`, { enabled })
      await queryClient.invalidateQueries({ queryKey })
      toast.success(enabled ? 'Early commit enabled' : 'Early commit disabled')
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Unable to update.')
    }
  }

  async function doCommit() {
    try {
      await apiClient.post(`/term-commit/${selectedTermId}/commit`)
      await queryClient.invalidateQueries({ queryKey })
      toast.success(`${commitStatus?.term_name ?? 'Term'} committed`)
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Unable to commit.')
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <p className="text-sm text-muted-foreground">
        Committing a term permanently locks every assessment, marks entry, and attainment write
        for that term in this program. Before commit, faculty have full access to change
        assessments and marks regardless of publish/submission status.
      </p>

      <div className="w-full max-w-sm">
        <Select value={selectedTermId} onValueChange={setManuallySelectedTermId}>
          <SelectTrigger>
            <SelectValue placeholder="Select a term" />
          </SelectTrigger>
          <SelectContent>
            {terms.map((t) => (
              <SelectItem key={t.id} value={t.id}>
                {t.name} {t.is_active ? '(current)' : ''}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {isLoading || !commitStatus ? (
        <Skeleton className="h-40 w-full" />
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              {commitStatus.term_name}
              {commitStatus.is_committed ? (
                <Badge className="bg-destructive/10 text-destructive">
                  <Lock className="mr-1 size-3" /> Committed
                </Badge>
              ) : (
                <Badge variant="outline" className="font-normal">
                  <LockOpen className="mr-1 size-3" /> Open
                </Badge>
              )}
            </CardTitle>
            <CardDescription>Ends {commitStatus.term_end_date}</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            {commitStatus.is_committed ? (
              <p className="text-sm text-muted-foreground">
                Committed{commitStatus.committed_at ? ` on ${new Date(commitStatus.committed_at).toLocaleString()}` : ''}.
                This is permanent — no further changes are possible for this term in this program.
              </p>
            ) : (
              <>
                <label className="flex items-center justify-between gap-2 rounded-md border px-3 py-2 text-sm">
                  <span>
                    Allow committing before the term ends
                    <span className="block text-xs text-muted-foreground">
                      Without this, Final Commit only becomes available after {commitStatus.term_end_date}.
                    </span>
                  </span>
                  <Switch
                    checked={commitStatus.manually_enabled}
                    onCheckedChange={(checked) => void toggleEarlyEnable(checked)}
                  />
                </label>

                <ConfirmAction
                  trigger={
                    <Button variant="destructive" disabled={!commitStatus.committable} className="self-start">
                      <Lock className="size-4" /> Final Commit
                    </Button>
                  }
                  title={`Permanently commit ${commitStatus.term_name}?`}
                  description="This cannot be undone. Every assessment, marks entry, and attainment calculation for this term in this program will be locked from further changes."
                  confirmLabel="Commit permanently"
                  onConfirm={doCommit}
                />
                {!commitStatus.committable && (
                  <p className="text-xs text-muted-foreground">
                    Not committable yet — the term hasn't ended and early commit isn't enabled.
                  </p>
                )}
              </>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}
