import * as React from 'react'
import { Download, Plus, Trash2 } from 'lucide-react'
import { toast } from 'sonner'
import { z } from 'zod'

import { useAuth } from '@/features/auth/useAuth'
import { useAcademicTermLookup, useCourseVersionLookup } from '@/features/academic-ops/useLookups'
import { ImportFromOfferingDialog } from '@/features/academic-ops/ImportFromOfferingDialog'
import type { CourseOffering, CourseSection, FacultyAssignment } from '@/features/academic-ops/types'
import { apiClient, ApiError } from '@/lib/api-client'
import { useEntityCreate, useEntityDelete, useEntityList } from '@/lib/crud-hooks'
import { useResetOnChange } from '@/lib/use-reset-on-change'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ConfirmAction } from '@/components/confirm-action'
import { DataTable, type DataTableColumn } from '@/components/data-table'
import { EntityFormDialog, type EntityField } from '@/components/entity-form-dialog'
import { RecordDetailSheet } from '@/components/record-detail-sheet'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'

const schema = z.object({
  faculty_user_id: z.string().min(1, 'Faculty member is required'),
  role: z.enum(['coordinator', 'instructor']),
})

interface FacultyDirectoryEntry {
  id: string
  full_name: string
}

export function FacultyAssignmentsTab() {
  const { hasPermission } = useAuth()
  const canManage = hasPermission('section.manage')
  const { labelFor } = useCourseVersionLookup()
  const { termById } = useAcademicTermLookup()
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

  const { data: faculty } = useEntityList<FacultyDirectoryEntry>(
    ['users', 'faculty-directory'],
    '/users/faculty-directory',
  )

  const [createOpen, setCreateOpen] = React.useState(false)
  const [importOpen, setImportOpen] = React.useState(false)
  const [viewAssignment, setViewAssignment] = React.useState<FacultyAssignment | null>(null)

  const currentOffering = React.useMemo(
    () => (offerings ?? []).find((o) => o.id === offeringId),
    [offerings, offeringId],
  )
  const currentSection = React.useMemo(
    () => (sections ?? []).find((s) => s.id === sectionId),
    [sections, sectionId],
  )
  // Other offerings of the SAME course (different term) — a faculty
  // assignment is only importable if that term's offering has a section
  // with the same section_code, checked at import time (a matching
  // offering doesn't guarantee a matching section — sections aren't linked
  // across terms any other way).
  const importCandidates = React.useMemo(() => {
    if (!currentOffering) return []
    return (offerings ?? [])
      .filter((o) => o.id !== offeringId && o.course_version_id === currentOffering.course_version_id)
      .map((o) => ({ label: termById.get(o.academic_term_id)?.name ?? 'Unknown term', value: o.id }))
  }, [offerings, offeringId, currentOffering, termById])

  const {
    data: assignments,
    isLoading,
    error,
  } = useEntityList<FacultyAssignment>(
    ['academic', 'faculty-assignments', sectionId],
    '/academic/faculty-assignments',
    { course_section_id: sectionId || undefined },
    { enabled: Boolean(sectionId) },
  )
  const create = useEntityCreate<Record<string, unknown>, FacultyAssignment>(
    '/academic/faculty-assignments',
    [['academic', 'faculty-assignments', sectionId]],
  )
  const remove = useEntityDelete((id) => `/academic/faculty-assignments/${id}`, [
    ['academic', 'faculty-assignments', sectionId],
  ])

  const offeringOptions = React.useMemo(
    () =>
      (offerings ?? []).map((o) => ({
        label: `${labelFor(o.course_version_id)} · ${termById.get(o.academic_term_id)?.name ?? ''}`,
        value: o.id,
      })),
    [offerings, labelFor, termById],
  )

  const fields: EntityField[] = [
    {
      name: 'faculty_user_id',
      label: 'Faculty member',
      type: 'select',
      options: (faculty ?? []).map((f) => ({ label: f.full_name, value: f.id })),
    },
    {
      name: 'role',
      label: 'Role',
      type: 'select',
      options: [
        { label: 'Coordinator', value: 'coordinator' },
        { label: 'Instructor', value: 'instructor' },
      ],
    },
  ]

  const columns: DataTableColumn<FacultyAssignment>[] = [
    { key: 'faculty', header: 'Faculty', render: (r) => r.faculty_name ?? r.faculty_user_id },
    {
      key: 'role',
      header: 'Role',
      render: (r) => (
        <Badge variant="secondary" className="font-normal capitalize">
          {r.role}
        </Badge>
      ),
    },
  ]

  return (
    <div className="flex flex-col gap-4">
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
        {canManage && sectionId && (
          <>
            <Button size="sm" variant="outline" onClick={() => setImportOpen(true)}>
              <Download className="size-4" /> Import from term
            </Button>
            <Button size="sm" onClick={() => setCreateOpen(true)}>
              <Plus className="size-4" /> Assign faculty
            </Button>
          </>
        )}
      </div>

      {!sectionId ? (
        <p className="text-sm text-muted-foreground">Select an offering and section to see assignments.</p>
      ) : (
        <DataTable
          data={assignments}
          columns={columns}
          rowKey={(r) => r.id}
          isLoading={isLoading}
          error={error}
          emptyMessage="No faculty assigned to this section yet."
          onRowClick={(r) => setViewAssignment(r)}
          actions={
            canManage
              ? (r) => (
                  <ConfirmAction
                    trigger={
                      <Button size="sm" variant="ghost" aria-label="Remove assignment">
                        <Trash2 className="size-4" />
                      </Button>
                    }
                    title="Remove this faculty assignment?"
                    onConfirm={async () => {
                      try {
                        await remove.mutateAsync(r.id)
                        toast.success('Assignment removed')
                      } catch (err) {
                        toast.error(err instanceof ApiError ? err.detail : 'Unable to remove assignment.')
                      }
                    }}
                  />
                )
              : undefined
          }
        />
      )}

      {viewAssignment && (
        <RecordDetailSheet
          open={Boolean(viewAssignment)}
          onOpenChange={(open) => !open && setViewAssignment(null)}
          title={viewAssignment.faculty_name ?? viewAssignment.faculty_user_id}
          subtitle={currentSection ? `Section ${currentSection.section_code}` : undefined}
          fields={[
            { label: 'Faculty', value: viewAssignment.faculty_name ?? viewAssignment.faculty_user_id },
            { label: 'Role', value: <span className="capitalize">{viewAssignment.role}</span> },
          ]}
        />
      )}

      <EntityFormDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        title="Assign faculty"
        fields={fields}
        schema={schema}
        defaultValues={{ faculty_user_id: '', role: 'instructor' }}
        onSubmit={async (values) => {
          try {
            await create.mutateAsync({
              course_section_id: sectionId,
              faculty_user_id: values.faculty_user_id,
              role: values.role,
            })
            toast.success('Faculty assigned')
          } catch (err) {
            throw err instanceof ApiError ? err : new ApiError('Unable to assign faculty.')
          }
        }}
      />

      <ImportFromOfferingDialog
        open={importOpen}
        onOpenChange={setImportOpen}
        entityLabel="Faculty assignments"
        candidateOfferings={importCandidates}
        onImport={async (sourceOfferingId) => {
          if (!currentSection) return
          const sourceSections = (
            await apiClient.get<CourseSection[]>('/academic/sections', {
              params: { course_offering_id: sourceOfferingId },
            })
          ).data
          const sourceSection = sourceSections.find(
            (s) => s.section_code === currentSection.section_code,
          )
          if (!sourceSection) {
            toast.error(
              `That term has no section "${currentSection.section_code}" for this course to import from.`,
            )
            return
          }

          const sourceAssignments = (
            await apiClient.get<FacultyAssignment[]>('/academic/faculty-assignments', {
              params: { course_section_id: sourceSection.id },
            })
          ).data
          const existing = new Set((assignments ?? []).map((a) => a.faculty_user_id))
          const toImport = sourceAssignments.filter((a) => !existing.has(a.faculty_user_id))

          let imported = 0
          for (const assignment of toImport) {
            try {
              await create.mutateAsync({
                course_section_id: sectionId,
                faculty_user_id: assignment.faculty_user_id,
                role: assignment.role,
              })
              imported += 1
            } catch {
              // Best-effort: one failure doesn't abort the rest of the batch.
            }
          }
          const skipped = sourceAssignments.length - toImport.length
          toast.success(
            `Imported ${imported} assignment${imported === 1 ? '' : 's'}` +
              (skipped > 0 ? ` (${skipped} already existed)` : ''),
          )
        }}
      />
    </div>
  )
}
