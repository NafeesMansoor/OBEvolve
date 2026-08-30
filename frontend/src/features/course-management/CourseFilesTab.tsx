import * as React from 'react'
import { Upload } from 'lucide-react'
import { toast } from 'sonner'

import type { CourseFileChecklistItem } from '@/features/course-files/types'
import type { MyCourseCard } from '@/features/course-management/types'
import { ApiError, apiClient } from '@/lib/api-client'
import { useEntityList } from '@/lib/crud-hooks'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'

const STATUS_STYLE: Record<string, string> = {
  pending: 'bg-amber-100 text-amber-800 dark:bg-amber-950 dark:text-amber-300',
  approved: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-950 dark:text-emerald-300',
  rejected: 'bg-destructive/10 text-destructive',
}

/** Faculty Module spec §5-9, BR-04: each required document gets its own
 * independent upload control and status — never one generic upload button. */
export function CourseFilesTab({ course }: { course: MyCourseCard }) {
  const { data: items, isLoading, refetch } = useEntityList<CourseFileChecklistItem>(
    ['course-files', 'sections', course.course_section_id],
    `/course-files/sections/${course.course_section_id}`,
  )

  if (isLoading) return <Skeleton className="h-64 w-full" />
  if (!items || items.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No course files apply to this section yet.
      </p>
    )
  }

  const byCategory = items.reduce<Record<string, CourseFileChecklistItem[]>>((acc, item) => {
    ;(acc[item.file_type.category] ??= []).push(item)
    return acc
  }, {})

  return (
    <div className="flex flex-col gap-6">
      {Object.entries(byCategory).map(([category, categoryItems]) => (
        <div key={category} className="flex flex-col gap-3">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
            {category.replace(/_/g, ' ')}
          </h3>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            {categoryItems.map((item) => (
              <CourseFileRow
                key={item.file_type.id}
                courseSectionId={course.course_section_id}
                item={item}
                canUpload={course.is_current_term}
                onUploaded={() => void refetch()}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

function CourseFileRow({
  courseSectionId,
  item,
  canUpload,
  onUploaded,
}: {
  courseSectionId: string
  item: CourseFileChecklistItem
  canUpload: boolean
  onUploaded: () => void
}) {
  const fileInputRef = React.useRef<HTMLInputElement>(null)
  const [isUploading, setIsUploading] = React.useState(false)
  const required = item.requirement?.is_required ?? false

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    e.target.value = ''
    if (!file) return
    setIsUploading(true)
    try {
      const formData = new FormData()
      formData.append('file', file)
      await apiClient.post(
        `/course-files/sections/${courseSectionId}/${item.file_type.id}/upload`,
        formData,
      )
      toast.success(`${item.file_type.name} uploaded`)
      onUploaded()
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Upload failed')
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-2">
          <CardTitle className="text-sm">{item.file_type.name}</CardTitle>
          {required ? (
            <Badge variant="outline" className="shrink-0 font-normal">
              Required
            </Badge>
          ) : (
            <Badge variant="secondary" className="shrink-0 font-normal">
              Optional
            </Badge>
          )}
        </div>
        {item.requirement?.deadline && (
          <CardDescription>
            Due {new Date(item.requirement.deadline).toLocaleDateString()}
          </CardDescription>
        )}
      </CardHeader>
      <CardContent className="flex items-center justify-between gap-3">
        {item.submission ? (
          <div className="flex flex-col gap-1 text-xs">
            <span className="font-medium text-foreground">
              {item.submission.file_name} · v{item.submission.version}
            </span>
            <Badge className={STATUS_STYLE[item.submission.status]} variant="outline">
              {item.submission.status}
            </Badge>
          </div>
        ) : (
          <span className="text-xs text-muted-foreground">Not submitted</span>
        )}
        {canUpload ? (
          <>
            <Button
              size="sm"
              variant="outline"
              disabled={isUploading}
              onClick={() => fileInputRef.current?.click()}
            >
              <Upload className="size-3.5" />
              {isUploading ? 'Uploading…' : item.submission ? 'Replace' : 'Upload'}
            </Button>
            <input ref={fileInputRef} type="file" className="hidden" onChange={handleFileChange} />
          </>
        ) : (
          <span className="text-xs text-muted-foreground">Read-only</span>
        )}
      </CardContent>
    </Card>
  )
}
