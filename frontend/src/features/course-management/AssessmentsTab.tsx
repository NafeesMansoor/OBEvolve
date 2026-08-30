import * as React from 'react'
import { ListChecks, Plus } from 'lucide-react'
import { toast } from 'sonner'
import { z } from 'zod'

import { useAuth } from '@/features/auth/useAuth'
import type {
  Assessment,
  AssessmentQuestion,
  AssessmentQuestionProgramOutcomeMapping,
  AssessmentType,
  Question,
  QuestionCourseOutcomeMapping,
} from '@/features/assessment/types'
import type { MyCourseCard } from '@/features/course-management/types'
import type {
  AccreditationFramework,
  CourseOutcome,
  ProblemAttribute,
  ProgramOutcome,
} from '@/features/curriculum/types'
import { ApiError, apiClient } from '@/lib/api-client'
import {
  useEntityAction,
  useEntityCreate,
  useEntityList,
} from '@/lib/crud-hooks'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { DataTable, type DataTableColumn } from '@/components/data-table'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import { EntityFormDialog, type EntityField } from '@/components/entity-form-dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { StatusBadge, WORKFLOW_NEXT, type WorkflowStatus } from '@/components/status-badge'
import { Textarea } from '@/components/ui/textarea'

const createSchema = z.object({
  assessment_type_id: z.string().min(1, 'Type is required'),
  title: z.string().min(1, 'Title is required').max(255),
  max_marks: z.coerce.number(),
  weight: z.union([z.coerce.number(), z.literal('')]).optional(),
  date: z.string().optional(),
  duration_minutes: z.union([z.coerce.number().int(), z.literal('')]).optional(),
  purpose: z.string().optional(),
})

/** Faculty Module spec §11-19: create assessments for this section and
 * manage their questions/tasks, with CEP/OEP-aware fields (K/P/A, PO
 * mapping) surfaced only for assessment types that need them. */
export function AssessmentsTab({ course }: { course: MyCourseCard }) {
  const { hasPermission } = useAuth()
  const canManage = hasPermission('assessment.create') && course.is_current_term
  const canApprove = hasPermission('assessment.approve')

  const [createOpen, setCreateOpen] = React.useState(false)
  const [tasksFor, setTasksFor] = React.useState<Assessment | null>(null)

  const { data: types } = useEntityList<AssessmentType>(['assessment', 'types'], '/assessment/types')
  const typeById = React.useMemo(() => new Map((types ?? []).map((t) => [t.id, t])), [types])

  const { data: assessments, isLoading } = useEntityList<Assessment>(
    ['assessment', 'assessments', course.course_section_id],
    '/assessment/assessments',
    { course_section_id: course.course_section_id },
  )

  const create = useEntityCreate<Record<string, unknown>>('/assessment/assessments', [
    ['assessment', 'assessments', course.course_section_id],
  ])
  const advance = useEntityAction((id) => `/assessment/assessments/${id}/advance`, [
    ['assessment', 'assessments', course.course_section_id],
  ])

  const createFields: EntityField[] = [
    {
      name: 'assessment_type_id',
      label: 'Assessment type',
      type: 'select',
      options: (types ?? []).map((t) => ({ label: t.name, value: t.id })),
    },
    { name: 'title', label: 'Title', type: 'text' },
    { name: 'max_marks', label: 'Total marks', type: 'number' },
    { name: 'weight', label: 'Weight (%)', type: 'number' },
    { name: 'date', label: 'Date', type: 'date' },
    { name: 'duration_minutes', label: 'Duration (minutes)', type: 'number' },
    {
      name: 'purpose',
      label: 'Purpose (CEP/OEP problem statement)',
      type: 'textarea',
      description: 'Only needed for Complex Engineering Problem / Open-Ended Lab Problem assessments.',
    },
  ]

  const columns: DataTableColumn<Assessment>[] = [
    { key: 'title', header: 'Title', render: (r) => r.title, searchValue: (r) => r.title },
    { key: 'type', header: 'Type', render: (r) => typeById.get(r.assessment_type_id)?.name ?? '—' },
    { key: 'max_marks', header: 'Total marks', render: (r) => r.max_marks },
    { key: 'weight', header: 'Weight', render: (r) => (r.weight ? `${r.weight}%` : '—') },
    { key: 'status', header: 'Status', render: (r) => <StatusBadge status={r.status} /> },
  ]

  return (
    <div className="flex flex-col gap-4">
      <div className="flex justify-end">
        {canManage && (
          <Button size="sm" onClick={() => setCreateOpen(true)}>
            <Plus className="size-4" /> New assessment
          </Button>
        )}
      </div>

      <DataTable
        data={assessments}
        columns={columns}
        rowKey={(r) => r.id}
        isLoading={isLoading}
        emptyMessage="No assessments created for this section yet."
        actions={(r) => {
          const next = WORKFLOW_NEXT[r.status as WorkflowStatus]
          return (
            <div className="flex gap-2">
              <Button size="sm" variant="outline" onClick={() => setTasksFor(r)}>
                <ListChecks className="size-4" /> Questions
              </Button>
              {canApprove && next && (
                <Button
                  size="sm"
                  variant="outline"
                  onClick={async () => {
                    try {
                      await advance.mutateAsync(r.id)
                      toast.success(`Advanced to ${next}`)
                    } catch (err) {
                      toast.error(err instanceof ApiError ? err.detail : 'Could not advance')
                    }
                  }}
                >
                  Advance
                </Button>
              )}
            </div>
          )
        }}
      />

      <EntityFormDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        title="New assessment"
        fields={createFields}
        schema={createSchema}
        defaultValues={{
          assessment_type_id: '',
          title: '',
          max_marks: '',
          weight: '',
          date: '',
          duration_minutes: '',
          purpose: '',
        }}
        onSubmit={async (values) => {
          await create.mutateAsync({
            course_section_id: course.course_section_id,
            academic_term_id: course.academic_term_id,
            assessment_type_id: values.assessment_type_id,
            title: values.title,
            max_marks: values.max_marks,
            weight: values.weight === '' ? null : values.weight,
            date: values.date || null,
            duration_minutes: values.duration_minutes === '' ? null : values.duration_minutes,
            purpose: values.purpose || null,
          })
        }}
      />

      {tasksFor && (
        <TasksDialog
          assessment={tasksFor}
          assessmentType={typeById.get(tasksFor.assessment_type_id)}
          course={course}
          onOpenChange={(open) => !open && setTasksFor(null)}
        />
      )}
    </div>
  )
}

const questionSchema = z.object({
  text: z.string().min(1, 'Required'),
  marks: z.coerce.number(),
  course_outcome_id: z.string().min(1, 'Select a Course Outcome'),
  kpa: z.string().optional(),
  program_outcome_id: z.string().optional(),
})

function TasksDialog({
  assessment,
  assessmentType,
  course,
  onOpenChange,
}: {
  assessment: Assessment
  assessmentType: AssessmentType | undefined
  course: MyCourseCard
  onOpenChange: (open: boolean) => void
}) {
  const isCep = assessmentType?.requires_cep_documents ?? false
  const isOep = assessmentType?.requires_oep_validation ?? false
  const isExam = assessmentType?.requires_documents ?? false
  const label = isCep || isOep ? 'Task' : 'Question'

  const { data: aqs, refetch: refetchAqs } = useEntityList<AssessmentQuestion>(
    ['assessment', 'assessment-questions', assessment.id],
    '/assessment/assessment-questions',
    { assessment_id: assessment.id },
  )
  const { data: questions } = useEntityList<Question>(
    ['assessment', 'questions', course.course_version_id],
    '/assessment/questions',
    { course_version_id: course.course_version_id },
  )
  const { data: coMappings } = useEntityList<QuestionCourseOutcomeMapping>(
    ['assessment', 'question-co-mappings', assessment.id],
    '/assessment/question-co-mappings',
  )
  const { data: poMappings } = useEntityList<AssessmentQuestionProgramOutcomeMapping>(
    ['assessment', 'assessment-question-po-mappings', assessment.id],
    '/assessment/assessment-question-po-mappings',
  )
  const { data: courseOutcomes } = useEntityList<CourseOutcome>(
    ['curriculum', 'course-outcomes', course.course_version_id],
    '/curriculum/course-outcomes',
    { course_version_id: course.course_version_id },
  )
  const { data: programOutcomes } = useEntityList<ProgramOutcome>(
    ['curriculum', 'program-outcomes', course.program_version_id ?? ''],
    '/curriculum/program-outcomes',
    { program_version_id: course.program_version_id ?? undefined },
    { enabled: Boolean(course.program_version_id) && isCep },
  )

  const questionById = React.useMemo(() => new Map((questions ?? []).map((q) => [q.id, q])), [questions])
  const coByQuestion = React.useMemo(
    () => new Map((coMappings ?? []).map((m) => [m.question_id, m.course_outcome_id])),
    [coMappings],
  )
  const poByAq = React.useMemo(
    () => new Map((poMappings ?? []).map((m) => [m.assessment_question_id, m.program_outcome_id])),
    [poMappings],
  )
  const coOutcomeById = React.useMemo(
    () => new Map((courseOutcomes ?? []).map((c) => [c.id, c])),
    [courseOutcomes],
  )
  const poOutcomeById = React.useMemo(
    () => new Map((programOutcomes ?? []).map((p) => [p.id, p])),
    [programOutcomes],
  )

  const totalMarks = (aqs ?? []).reduce((sum, aq) => sum + Number(aq.marks_allocated), 0)

  async function handleAdd(values: z.infer<typeof questionSchema>) {
    const question = await apiClient.post<Question>('/assessment/questions', {
      course_version_id: course.course_version_id,
      text: values.text,
      question_type: isCep || isOep ? 'task' : 'exam',
      marks: values.marks,
      kpa: isCep && values.kpa ? values.kpa : null,
    })
    await apiClient.post('/assessment/question-co-mappings', {
      question_id: question.data.id,
      course_outcome_id: values.course_outcome_id,
    })
    const aq = await apiClient.post<AssessmentQuestion>('/assessment/assessment-questions', {
      assessment_id: assessment.id,
      question_id: question.data.id,
      marks_allocated: values.marks,
      sequence: (aqs?.length ?? 0) + 1,
    })
    if (isCep && values.program_outcome_id) {
      await apiClient.post('/assessment/assessment-question-po-mappings', {
        assessment_question_id: aq.data.id,
        program_outcome_id: values.program_outcome_id,
      })
    }
    await refetchAqs()
  }

  return (
    <Dialog open onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>
            {assessment.title} — {label}s
          </DialogTitle>
        </DialogHeader>

        {isExam && (
          <p className="text-sm text-muted-foreground">
            {label} marks total <strong>{totalMarks}</strong> of {assessment.max_marks} required.
            {totalMarks !== Number(assessment.max_marks) && (
              <span className="text-warning"> Must match before this assessment can be finalized.</span>
            )}
          </p>
        )}

        <div className="flex flex-col gap-2">
          {(aqs ?? []).map((aq) => {
            const q = questionById.get(aq.question_id)
            const coId = q ? coByQuestion.get(q.id) : undefined
            const poId = poByAq.get(aq.id)
            return (
              <div key={aq.id} className="rounded-md border p-3 text-sm">
                <div className="flex items-start justify-between gap-2">
                  <p className="font-medium">{q?.text ?? '—'}</p>
                  <Badge variant="outline" className="shrink-0 font-normal">
                    {aq.marks_allocated} marks
                  </Badge>
                </div>
                <div className="mt-1 flex flex-wrap gap-1.5 text-xs text-muted-foreground">
                  {coId && <span>CO: {coOutcomeById.get(coId)?.code ?? coId}</span>}
                  {q?.kpa && <span>· K/P/A: {q.kpa}</span>}
                  {poId && <span>· PO: {poOutcomeById.get(poId)?.code ?? poId}</span>}
                </div>
              </div>
            )
          })}
          {(!aqs || aqs.length === 0) && (
            <p className="text-sm text-muted-foreground">No {label.toLowerCase()}s added yet.</p>
          )}
        </div>

        {isCep && <CepGuidancePanel programVersionId={course.program_version_id} />}

        {course.is_current_term ? (
          <AddTaskForm
            isCep={isCep}
            courseOutcomes={courseOutcomes ?? []}
            programOutcomes={programOutcomes ?? []}
            label={label}
            onAdd={handleAdd}
          />
        ) : (
          <p className="text-sm text-muted-foreground">
            Read-only — this course is from a previous semester.
          </p>
        )}
      </DialogContent>
    </Dialog>
  )
}

/** Faculty Module — CEP guidance: which Complex Engineering Problem
 * "attributes" (WP1-WP7, BAETE v3.0 Table 6.2) a task should address, shown
 * as read-only reference alongside authoring, not a new per-task mapping
 * table (scope decision — the framework catalogue is guidance, the actual
 * mapping stays CO/PO via the fields already above). */
function CepGuidancePanel({ programVersionId }: { programVersionId: string | null }) {
  const { data: frameworks } = useEntityList<AccreditationFramework>(
    ['curriculum', 'frameworks'],
    '/curriculum/frameworks',
  )
  const framework = (frameworks ?? []).find((f) => f.is_active) ?? frameworks?.[0]
  const { data: attributes } = useEntityList<ProblemAttribute>(
    ['curriculum', 'problem-attributes', framework?.id ?? ''],
    `/curriculum/frameworks/${framework?.id}/problem-attributes`,
    undefined,
    { enabled: Boolean(framework?.id) },
  )

  if (!programVersionId || !attributes || attributes.length === 0) return null

  return (
    <div className="rounded-md border border-dashed bg-muted/30 p-3">
      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
        Complex Engineering Problem attributes — which should this task address?
      </p>
      <ul className="flex flex-col gap-1.5">
        {attributes.map((attr) => (
          <li key={attr.id} className="text-xs">
            <span className="font-medium text-foreground">
              {attr.code}
              {attr.title ? ` — ${attr.title}` : ''}:
            </span>{' '}
            <span className="text-muted-foreground">{attr.description}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}

function AddTaskForm({
  isCep,
  courseOutcomes,
  programOutcomes,
  label,
  onAdd,
}: {
  isCep: boolean
  courseOutcomes: CourseOutcome[]
  programOutcomes: ProgramOutcome[]
  label: string
  onAdd: (values: z.infer<typeof questionSchema>) => Promise<void>
}) {
  const [text, setText] = React.useState('')
  const [marks, setMarks] = React.useState('')
  const [courseOutcomeId, setCourseOutcomeId] = React.useState('')
  const [kpa, setKpa] = React.useState('')
  const [programOutcomeId, setProgramOutcomeId] = React.useState('')
  const [isSaving, setIsSaving] = React.useState(false)

  async function handleSubmit() {
    const parsed = questionSchema.safeParse({
      text,
      marks,
      course_outcome_id: courseOutcomeId,
      kpa,
      program_outcome_id: programOutcomeId,
    })
    if (!parsed.success) {
      toast.error(parsed.error.issues[0]?.message ?? 'Invalid input')
      return
    }
    setIsSaving(true)
    try {
      await onAdd(parsed.data)
      setText('')
      setMarks('')
      setCourseOutcomeId('')
      setKpa('')
      setProgramOutcomeId('')
      toast.success(`${label} added`)
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Failed to add')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="flex flex-col gap-2 rounded-md border border-dashed p-3">
      <Label>Add {label.toLowerCase()}</Label>
      <Textarea
        placeholder={`${label} text`}
        value={text}
        onChange={(e) => setText(e.target.value)}
      />
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
        <Input type="number" placeholder="Marks" value={marks} onChange={(e) => setMarks(e.target.value)} />
        <Select value={courseOutcomeId} onValueChange={setCourseOutcomeId}>
          <SelectTrigger>
            <SelectValue placeholder="Course Outcome" />
          </SelectTrigger>
          <SelectContent>
            {courseOutcomes.map((co) => (
              <SelectItem key={co.id} value={co.id}>
                {co.code}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        {isCep && (
          <Select value={kpa} onValueChange={setKpa}>
            <SelectTrigger>
              <SelectValue placeholder="K/P/A" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="K">Knowledge</SelectItem>
              <SelectItem value="P">Problem</SelectItem>
              <SelectItem value="A">Activity</SelectItem>
            </SelectContent>
          </Select>
        )}
        {isCep && (
          <Select value={programOutcomeId} onValueChange={setProgramOutcomeId}>
            <SelectTrigger>
              <SelectValue placeholder="Program Outcome" />
            </SelectTrigger>
            <SelectContent>
              {programOutcomes.map((po) => (
                <SelectItem key={po.id} value={po.id}>
                  {po.code}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </div>
      <Button size="sm" onClick={handleSubmit} disabled={isSaving} className="self-start">
        {isSaving ? 'Adding…' : `Add ${label.toLowerCase()}`}
      </Button>
    </div>
  )
}
