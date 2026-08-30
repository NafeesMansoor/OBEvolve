import * as React from 'react'
import { toast } from 'sonner'

import { useAuth } from '@/features/auth/useAuth'
import { useCourseVersionLookup } from '@/features/academic-ops/useLookups'
import type { Question } from '@/features/assessment/types'
import { ApiError } from '@/lib/api-client'
import { useEntityList, useEntityUpdate } from '@/lib/crud-hooks'
import { Badge } from '@/components/ui/badge'
import { DataTable, type DataTableColumn } from '@/components/data-table'
import { PageHeader } from '@/components/page-header'
import { RequirePermission } from '@/components/require-permission'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'

/** Faculty Module spec §16-17: search/filter the reusable Question Bank
 * (questions any faculty has explicitly shared globally) and toggle sharing
 * on your own questions. Reusing a question into a specific assessment
 * happens from that assessment's "Add task" form (Course Management ›
 * Assessments), which lists these same globally-shared questions inline —
 * this page is the browse/manage surface. */
export function QuestionBankPage() {
  const { user } = useAuth()
  const { options: courseVersionOptions, labelFor } = useCourseVersionLookup()
  const [courseVersionId, setCourseVersionId] = React.useState('')

  const { data: questions, isLoading, refetch } = useEntityList<Question>(
    ['assessment', 'questions', 'bank', courseVersionId],
    '/assessment/questions',
    { course_version_id: courseVersionId || undefined, is_globally_shared: 'true' },
  )
  const { data: myQuestions } = useEntityList<Question>(
    ['assessment', 'questions', 'mine', courseVersionId],
    '/assessment/questions',
    { course_version_id: courseVersionId || undefined },
  )
  const update = useEntityUpdate<Record<string, unknown>>((id) => `/assessment/questions/${id}`, [
    ['assessment', 'questions'],
  ])

  const combined = React.useMemo(() => {
    const map = new Map<string, Question>()
    for (const q of questions ?? []) map.set(q.id, q)
    for (const q of myQuestions ?? []) if (q.author_id === user?.id) map.set(q.id, q)
    return Array.from(map.values())
  }, [questions, myQuestions, user?.id])

  const columns: DataTableColumn<Question>[] = [
    { key: 'text', header: 'Question', render: (r) => r.text, searchValue: (r) => r.text },
    { key: 'course', header: 'Course', render: (r) => labelFor(r.course_version_id) },
    { key: 'marks', header: 'Marks', render: (r) => r.marks },
    { key: 'topic', header: 'Topic', render: (r) => r.topic ?? '—' },
    {
      key: 'shared',
      header: 'Shared globally',
      render: (r) =>
        r.author_id === user?.id ? (
          <Switch
            checked={r.is_globally_shared}
            onCheckedChange={async (checked) => {
              try {
                await update.mutateAsync({
                  id: r.id,
                  body: {
                    course_version_id: r.course_version_id,
                    text: r.text,
                    question_type: r.question_type,
                    difficulty: r.difficulty,
                    marks: r.marks,
                    topic: r.topic,
                    author_id: r.author_id,
                    kpa: r.kpa,
                    is_globally_shared: checked,
                  },
                })
                await refetch()
              } catch (err) {
                toast.error(err instanceof ApiError ? err.detail : 'Failed to update')
              }
            }}
          />
        ) : r.is_globally_shared ? (
          <Badge variant="secondary" className="font-normal">
            Shared
          </Badge>
        ) : (
          <span className="text-muted-foreground">—</span>
        ),
    },
  ]

  return (
    <RequirePermission anyOf={['assessment.view']}>
      <PageHeader
        title="Question Bank"
        description="Reuse questions shared by any faculty teaching the same course, this term or a future one."
      />
      <div className="mb-4 flex items-center gap-2">
        <Select value={courseVersionId} onValueChange={setCourseVersionId}>
          <SelectTrigger className="w-72">
            <SelectValue placeholder="Filter by course" />
          </SelectTrigger>
          <SelectContent>
            {courseVersionOptions.map((o) => (
              <SelectItem key={o.value} value={o.value}>
                {o.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <DataTable
        data={combined}
        columns={columns}
        rowKey={(r) => r.id}
        isLoading={isLoading}
        searchable
        searchPlaceholder="Search questions…"
        emptyMessage="No questions found. Share a question from an assessment's task list to see it here."
      />
    </RequirePermission>
  )
}
