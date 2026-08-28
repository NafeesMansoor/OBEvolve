import * as React from 'react'
import { ArrowRight, Filter, Link2, Plus, Trash2, X } from 'lucide-react'
import { toast } from 'sonner'
import { z } from 'zod'

import { useAuth } from '@/features/auth/useAuth'
import { NewQuestionDialog } from '@/features/assessment/NewQuestionDialog'
import type {
  BloomLevel,
  Question,
  QuestionBloomMapping,
  QuestionCourseOutcomeMapping,
} from '@/features/assessment/types'
import type { Course, CourseOutcome, CourseVersion } from '@/features/curriculum/types'
import { ApiError, apiClient } from '@/lib/api-client'
import { useEntityAction, useEntityDelete, useEntityList, useEntityUpdate } from '@/lib/crud-hooks'
import { useResetOnChange } from '@/lib/use-reset-on-change'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ConfirmAction } from '@/components/confirm-action'
import { DataTable, type DataTableColumn } from '@/components/data-table'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { EntityFormDialog, type EntityField } from '@/components/entity-form-dialog'
import { RecordDetailSheet } from '@/components/record-detail-sheet'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { StatusBadge, WORKFLOW_NEXT, type WorkflowStatus } from '@/components/status-badge'

const schema = z.object({
  text: z.string().min(1, 'Question text is required'),
  question_type: z.string().min(1, 'Question type is required').max(50),
  marks: z.coerce.number(),
  topic: z.string().optional(),
  author_id: z.string().optional(),
})

interface FacultyDirectoryEntry {
  id: string
  full_name: string
}

export function QuestionsTab() {
  const { hasPermission } = useAuth()
  const canManage = hasPermission('assessment.create')
  const canApprove = hasPermission('assessment.approve')

  const [courseId, setCourseId] = React.useState('')
  const [createOpen, setCreateOpen] = React.useState(false)
  const [editQuestion, setEditQuestion] = React.useState<Question | null>(null)
  const [mappingsFor, setMappingsFor] = React.useState<Question | null>(null)
  const [viewQuestion, setViewQuestion] = React.useState<Question | null>(null)

  const { data: courses } = useEntityList<Course>(['curriculum', 'courses'], '/curriculum/courses')
  const { data: versions } = useEntityList<CourseVersion>(
    ['curriculum', 'course-versions', courseId],
    '/curriculum/course-versions',
    { course_id: courseId || undefined },
    { enabled: Boolean(courseId) },
  )
  const [courseVersionId, setCourseVersionId] = useResetOnChange(courseId, '')
  const { data: users } = useEntityList<FacultyDirectoryEntry>(
    ['users', 'faculty-directory'],
    '/users/faculty-directory',
  )
  const userById = React.useMemo(() => new Map((users ?? []).map((u) => [u.id, u])), [users])

  const {
    data: questions,
    isLoading,
    error,
  } = useEntityList<Question>(
    ['assessment', 'questions', courseVersionId],
    '/assessment/questions',
    { course_version_id: courseVersionId || undefined },
    { enabled: Boolean(courseVersionId) },
  )
  const update = useEntityUpdate<Record<string, unknown>, Question>(
    (id) => `/assessment/questions/${id}`,
    [['assessment', 'questions', courseVersionId]],
  )
  const remove = useEntityDelete((id) => `/assessment/questions/${id}`, [
    ['assessment', 'questions', courseVersionId],
  ])
  const advance = useEntityAction<Question>((id) => `/assessment/questions/${id}/advance`, [
    ['assessment', 'questions', courseVersionId],
  ])

  const fields: EntityField[] = [
    { name: 'text', label: 'Question text', type: 'textarea' },
    { name: 'question_type', label: 'Question type', type: 'text', placeholder: 'e.g. mcq, short_answer' },
    { name: 'marks', label: 'Marks', type: 'number', step: '0.5' },
    { name: 'topic', label: 'Topic', type: 'text' },
    {
      name: 'author_id',
      label: 'Author',
      type: 'select',
      options: (users ?? []).map((u) => ({ label: u.full_name, value: u.id })),
    },
  ]

  const columns: DataTableColumn<Question>[] = [
    { key: 'text', header: 'Question', render: (r) => r.text, className: 'max-w-md' },
    { key: 'question_type', header: 'Type', render: (r) => r.question_type },
    { key: 'marks', header: 'Marks', render: (r) => r.marks },
    { key: 'status', header: 'Status', render: (r) => <StatusBadge status={r.status} /> },
  ]

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex flex-wrap gap-2">
          <div className="w-64">
            <Select value={courseId} onValueChange={setCourseId}>
              <SelectTrigger>
                <SelectValue placeholder="Select a course" />
              </SelectTrigger>
              <SelectContent>
                {(courses ?? []).map((c) => (
                  <SelectItem key={c.id} value={c.id}>
                    {c.code} — {c.title}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="w-48">
            <Select value={courseVersionId} onValueChange={setCourseVersionId} disabled={!courseId}>
              <SelectTrigger>
                <SelectValue placeholder="Version" />
              </SelectTrigger>
              <SelectContent>
                {(versions ?? []).map((v) => (
                  <SelectItem key={v.id} value={v.id}>
                    {v.version_label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
        {canManage && courseVersionId && (
          <Button size="sm" onClick={() => setCreateOpen(true)}>
            <Plus className="size-4" /> New question
          </Button>
        )}
      </div>

      {!courseVersionId ? (
        <div className="flex flex-col items-center gap-2 rounded-md border border-dashed py-10 text-center text-muted-foreground">
          <Filter className="size-6 opacity-50" />
          <p className="text-sm">Select a course and version to see its questions.</p>
        </div>
      ) : (
        <DataTable
          data={questions}
          columns={columns}
          rowKey={(r) => r.id}
          isLoading={isLoading}
          error={error}
          emptyMessage="No questions yet for this version."
          onRowClick={(r) => setViewQuestion(r)}
          actions={(r) => (
            <>
              <Button size="sm" variant="outline" onClick={() => setMappingsFor(r)}>
                <Link2 className="size-3.5" /> Mappings
              </Button>
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
                    <Button size="sm" variant="ghost" aria-label="Delete this question">
                      <Trash2 className="size-4 text-destructive" />
                    </Button>
                  }
                  title="Delete this question?"
                  onConfirm={async () => {
                    try {
                      await remove.mutateAsync(r.id)
                      toast.success('Question deleted')
                    } catch (err) {
                      toast.error(err instanceof ApiError ? err.detail : 'Unable to delete question.')
                    }
                  }}
                />
              )}
            </>
          )}
        />
      )}

      <NewQuestionDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        courseVersionId={courseVersionId}
        users={users}
      />

      {viewQuestion && (
        <RecordDetailSheet
          open={Boolean(viewQuestion)}
          onOpenChange={(open) => !open && setViewQuestion(null)}
          title={viewQuestion.text}
          badge={<StatusBadge status={viewQuestion.status} />}
          fields={[
            { label: 'Type', value: viewQuestion.question_type },
            { label: 'Marks', value: viewQuestion.marks },
            { label: 'Topic', value: viewQuestion.topic ?? '—' },
            {
              label: 'Author',
              value: viewQuestion.author_id ? (userById.get(viewQuestion.author_id)?.full_name ?? '—') : '—',
            },
            { label: 'Status', value: viewQuestion.status },
          ]}
          onEdit={
            canManage
              ? () => {
                  setEditQuestion(viewQuestion)
                  setViewQuestion(null)
                }
              : undefined
          }
        />
      )}

      {editQuestion && (
        <EntityFormDialog
          open={Boolean(editQuestion)}
          onOpenChange={(open) => !open && setEditQuestion(null)}
          title="Edit question"
          fields={fields}
          schema={schema}
          defaultValues={{
            text: editQuestion.text,
            question_type: editQuestion.question_type,
            marks: editQuestion.marks,
            topic: editQuestion.topic ?? '',
            author_id: editQuestion.author_id ?? '',
          }}
          onSubmit={async (values) => {
            try {
              await update.mutateAsync({
                id: editQuestion.id,
                body: {
                  text: values.text,
                  question_type: values.question_type,
                  marks: values.marks,
                  topic: values.topic || null,
                  author_id: values.author_id || null,
                },
              })
              toast.success('Question updated')
            } catch (err) {
              throw err instanceof ApiError ? err : new ApiError('Unable to update question.')
            }
          }}
        />
      )}

      {mappingsFor && (
        <QuestionMappingsDialog
          question={mappingsFor}
          courseVersionId={courseVersionId}
          canManage={canManage}
          onClose={() => setMappingsFor(null)}
        />
      )}
    </div>
  )
}

function QuestionMappingsDialog({
  question,
  courseVersionId,
  canManage,
  onClose,
}: {
  question: Question
  courseVersionId: string
  canManage: boolean
  onClose: () => void
}) {
  const [coId, setCoId] = React.useState('')
  const [bloomId, setBloomId] = React.useState('')
  const { data: outcomes } = useEntityList<CourseOutcome>(
    ['curriculum', 'course-outcomes', courseVersionId],
    '/curriculum/course-outcomes',
    { course_version_id: courseVersionId },
  )
  const coById = React.useMemo(() => new Map((outcomes ?? []).map((o) => [o.id, o])), [outcomes])

  const { data: coMappings, refetch: refetchCO } = useEntityList<QuestionCourseOutcomeMapping>(
    ['assessment', 'question-co-mappings', question.id],
    '/assessment/question-co-mappings',
    { question_id: question.id },
  )

  const { data: bloomLevels } = useEntityList<BloomLevel>(
    ['curriculum', 'bloom-levels'],
    '/curriculum/bloom-levels',
  )
  const bloomById = React.useMemo(() => new Map((bloomLevels ?? []).map((b) => [b.id, b])), [bloomLevels])
  const { data: bloomMappings, refetch: refetchBloom } = useEntityList<QuestionBloomMapping>(
    ['assessment', 'question-bloom-mappings', question.id],
    '/assessment/question-bloom-mappings',
    { question_id: question.id },
  )

  async function addMapping() {
    if (!coId) return
    try {
      await apiClient.post('/assessment/question-co-mappings', {
        question_id: question.id,
        course_outcome_id: coId,
      })
      setCoId('')
      await refetchCO()
      toast.success('Mapped to course outcome')
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Unable to add mapping.')
    }
  }

  async function removeMapping(id: string) {
    try {
      await apiClient.delete(`/assessment/question-co-mappings/${id}`)
      await refetchCO()
      toast.success('Mapping removed')
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Unable to remove mapping.')
    }
  }

  async function addBloomMapping() {
    if (!bloomId) return
    try {
      await apiClient.post('/assessment/question-bloom-mappings', {
        question_id: question.id,
        bloom_level_id: bloomId,
      })
      setBloomId('')
      await refetchBloom()
      toast.success('Mapped to Bloom level')
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Unable to add Bloom mapping.')
    }
  }

  async function removeBloomMapping(id: string) {
    try {
      await apiClient.delete(`/assessment/question-bloom-mappings/${id}`)
      await refetchBloom()
      toast.success('Bloom mapping removed')
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Unable to remove Bloom mapping.')
    }
  }

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Outcome mappings</DialogTitle>
        </DialogHeader>

        <div className="flex flex-col gap-4">
          <div>
            <p className="mb-2 text-sm font-medium">Course outcomes</p>
            <div className="flex flex-wrap gap-1.5">
              {(coMappings ?? []).length === 0 ? (
                <span className="text-xs text-muted-foreground">No course outcomes linked yet.</span>
              ) : (
                coMappings?.map((m) => (
                  <Badge key={m.id} variant="secondary" className="gap-1 pr-1 font-normal">
                    {coById.get(m.course_outcome_id)?.code ?? m.course_outcome_id}
                    {canManage && (
                      <button
                        type="button"
                        onClick={() => removeMapping(m.id)}
                        className="rounded-full p-0.5 hover:bg-muted-foreground/20"
                        aria-label="Remove mapping"
                      >
                        <X className="size-3" />
                      </button>
                    )}
                  </Badge>
                ))
              )}
            </div>
            {canManage && (
              <div className="mt-2 flex items-end gap-2">
                <div className="flex-1">
                  <Select value={coId} onValueChange={setCoId}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select a course outcome" />
                    </SelectTrigger>
                    <SelectContent>
                      {(outcomes ?? []).map((o) => (
                        <SelectItem key={o.id} value={o.id}>
                          {o.code} — {o.statement}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <Button size="sm" onClick={addMapping} disabled={!coId}>
                  Link
                </Button>
              </div>
            )}
          </div>

          <div className="border-t pt-3">
            <p className="mb-2 text-sm font-medium">Bloom&apos;s cognitive levels</p>
            <div className="flex flex-wrap gap-1.5">
              {(bloomMappings ?? []).length === 0 ? (
                <span className="text-xs text-muted-foreground">No Bloom level linked yet.</span>
              ) : (
                bloomMappings?.map((m) => (
                  <Badge key={m.id} variant="secondary" className="gap-1 pr-1 font-normal">
                    {bloomById.get(m.bloom_level_id)?.name ?? m.bloom_level_id}
                    {canManage && (
                      <button
                        type="button"
                        onClick={() => removeBloomMapping(m.id)}
                        className="rounded-full p-0.5 hover:bg-muted-foreground/20"
                        aria-label="Remove Bloom mapping"
                      >
                        <X className="size-3" />
                      </button>
                    )}
                  </Badge>
                ))
              )}
            </div>
            {canManage && (
              <div className="mt-2 flex items-end gap-2">
                <div className="flex-1">
                  <Select value={bloomId} onValueChange={setBloomId}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select a Bloom level" />
                    </SelectTrigger>
                    <SelectContent>
                      {(bloomLevels ?? []).length === 0 ? (
                        <div className="px-2 py-1.5 text-sm text-muted-foreground">None available yet</div>
                      ) : (
                        bloomLevels?.map((level) => (
                          <SelectItem key={level.id} value={level.id}>
                            {level.name}
                          </SelectItem>
                        ))
                      )}
                    </SelectContent>
                  </Select>
                </div>
                <Button size="sm" onClick={addBloomMapping} disabled={!bloomId}>
                  Link
                </Button>
              </div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
