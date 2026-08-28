import * as React from 'react'
import { CheckCircle2, ClipboardCheck, Download, XCircle } from 'lucide-react'
import { toast } from 'sonner'

import type { PendingAssessmentDocument } from '@/features/assessment/types'
import { ApiError, apiClient } from '@/lib/api-client'
import { useActiveProgram } from '@/lib/active-program-context'
import { useEntityList } from '@/lib/crud-hooks'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'

const DOCUMENT_TYPE_LABELS: Record<string, string> = {
  question_paper: 'Question paper',
  moderation_form: 'Moderation form',
  compliance_form: 'Compliance form',
  script_highest: 'Highest-scoring script',
  script_lowest: 'Lowest-scoring script',
  script_median: 'Median-scoring script',
  problem_definition: 'Problem definition document',
  marked_rubric_sample: 'Marked rubric sample',
  project_report: 'Project report',
}

async function download(id: string, fileName: string) {
  try {
    const response = await apiClient.get(`/assessment/documents/${id}/download`, { responseType: 'blob' })
    const url = URL.createObjectURL(response.data as Blob)
    const link = document.createElement('a')
    link.href = url
    link.download = fileName
    link.click()
    URL.revokeObjectURL(url)
  } catch {
    toast.error('Unable to download this document.')
  }
}

/**
 * The dedicated "everything I need to review" surface for Course
 * Coordinators / Program Administrators (assessment.approve) — spec:
 * "the course coordinator and the program administration's ui should have a
 * separate option where all the pending stuff should be shown". Scoped to
 * the active program by get_program_scoped_db server-side (X-Program-Code).
 */
export function PendingDocumentsTab() {
  // Program-scoped endpoint, and TabsContent stays mounted (just hidden)
  // even when this isn't the active tab — must wait for the active program
  // to resolve or this fires (and 400s) before X-Program-Code is ever set.
  const { activeProgramCode } = useActiveProgram()
  const { data, isLoading, refetch } = useEntityList<PendingAssessmentDocument>(
    ['assessment', 'documents', 'pending'],
    '/assessment/documents/pending',
    undefined,
    { enabled: Boolean(activeProgramCode) },
  )
  const [reviewingId, setReviewingId] = React.useState<string | null>(null)
  const [note, setNote] = React.useState('')

  async function review(docId: string, status: 'approved' | 'rejected') {
    try {
      await apiClient.post(`/assessment/documents/${docId}/review`, { status, review_note: note || null })
      await refetch()
      toast.success(status === 'approved' ? 'Document approved' : 'Document rejected')
      setReviewingId(null)
      setNote('')
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Unable to submit review.')
    }
  }

  if (isLoading) {
    return (
      <div className="flex flex-col gap-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <Skeleton key={i} className="h-20 w-full" />
        ))}
      </div>
    )
  }

  if (!data || data.length === 0) {
    return (
      <div className="flex flex-col items-center gap-2 rounded-md border border-dashed py-10 text-center text-muted-foreground">
        <ClipboardCheck className="size-6 opacity-50" />
        <p className="text-sm">Nothing pending review right now.</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-3">
      {data.map((item) => (
        <Card key={item.document.id}>
          <CardContent className="flex flex-col gap-2.5 py-4">
            <div className="flex flex-wrap items-start justify-between gap-2">
              <div>
                <p className="text-sm font-medium">{item.assessment_title}</p>
                <p className="text-xs text-muted-foreground">
                  {DOCUMENT_TYPE_LABELS[item.document.document_type] ?? item.document.document_type} ·{' '}
                  {item.document.file_name} · {(item.document.file_size / 1024).toFixed(0)} KB
                </p>
              </div>
              <div className="flex shrink-0 items-center gap-1.5">
                <Badge variant="outline" className="border-transparent bg-warning/15 text-warning">
                  pending
                </Badge>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => download(item.document.id, item.document.file_name)}
                  aria-label="Download"
                >
                  <Download className="size-3.5" />
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setReviewingId(reviewingId === item.document.id ? null : item.document.id)}
                >
                  Review
                </Button>
              </div>
            </div>

            {reviewingId === item.document.id && (
              <div className="flex flex-col gap-2 border-t pt-2.5">
                <Textarea
                  placeholder="Optional review note"
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  className="min-h-[52px] text-sm"
                />
                <div className="flex justify-end gap-2">
                  <Button size="sm" variant="destructive" onClick={() => review(item.document.id, 'rejected')}>
                    <XCircle className="size-3.5" />
                    Reject
                  </Button>
                  <Button
                    size="sm"
                    className="bg-success text-success-foreground hover:bg-success/90"
                    onClick={() => review(item.document.id, 'approved')}
                  >
                    <CheckCircle2 className="size-3.5" />
                    Approve
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  )
}
