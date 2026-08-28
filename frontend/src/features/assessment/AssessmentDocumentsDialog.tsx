import * as React from 'react'
import { CalendarClock, CheckCircle2, Download, FileText, Plus, Trash2, Upload, XCircle } from 'lucide-react'
import { toast } from 'sonner'

import type {
  Assessment,
  AssessmentDocument,
  AssessmentDocumentType,
  AssessmentType,
} from '@/features/assessment/types'
import { ApiError, apiClient } from '@/lib/api-client'
import { useEntityList } from '@/lib/crud-hooks'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'

interface SlotDef {
  type: AssessmentDocumentType
  label: string
  /** Only meaningful for repeatable slots (see AssessmentDocument's backend docstring). */
  repeatable?: boolean
  minRequired: number
}

const EXAM_SLOTS: SlotDef[] = [
  { type: 'question_paper', label: 'Question paper', minRequired: 1 },
  { type: 'moderation_form', label: 'Moderation form', minRequired: 1 },
  { type: 'compliance_form', label: 'Compliance form', minRequired: 1 },
]
const SCRIPT_SLOTS: SlotDef[] = [
  { type: 'script_highest', label: 'Highest-scoring script', minRequired: 1 },
  { type: 'script_lowest', label: 'Lowest-scoring script', minRequired: 1 },
  { type: 'script_median', label: 'Median-scoring script', minRequired: 1 },
]
const CEP_SINGLETON_SLOTS: SlotDef[] = [
  { type: 'problem_definition', label: 'Problem definition document', minRequired: 1 },
]
const CEP_MULTI_SLOTS: SlotDef[] = [
  { type: 'marked_rubric_sample', label: 'Marked rubric sample', repeatable: true, minRequired: 1 },
  { type: 'project_report', label: 'Project report', repeatable: true, minRequired: 3 },
]

const STATUS_STYLES: Record<string, string> = {
  pending: 'bg-warning/15 text-warning border-transparent',
  approved: 'bg-success/15 text-success border-transparent',
  rejected: 'bg-destructive/15 text-destructive border-transparent',
}

async function downloadDocument(doc: AssessmentDocument) {
  try {
    const response = await apiClient.get(`/assessment/documents/${doc.id}/download`, {
      responseType: 'blob',
    })
    const url = URL.createObjectURL(response.data as Blob)
    const link = document.createElement('a')
    link.href = url
    link.download = doc.file_name
    link.click()
    URL.revokeObjectURL(url)
  } catch {
    toast.error('Unable to download this document.')
  }
}

function DocumentRow({
  doc,
  canReview,
  onReview,
  onDelete,
  canDelete,
}: {
  doc: AssessmentDocument
  canReview: boolean
  onReview: (docId: string, status: 'approved' | 'rejected', note: string) => Promise<void>
  onDelete?: () => void
  canDelete?: boolean
}) {
  const [reviewOpen, setReviewOpen] = React.useState(false)
  const [note, setNote] = React.useState('')
  const [submitting, setSubmitting] = React.useState(false)

  return (
    <div className="rounded-md border bg-muted/30 px-2.5 py-2">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="min-w-0">
          <p className="truncate text-xs font-medium">{doc.file_name}</p>
          <p className="text-[11px] text-muted-foreground">
            {(doc.file_size / 1024).toFixed(0)} KB
            {doc.review_note ? ` · ${doc.review_note}` : ''}
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-1.5">
          <Badge variant="outline" className={STATUS_STYLES[doc.status]}>
            {doc.status}
          </Badge>
          <Button size="sm" variant="ghost" onClick={() => downloadDocument(doc)} aria-label="Download">
            <Download className="size-3.5" />
          </Button>
          {canDelete && onDelete && (
            <Button size="sm" variant="ghost" onClick={onDelete} aria-label="Delete">
              <Trash2 className="size-3.5 text-destructive" />
            </Button>
          )}
          {canReview && doc.status === 'pending' && (
            <Button size="sm" variant="outline" onClick={() => setReviewOpen((v) => !v)}>
              Review
            </Button>
          )}
        </div>
      </div>
      {reviewOpen && (
        <div className="mt-2 flex flex-col gap-2 border-t pt-2">
          <Textarea
            placeholder="Optional review note"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            className="min-h-[48px] text-sm"
          />
          <div className="flex justify-end gap-2">
            <Button
              size="sm"
              variant="destructive"
              disabled={submitting}
              onClick={async () => {
                setSubmitting(true)
                await onReview(doc.id, 'rejected', note)
                setSubmitting(false)
                setReviewOpen(false)
              }}
            >
              <XCircle className="size-3.5" />
              Reject
            </Button>
            <Button
              size="sm"
              className="bg-success text-success-foreground hover:bg-success/90"
              disabled={submitting}
              onClick={async () => {
                setSubmitting(true)
                await onReview(doc.id, 'approved', note)
                setSubmitting(false)
                setReviewOpen(false)
              }}
            >
              <CheckCircle2 className="size-3.5" />
              Approve
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}

function DeadlineBanner({
  assessment,
  termEndDate,
  canExtend,
  onExtended,
}: {
  assessment: Assessment
  termEndDate: string | null
  canExtend: boolean
  onExtended: () => void
}) {
  const [extending, setExtending] = React.useState(false)
  const [newDeadline, setNewDeadline] = React.useState('')
  const effective = assessment.document_deadline_extended_to ?? termEndDate
  const isExtended = Boolean(assessment.document_deadline_extended_to)
  const isOverdue = effective ? new Date(effective) < new Date(new Date().toDateString()) : false

  async function submitExtend() {
    if (!newDeadline) return
    try {
      await apiClient.post(`/assessment/assessments/${assessment.id}/extend-document-deadline`, {
        new_deadline: newDeadline,
      })
      toast.success('Deadline extended')
      setExtending(false)
      setNewDeadline('')
      onExtended()
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Unable to extend deadline.')
    }
  }

  return (
    <div className="flex flex-col gap-2 rounded-md border border-dashed p-2.5 text-xs">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="flex items-center gap-1.5 text-muted-foreground">
          <CalendarClock className="size-3.5" />
          {effective ? (
            <>
              Documents due <span className="font-medium text-foreground">{effective}</span>
              {isExtended && ' (extended by a program administrator)'}
              {isOverdue && (
                <Badge variant="outline" className="ml-1.5 border-transparent bg-destructive/15 text-destructive">
                  Overdue
                </Badge>
              )}
            </>
          ) : (
            'No deadline on file for this term.'
          )}
        </span>
        {canExtend && !extending && (
          <Button size="sm" variant="outline" onClick={() => setExtending(true)}>
            Extend deadline
          </Button>
        )}
      </div>
      {extending && (
        <div className="flex items-center gap-2">
          <Input
            type="date"
            value={newDeadline}
            onChange={(e) => setNewDeadline(e.target.value)}
            className="h-8 w-40 text-xs"
          />
          <Button size="sm" onClick={submitExtend} disabled={!newDeadline}>
            Save
          </Button>
          <Button size="sm" variant="ghost" onClick={() => setExtending(false)}>
            Cancel
          </Button>
        </div>
      )}
    </div>
  )
}

function SlotSection({
  title,
  slots,
  byType,
  canManage,
  canReview,
  onUpload,
  onReview,
  onDelete,
  uploadingType,
}: {
  title: string
  slots: SlotDef[]
  byType: Map<string, AssessmentDocument[]>
  canManage: boolean
  canReview: boolean
  onUpload: (type: AssessmentDocumentType) => void
  onReview: (docId: string, status: 'approved' | 'rejected', note: string) => Promise<void>
  onDelete: (docId: string) => void
  uploadingType: AssessmentDocumentType | null
}) {
  return (
    <div className="flex flex-col gap-2.5">
      <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{title}</p>
      {slots.map((slot) => {
        const docs = byType.get(slot.type) ?? []
        const isUploading = uploadingType === slot.type
        const approvedCount = docs.filter((d) => d.status !== 'rejected').length
        const isComplete = approvedCount >= slot.minRequired

        return (
          <div key={slot.type} className="rounded-md border p-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <FileText className="size-4 text-muted-foreground" />
                <span className="text-sm font-medium">{slot.label}</span>
                {slot.repeatable && slot.minRequired > 1 && (
                  <span className="text-xs text-muted-foreground">(at least {slot.minRequired})</span>
                )}
                <Badge
                  variant="outline"
                  className={
                    isComplete
                      ? 'border-transparent bg-success/15 font-normal text-success'
                      : 'font-normal text-muted-foreground'
                  }
                >
                  {isComplete ? 'Complete' : `${docs.length}/${slot.minRequired}`}
                </Badge>
              </div>
              {canManage && (
                <Button size="sm" variant="outline" disabled={isUploading} onClick={() => onUpload(slot.type)}>
                  {slot.repeatable ? <Plus className="size-3.5" /> : <Upload className="size-3.5" />}
                  {isUploading
                    ? 'Uploading…'
                    : slot.repeatable
                      ? 'Add file'
                      : docs.length > 0
                        ? 'Replace'
                        : 'Upload'}
                </Button>
              )}
            </div>

            {docs.length > 0 && (
              <div className="mt-2 flex flex-col gap-1.5">
                {docs.map((doc) => (
                  <DocumentRow
                    key={doc.id}
                    doc={doc}
                    canReview={canReview}
                    onReview={onReview}
                    canDelete={Boolean(slot.repeatable) && canManage}
                    onDelete={() => onDelete(doc.id)}
                  />
                ))}
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

export function AssessmentDocumentsDialog({
  assessment,
  assessmentType,
  termEndDate,
  canManage,
  canReview,
  onClose,
}: {
  assessment: Assessment
  assessmentType: AssessmentType | undefined
  termEndDate: string | null
  canManage: boolean
  canReview: boolean
  onClose: () => void
}) {
  const assessmentId = assessment.id
  const {
    data: documents,
    isLoading,
    refetch,
  } = useEntityList<AssessmentDocument>(
    ['assessment', 'assessment-documents', assessmentId],
    `/assessment/assessments/${assessmentId}/documents`,
  )
  const byType = React.useMemo(() => {
    const map = new Map<string, AssessmentDocument[]>()
    for (const doc of documents ?? []) {
      const list = map.get(doc.document_type) ?? []
      list.push(doc)
      map.set(doc.document_type, list)
    }
    return map
  }, [documents])

  const [uploadingType, setUploadingType] = React.useState<AssessmentDocumentType | null>(null)
  const fileInputRef = React.useRef<HTMLInputElement | null>(null)
  const pendingUploadType = React.useRef<AssessmentDocumentType | null>(null)

  function triggerUpload(type: AssessmentDocumentType) {
    pendingUploadType.current = type
    fileInputRef.current?.click()
  }

  async function handleFileChosen(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    const type = pendingUploadType.current
    e.target.value = ''
    if (!file || !type) return

    setUploadingType(type)
    try {
      const form = new FormData()
      form.append('document_type', type)
      form.append('file', file)
      await apiClient.post(`/assessment/assessments/${assessmentId}/documents`, form)
      await refetch()
      toast.success('Document uploaded')
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Unable to upload this document.')
    } finally {
      setUploadingType(null)
    }
  }

  async function review(docId: string, status: 'approved' | 'rejected', note: string) {
    try {
      await apiClient.post(`/assessment/documents/${docId}/review`, { status, review_note: note || null })
      await refetch()
      toast.success(status === 'approved' ? 'Document approved' : 'Document rejected')
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Unable to submit review.')
    }
  }

  async function remove(docId: string) {
    try {
      await apiClient.delete(`/assessment/documents/${docId}`)
      await refetch()
      toast.success('Document removed')
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Unable to remove this document.')
    }
  }

  const sections: { title: string; slots: SlotDef[] }[] = []
  if (assessmentType?.requires_documents) sections.push({ title: 'Exam-office documents', slots: EXAM_SLOTS })
  sections.push({ title: 'Answer scripts', slots: SCRIPT_SLOTS })
  if (assessmentType?.requires_cep_documents) {
    sections.push({ title: 'CEP documents', slots: [...CEP_SINGLETON_SLOTS, ...CEP_MULTI_SLOTS] })
  }

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-h-[85vh] overflow-y-auto sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>Documents — {assessment.title}</DialogTitle>
        </DialogHeader>

        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.doc,.docx,.png,.jpg,.jpeg"
          className="hidden"
          onChange={handleFileChosen}
        />

        <div className="flex flex-col gap-4">
          <DeadlineBanner
            assessment={assessment}
            termEndDate={termEndDate}
            canExtend={canReview}
            onExtended={refetch}
          />

          {isLoading ? (
            Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-16 w-full" />)
          ) : (
            <>
              {sections.map((section) => (
                <SlotSection
                  key={section.title}
                  title={section.title}
                  slots={section.slots}
                  byType={byType}
                  canManage={canManage}
                  canReview={canReview}
                  onUpload={triggerUpload}
                  onReview={review}
                  onDelete={remove}
                  uploadingType={uploadingType}
                />
              ))}
              {!assessmentType?.requires_documents && !assessmentType?.requires_cep_documents && (
                <p className="text-xs text-muted-foreground">
                  Scripts are optional for this assessment type — only Midterm/Final Exam require the
                  full document set.
                </p>
              )}
            </>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
