import * as React from 'react'
import { useQueries } from '@tanstack/react-query'
import { AlertTriangle, ArrowRight, FileText, Filter, ListChecks, Plus, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { z } from 'zod'

import { useAuth } from '@/features/auth/useAuth'
import { useAcademicTermLookup, useCourseVersionLookup } from '@/features/academic-ops/useLookups'
import type { CourseOffering, CourseSection } from '@/features/academic-ops/types'
import { AssessmentDocumentsDialog } from '@/features/assessment/AssessmentDocumentsDialog'
import type {
  Assessment,
  AssessmentDocument,
  AssessmentQuestion,
  AssessmentType,
  AssessmentWeightSummary,
  Question,
  Rubric,
} from '@/features/assessment/types'
import { ApiError, apiClient } from '@/lib/api-client'
import {
  useEntityAction,
  useEntityCreate,
  useEntityDelete,
  useEntityGet,
  useEntityList,
  useEntityUpdate,
} from '@/lib/crud-hooks'
import { useResetOnChange } from '@/lib/use-reset-on-change'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ConfirmAction } from '@/components/confirm-action'
import { DataTable, type DataTableColumn } from '@/components/data-table'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { EntityFormDialog, type EntityField } from '@/components/entity-form-dialog'
import { RecordDetailSheet } from '@/components/record-detail-sheet'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { StatusBadge, WORKFLOW_NEXT, type WorkflowStatus } from '@/components/status-badge'

const schema = z.object({
  academic_term_id: z.string().min(1, 'Academic term is required'),
  assessment_type_id: z.string().min(1, 'Assessment type is required'),
  title: z.string().min(1, 'Title is required').max(255),
  max_marks: z.coerce.number(),
  weight: z.union([z.coerce.number(), z.literal('')]).optional(),
  date: z.string().optional(),
  duration_minutes: z.union([z.coerce.number().int(), z.literal('')]).optional(),
  rubric_id: z.string().optional(),
})

export function AssessmentsTab() {
  const { hasPermission } = useAuth()
  const canManage = hasPermission('assessment.create')
  const canApprove = hasPermission('assessment.approve')

  const { labelFor } = useCourseVersionLookup()
  const { options: termOptions, termById } = useAcademicTermLookup()
  const { data: offerings } = useEntityList<CourseOffering>(
    ['academic', 'course-offerings'],
    '/academic/course-offerings',
  )
  const [offeringId, setOfferingId] = React.useState('')
  const { data: sections } = useEntityList<CourseSection>(
    ['academic', 'sections', offeringId],
    '/academic/sections',
    { course_offering_id: offeringId || undefined },
    { enabled: Boolean(offeringId) },
  )
  const [sectionId, setSectionId] = useResetOnChange(offeringId, '')

  const { data: types } = useEntityList<AssessmentType>(['assessment', 'types'], '/assessment/types')
  const { data: rubrics } = useEntityList<Rubric>(['assessment', 'rubrics'], '/assessment/rubrics')
  const typeById = React.useMemo(() => new Map((types ?? []).map((t) => [t.id, t])), [types])
  const rubricById = React.useMemo(() => new Map((rubrics ?? []).map((r) => [r.id, r])), [rubrics])

  const [createOpen, setCreateOpen] = React.useState(false)
  const [editAssessment, setEditAssessment] = React.useState<Assessment | null>(null)
  const [attachFor, setAttachFor] = React.useState<Assessment | null>(null)
  const [viewAssessment, setViewAssessment] = React.useState<Assessment | null>(null)
  const [documentsFor, setDocumentsFor] = React.useState<Assessment | null>(null)

  const {
    data: assessments,
    isLoading,
    error,
  } = useEntityList<Assessment>(
    ['assessment', 'assessments', sectionId],
    '/assessment/assessments',
    { course_section_id: sectionId || undefined },
    { enabled: Boolean(sectionId) },
  )
  const create = useEntityCreate<Record<string, unknown>, Assessment>('/assessment/assessments', [
    ['assessment', 'assessments', sectionId],
    ['assessment', 'weight-summary', sectionId],
  ])
  const update = useEntityUpdate<Record<string, unknown>, Assessment>(
    (id) => `/assessment/assessments/${id}`,
    [
      ['assessment', 'assessments', sectionId],
      ['assessment', 'weight-summary', sectionId],
    ],
  )
  const remove = useEntityDelete((id) => `/assessment/assessments/${id}`, [
    ['assessment', 'assessments', sectionId],
    ['assessment', 'weight-summary', sectionId],
  ])
  const advance = useEntityAction<Assessment>((id) => `/assessment/assessments/${id}/advance`, [
    ['assessment', 'assessments', sectionId],
  ])

  const { data: weightSummary } = useEntityGet<AssessmentWeightSummary>(
    ['assessment', 'weight-summary', sectionId],
    `/assessment/assessments/weight-summary?course_section_id=${sectionId}`,
    { enabled: Boolean(sectionId) },
  )

  const offeringOptions = React.useMemo(
    () =>
      (offerings ?? []).map((o) => ({
        label: `${labelFor(o.course_version_id)} · ${termById.get(o.academic_term_id)?.name ?? ''}`,
        value: o.id,
      })),
    [offerings, labelFor, termById],
  )

  const fields: EntityField[] = [
    { name: 'title', label: 'Title', type: 'text' },
    { name: 'academic_term_id', label: 'Academic term', type: 'select', options: termOptions },
    {
      name: 'assessment_type_id',
      label: 'Assessment type',
      type: 'select',
      options: (types ?? []).map((t) => ({ label: t.name, value: t.id })),
    },
    { name: 'max_marks', label: 'Max marks', type: 'number', step: '0.5' },
    { name: 'weight', label: 'Weight (%)', type: 'number', step: '0.5' },
    { name: 'date', label: 'Date', type: 'date' },
    { name: 'duration_minutes', label: 'Duration (minutes)', type: 'number' },
    {
      name: 'rubric_id',
      label: 'Rubric (optional)',
      type: 'select',
      options: (rubrics ?? []).map((r) => ({ label: r.name, value: r.id })),
    },
  ]

  const columns: DataTableColumn<Assessment>[] = [
    { key: 'title', header: 'Title', render: (r) => r.title },
    { key: 'type', header: 'Type', render: (r) => typeById.get(r.assessment_type_id)?.name ?? '—' },
    { key: 'max_marks', header: 'Max marks', render: (r) => r.max_marks },
    { key: 'status', header: 'Status', render: (r) => <StatusBadge status={r.status} /> },
  ]

  const documentRequiredAssessments = React.useMemo(
    () =>
      (assessments ?? []).filter((a) => {
        const t = typeById.get(a.assessment_type_id)
        return t?.requires_documents || t?.requires_cep_documents
      }),
    [assessments, typeById],
  )
  const completeness = useDocumentCompleteness(documentRequiredAssessments, typeById)

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap gap-2">
          <div className="w-full max-w-md">
            <Select value={offeringId} onValueChange={setOfferingId}>
              <SelectTrigger>
                <SelectValue placeholder="Select a course offering" />
              </SelectTrigger>
              <SelectContent>
                {offeringOptions.map((o) => (
                  <SelectItem key={o.value} value={o.value}>
                    {o.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="w-40">
            <Select value={sectionId} onValueChange={setSectionId} disabled={!offeringId}>
              <SelectTrigger>
                <SelectValue placeholder="Section" />
              </SelectTrigger>
              <SelectContent>
                {(sections ?? []).map((s) => (
                  <SelectItem key={s.id} value={s.id}>
                    {s.section_code}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
        {canManage && sectionId && (
          <Button size="sm" onClick={() => setCreateOpen(true)}>
            <Plus className="size-4" /> New assessment
          </Button>
        )}
      </div>

      {sectionId && weightSummary && weightSummary.assessment_count > 0 && (
        <Badge
          variant={weightSummary.is_complete ? 'secondary' : 'outline'}
          className="w-fit font-normal tabular-nums"
        >
          Weight total: {weightSummary.total_weight}%
          {weightSummary.weighted_count < weightSummary.assessment_count &&
            ` (${weightSummary.assessment_count - weightSummary.weighted_count} unweighted)`}
          {!weightSummary.is_complete && ' — doesn’t sum to 100%'}
        </Badge>
      )}

      {completeness.incompleteCount > 0 && (
        <div className="flex items-center gap-2 rounded-md border border-warning/30 bg-warning/10 px-3 py-2 text-sm text-warning">
          <AlertTriangle className="size-4 shrink-0" />
          <span>
            {completeness.incompleteCount} assessment{completeness.incompleteCount === 1 ? '' : 's'} in this
            section {completeness.incompleteCount === 1 ? 'has' : 'have'} pending or missing required
            documents.
          </span>
        </div>
      )}

      {!sectionId ? (
        <div className="flex flex-col items-center gap-2 rounded-md border border-dashed py-10 text-center text-muted-foreground">
          <Filter className="size-6 opacity-50" />
          <p className="text-sm">Select an offering and section to see assessments.</p>
        </div>
      ) : (
        <DataTable
          data={assessments}
          columns={columns}
          rowKey={(r) => r.id}
          isLoading={isLoading}
          error={error}
          emptyMessage="No assessments yet for this section."
          onRowClick={(r) => setViewAssessment(r)}
          actions={(r) => (
            <>
              <Button size="sm" variant="outline" onClick={() => setAttachFor(r)}>
                <ListChecks className="size-3.5" /> Questions
              </Button>
              {(typeById.get(r.assessment_type_id)?.requires_documents ||
                typeById.get(r.assessment_type_id)?.requires_cep_documents) && (
                <Button
                  size="sm"
                  variant={completeness.incompleteIds.has(r.id) ? 'outline' : 'ghost'}
                  className={
                    completeness.incompleteIds.has(r.id)
                      ? 'border-warning/40 text-warning hover:text-warning'
                      : undefined
                  }
                  onClick={() => setDocumentsFor(r)}
                >
                  <FileText className="size-3.5" /> Documents
                </Button>
              )}
              {canApprove && WORKFLOW_NEXT[r.status as WorkflowStatus] && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={async () => {
                    try {
                      await advance.mutateAsync(r.id)
                      toast.success('Advanced')
                    } catch (err) {
                      toast.error(err instanceof ApiError ? err.detail : 'Unable to advance.')
                    }
                  }}
                >
                  Advance <ArrowRight className="size-3.5" />
                </Button>
              )}
              {canManage && (
                <ConfirmAction
                  trigger={
                    <Button size="sm" variant="ghost" aria-label={`Delete assessment "${r.title}"`}>
                      <Trash2 className="size-4 text-destructive" />
                    </Button>
                  }
                  title={`Delete assessment "${r.title}"?`}
                  onConfirm={async () => {
                    try {
                      await remove.mutateAsync(r.id)
                      toast.success('Assessment deleted')
                    } catch (err) {
                      toast.error(err instanceof ApiError ? err.detail : 'Unable to delete assessment.')
                    }
                  }}
                />
              )}
            </>
          )}
        />
      )}

      <EntityFormDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        title="New assessment"
        fields={fields}
        schema={schema}
        defaultValues={{
          title: '',
          academic_term_id: '',
          assessment_type_id: '',
          max_marks: '',
          weight: '',
          date: '',
          duration_minutes: '',
          rubric_id: '',
        }}
        onSubmit={async (values) => {
          try {
            await create.mutateAsync({
              course_section_id: sectionId,
              academic_term_id: values.academic_term_id,
              assessment_type_id: values.assessment_type_id,
              title: values.title,
              max_marks: values.max_marks,
              weight: values.weight === '' ? null : values.weight,
              date: values.date || null,
              duration_minutes: values.duration_minutes === '' ? null : values.duration_minutes,
              rubric_id: values.rubric_id || null,
            })
            toast.success('Assessment created')
          } catch (err) {
            throw err instanceof ApiError ? err : new ApiError('Unable to create assessment.')
          }
        }}
      />

      {viewAssessment && (
        <RecordDetailSheet
          open={Boolean(viewAssessment)}
          onOpenChange={(open) => !open && setViewAssessment(null)}
          title={viewAssessment.title}
          subtitle={typeById.get(viewAssessment.assessment_type_id)?.name}
          badge={<StatusBadge status={viewAssessment.status} />}
          fields={[
            { label: 'Term', value: termById.get(viewAssessment.academic_term_id)?.name ?? '—' },
            { label: 'Type', value: typeById.get(viewAssessment.assessment_type_id)?.name ?? '—' },
            { label: 'Max marks', value: viewAssessment.max_marks },
            { label: 'Weight', value: viewAssessment.weight ? `${viewAssessment.weight}%` : '—' },
            { label: 'Date', value: viewAssessment.date ?? '—' },
            { label: 'Duration', value: viewAssessment.duration_minutes ? `${viewAssessment.duration_minutes} min` : '—' },
            { label: 'Rubric', value: viewAssessment.rubric_id ? (rubricById.get(viewAssessment.rubric_id)?.name ?? '—') : '—' },
            { label: 'Status', value: viewAssessment.status },
          ]}
          onEdit={
            canManage
              ? () => {
                  setEditAssessment(viewAssessment)
                  setViewAssessment(null)
                }
              : undefined
          }
        />
      )}

      {editAssessment && (
        <EntityFormDialog
          open={Boolean(editAssessment)}
          onOpenChange={(open) => !open && setEditAssessment(null)}
          title="Edit assessment"
          fields={fields}
          schema={schema}
          defaultValues={{
            title: editAssessment.title,
            academic_term_id: editAssessment.academic_term_id,
            assessment_type_id: editAssessment.assessment_type_id,
            max_marks: editAssessment.max_marks,
            weight: editAssessment.weight ?? '',
            date: editAssessment.date ?? '',
            duration_minutes: editAssessment.duration_minutes ?? '',
            rubric_id: editAssessment.rubric_id ?? '',
          }}
          onSubmit={async (values) => {
            try {
              await update.mutateAsync({
                id: editAssessment.id,
                body: {
                  academic_term_id: values.academic_term_id,
                  assessment_type_id: values.assessment_type_id,
                  title: values.title,
                  max_marks: values.max_marks,
                  weight: values.weight === '' ? null : values.weight,
                  date: values.date || null,
                  duration_minutes: values.duration_minutes === '' ? null : values.duration_minutes,
                  rubric_id: values.rubric_id || null,
                },
              })
              toast.success('Assessment updated')
            } catch (err) {
              throw err instanceof ApiError ? err : new ApiError('Unable to update assessment.')
            }
          }}
        />
      )}

      {attachFor && (
        <AttachQuestionsDialog
          assessment={attachFor}
          canManage={canManage}
          onClose={() => setAttachFor(null)}
        />
      )}

      {documentsFor && (
        <AssessmentDocumentsDialog
          assessment={documentsFor}
          assessmentType={typeById.get(documentsFor.assessment_type_id)}
          termEndDate={termById.get(documentsFor.academic_term_id)?.end_date ?? null}
          canManage={canManage}
          canReview={canApprove}
          onClose={() => setDocumentsFor(null)}
        />
      )}
    </div>
  )
}

/**
 * Fans out one documents-list fetch per assessment that requires documents
 * (bounded — a section has at most a handful of Midterm/Final/CEP
 * assessments), so the section-level "N assessments have pending/missing
 * documents" banner and each row's Documents-button warning styling can be
 * computed from data every `assessment.view` holder can already see —
 * no separate permission-gated summary endpoint needed for this.
 */
function useDocumentCompleteness(
  assessments: Assessment[],
  typeById: Map<string, AssessmentType>,
) {
  const results = useQueries({
    queries: assessments.map((a) => ({
      queryKey: ['assessment', 'assessment-documents', a.id],
      queryFn: async () =>
        (await apiClient.get<AssessmentDocument[]>(`/assessment/assessments/${a.id}/documents`)).data,
    })),
  })

  const incompleteIds = new Set<string>()
  results.forEach((result, i) => {
    const assessment = assessments[i]
    const type = typeById.get(assessment.assessment_type_id)
    if (!result.data || !type) return

    const byType = new Map<string, AssessmentDocument[]>()
    for (const doc of result.data) {
      const list = byType.get(doc.document_type) ?? []
      list.push(doc)
      byType.set(doc.document_type, list)
    }
    const required: { type: string; min: number }[] = []
    if (type.requires_documents) {
      required.push(
        { type: 'question_paper', min: 1 },
        { type: 'moderation_form', min: 1 },
        { type: 'compliance_form', min: 1 },
        { type: 'script_highest', min: 1 },
        { type: 'script_lowest', min: 1 },
        { type: 'script_median', min: 1 },
      )
    }
    if (type.requires_cep_documents) {
      required.push(
        { type: 'problem_definition', min: 1 },
        { type: 'marked_rubric_sample', min: 1 },
        { type: 'project_report', min: 3 },
      )
    }
    const isComplete = required.every((r) => {
      const docs = byType.get(r.type) ?? []
      return docs.filter((d) => d.status !== 'rejected').length >= r.min
    })
    if (!isComplete) incompleteIds.add(assessment.id)
  })

  return { incompleteIds, incompleteCount: incompleteIds.size }
}

function AttachQuestionsDialog({
  assessment,
  canManage,
  onClose,
}: {
  assessment: Assessment
  canManage: boolean
  onClose: () => void
}) {
  const [questionId, setQuestionId] = React.useState('')
  const [marks, setMarks] = React.useState('')

  // Questions attached to assessments come from the same course's question
  // bank, but assessments aren't scoped to a course_version_id directly —
  // so all questions are offered here rather than trying to infer the
  // course from the section (out of scope for this pass).
  const { data: allQuestions } = useEntityList<Question>(['assessment', 'questions', 'all'], '/assessment/questions')
  const questionById = React.useMemo(
    () => new Map((allQuestions ?? []).map((q) => [q.id, q])),
    [allQuestions],
  )

  const { data: attached, refetch } = useEntityList<AssessmentQuestion>(
    ['assessment', 'assessment-questions', assessment.id],
    '/assessment/assessment-questions',
    { assessment_id: assessment.id },
  )

  async function attach() {
    if (!questionId || !marks) return
    try {
      await apiClient.post('/assessment/assessment-questions', {
        assessment_id: assessment.id,
        question_id: questionId,
        marks_allocated: marks,
        sequence: (attached?.length ?? 0) + 1,
      })
      setQuestionId('')
      setMarks('')
      await refetch()
      toast.success('Question attached')
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Unable to attach question.')
    }
  }

  async function detach(id: string) {
    try {
      await apiClient.delete(`/assessment/assessment-questions/${id}`)
      await refetch()
      toast.success('Question detached')
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Unable to detach question.')
    }
  }

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Questions for &quot;{assessment.title}&quot;</DialogTitle>
        </DialogHeader>

        <div className="flex flex-col gap-3">
          {(attached ?? []).length === 0 ? (
            <p className="text-sm text-muted-foreground">No questions attached yet.</p>
          ) : (
            <div className="flex flex-col gap-2">
              {attached
                ?.slice()
                .sort((a, b) => a.sequence - b.sequence)
                .map((aq) => (
                  <div key={aq.id} className="flex items-center justify-between gap-2 rounded-md border px-3 py-2 text-sm">
                    <span className="line-clamp-1">
                      <span className="font-medium tabular-nums">#{aq.sequence}</span> —{' '}
                      {questionById.get(aq.question_id)?.text ?? aq.question_id}{' '}
                      <span className="text-muted-foreground tabular-nums">({aq.marks_allocated} marks)</span>
                    </span>
                    {canManage && (
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => detach(aq.id)}
                        aria-label="Detach question"
                        className="shrink-0"
                      >
                        <Trash2 className="size-4 text-destructive" />
                      </Button>
                    )}
                  </div>
                ))}
            </div>
          )}

          {canManage && (
            <div className="flex items-end gap-2 border-t pt-3">
              <div className="flex-1">
                <Select value={questionId} onValueChange={setQuestionId}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a question" />
                  </SelectTrigger>
                  <SelectContent>
                    {(allQuestions ?? []).map((q) => (
                      <SelectItem key={q.id} value={q.id}>
                        {q.text.slice(0, 60)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <Input
                type="number"
                placeholder="Marks"
                value={marks}
                onChange={(e) => setMarks(e.target.value)}
                className="w-24 tabular-nums"
                aria-label="Marks for this question"
              />
              <Button size="sm" onClick={attach} disabled={!questionId || !marks}>
                Attach
              </Button>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}
