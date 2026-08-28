import * as React from 'react'
import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import { toast } from 'sonner'
import { z } from 'zod'

import type { BloomLevel } from '@/features/assessment/types'
import type { CourseOutcome } from '@/features/curriculum/types'
import { ApiError, apiClient } from '@/lib/api-client'
import { useEntityCreate, useEntityList } from '@/lib/crud-hooks'
import { useResetOnChange } from '@/lib/use-reset-on-change'
import { Button } from '@/components/ui/button'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'

const schema = z.object({
  text: z.string().min(1, 'Question text is required'),
  question_type: z.string().min(1, 'Question type is required').max(50),
  marks: z.coerce.number(),
  topic: z.string().optional(),
  author_id: z.string().optional(),
  bloom_level_id: z.string().optional(),
})

type FormInput = z.input<typeof schema>
type FormValues = z.output<typeof schema>

interface FacultyDirectoryEntry {
  id: string
  full_name: string
}

/**
 * Question authoring surface, purpose-built rather than the generic
 * EntityFormDialog because Bloom level and CO mapping are relations (junction
 * tables), not columns on Question — `difficulty` (a free-text column) is
 * deliberately not shown here; a question is classified by Bloom's cognitive
 * level and which course outcome(s) it targets instead.
 */
export function NewQuestionDialog({
  open,
  onOpenChange,
  courseVersionId,
  users,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  courseVersionId: string
  users: FacultyDirectoryEntry[] | undefined
}) {
  const [selectedCOs, setSelectedCOs] = useResetOnChange(open, new Set<string>())

  const { data: outcomes } = useEntityList<CourseOutcome>(
    ['curriculum', 'course-outcomes', courseVersionId],
    '/curriculum/course-outcomes',
    { course_version_id: courseVersionId },
    { enabled: open && Boolean(courseVersionId) },
  )
  const { data: bloomLevels } = useEntityList<BloomLevel>(
    ['curriculum', 'bloom-levels'],
    '/curriculum/bloom-levels',
    undefined,
    { enabled: open },
  )

  const create = useEntityCreate<Record<string, unknown>, { id: string }>('/assessment/questions', [
    ['assessment', 'questions', courseVersionId],
  ])

  const form = useForm<FormInput, unknown, FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { text: '', question_type: '', marks: undefined, topic: '', author_id: '', bloom_level_id: '' },
  })

  React.useEffect(() => {
    if (open) {
      form.reset({ text: '', question_type: '', marks: undefined, topic: '', author_id: '', bloom_level_id: '' })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open])

  function toggleCO(id: string) {
    setSelectedCOs((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  async function handleSubmit(values: FormValues) {
    try {
      const question = await create.mutateAsync({
        course_version_id: courseVersionId,
        text: values.text,
        question_type: values.question_type,
        marks: values.marks,
        topic: values.topic || null,
        author_id: values.author_id || null,
      })

      const followUps: Promise<unknown>[] = []
      if (values.bloom_level_id) {
        followUps.push(
          apiClient.post('/assessment/question-bloom-mappings', {
            question_id: question.id,
            bloom_level_id: values.bloom_level_id,
          }),
        )
      }
      for (const coId of selectedCOs) {
        followUps.push(
          apiClient.post('/assessment/question-co-mappings', {
            question_id: question.id,
            course_outcome_id: coId,
          }),
        )
      }
      if (followUps.length > 0) {
        const results = await Promise.allSettled(followUps)
        if (results.some((r) => r.status === 'rejected')) {
          toast.error('Question created, but some outcome/Bloom mappings failed to save. Add them from Mappings.')
        }
      }

      toast.success('Question created')
      onOpenChange(false)
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Unable to create question.')
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85vh] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>New question</DialogTitle>
          <DialogDescription>
            Classify by Bloom&apos;s cognitive level and the course outcome(s) it assesses.
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4" noValidate>
            <FormField
              control={form.control}
              name="text"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Question text</FormLabel>
                  <FormControl>
                    <Textarea {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="question_type"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Question type</FormLabel>
                    <FormControl>
                      <Input placeholder="e.g. mcq, short_answer" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="marks"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Marks</FormLabel>
                    <FormControl>
                      <Input
                        type="number"
                        step="0.5"
                        {...field}
                        value={(field.value as number | string | undefined) ?? ''}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="bloom_level_id"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Bloom&apos;s cognitive level</FormLabel>
                  <Select value={field.value} onValueChange={field.onChange}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select a level" />
                      </SelectTrigger>
                    </FormControl>
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
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormItem>
              <FormLabel>CO mapping</FormLabel>
              <div className="max-h-40 overflow-y-auto rounded-md border p-2">
                {(outcomes ?? []).length === 0 ? (
                  <p className="px-1 py-1 text-sm text-muted-foreground">
                    No course outcomes defined for this version yet.
                  </p>
                ) : (
                  <div className="flex flex-col gap-1.5">
                    {outcomes?.map((o) => (
                      <label
                        key={o.id}
                        className="flex cursor-pointer items-start gap-2 rounded-sm px-1 py-1 text-sm hover:bg-accent"
                      >
                        <Checkbox
                          checked={selectedCOs.has(o.id)}
                          onCheckedChange={() => toggleCO(o.id)}
                          className="mt-0.5"
                        />
                        <span>
                          <span className="font-medium">{o.code}</span> — {o.statement}
                        </span>
                      </label>
                    ))}
                  </div>
                )}
              </div>
            </FormItem>

            <div className="grid grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="topic"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Topic</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="author_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Author</FormLabel>
                    <Select value={field.value} onValueChange={field.onChange}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select…" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {(users ?? []).length === 0 ? (
                          <div className="px-2 py-1.5 text-sm text-muted-foreground">None available yet</div>
                        ) : (
                          users?.map((u) => (
                            <SelectItem key={u.id} value={u.id}>
                              {u.full_name}
                            </SelectItem>
                          ))
                        )}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={form.formState.isSubmitting}>
                {form.formState.isSubmitting ? 'Saving…' : 'Create question'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
