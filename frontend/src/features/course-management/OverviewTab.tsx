import * as React from 'react'
import { toast } from 'sonner'

import type { FacultyAssignment } from '@/features/academic-ops/types'
import { useAuth } from '@/features/auth/useAuth'
import type { CourseChangeRequest } from '@/features/change-requests/types'
import { ChangeRequestRow } from '@/features/change-requests/ChangeRequestRow'
import { BulletList } from '@/features/course-management/BulletList'
import { InlineEditableField } from '@/features/course-management/InlineEditableField'
import type { MyCourseCard } from '@/features/course-management/types'
import type { Course, CourseVersion } from '@/features/curriculum/types'
import { ApiError, apiClient } from '@/lib/api-client'
import { useEntityCreate, useEntityGet, useEntityList } from '@/lib/crud-hooks'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import { Table, TableBody, TableHead, TableHeader, TableRow } from '@/components/ui/table'

/** Faculty Module spec §4.1 + Course-Level Settings spec §5.A: read-only
 * course info, the description/objectives (single-stage change-request
 * flow, gated by the "overview" section being enabled for this course's
 * type, edited inline — double-click a field, Wix-editor-style, rather
 * than a separate button + modal — see `InlineEditableField`), and the
 * three fields a faculty member can edit directly (office/consultation/
 * meeting link — a personal detail, not course content, so it stays a
 * direct write). */
export function OverviewTab({ course }: { course: MyCourseCard }) {
  const { user } = useAuth()
  const { data: assignments, isLoading } = useEntityList<FacultyAssignment>(
    ['academic', 'faculty-assignments', course.course_section_id],
    '/academic/faculty-assignments',
    { course_section_id: course.course_section_id },
  )
  const mine = assignments?.find((a) => a.faculty_user_id === user?.id)

  const { data: courseVersion } = useEntityGet<CourseVersion>(
    ['curriculum', 'course-version', course.course_version_id],
    `/curriculum/course-versions/${course.course_version_id}`,
  )
  const { data: courseDetail } = useEntityGet<Course>(
    ['curriculum', 'course', courseVersion?.course_id ?? ''],
    `/curriculum/courses/${courseVersion?.course_id}`,
    { enabled: Boolean(courseVersion?.course_id) },
  )
  const { data: sectionConfig } = useEntityGet<Record<string, boolean>>(
    ['course-types', 'resolve', course.course_section_id],
    `/course-types/resolve/${course.course_section_id}`,
  )
  const overviewEnabled = sectionConfig?.overview ?? false

  const { data: requests, isLoading: requestsLoading } = useEntityList<CourseChangeRequest>(
    ['course-change-requests', course.course_section_id, 'overview'],
    '/course-change-requests',
    { course_section_id: course.course_section_id },
  )
  const overviewRequests = (requests ?? []).filter((r) => r.section_key === 'overview')
  const create = useEntityCreate<Record<string, unknown>>('/course-change-requests', [
    ['course-change-requests', course.course_section_id],
  ])

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Course information</CardTitle>
            <CardDescription>Approved academic and scheduling details.</CardDescription>
          </CardHeader>
          <CardContent className="grid grid-cols-2 gap-4 text-sm">
            <Field label="Course code" value={course.course_code} />
            <Field label="Section" value={course.section_code} />
            <Field label="Title" value={course.course_title} />
            <Field label="Term" value={course.term_name} />
            <Field label="Credits" value={course.credits} />
            <Field label="Enrolled" value={String(course.enrolled_count)} />
            <Field label="Your role" value={mine?.role ?? '—'} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Your contact information</CardTitle>
            <CardDescription>Shown to students for this section.</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-32" />
            ) : mine ? (
              <ContactInfoForm assignment={mine} />
            ) : (
              <p className="text-sm text-muted-foreground">Assignment record not found.</p>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Description &amp; objectives</CardTitle>
          <CardDescription>
            {overviewEnabled && course.is_current_term
              ? 'Double-click a field to propose a change — your Section Coordinator approves and it becomes final.'
              : 'Not enabled for editing on this course type.'}
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-3 text-sm">
          <div>
            <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Description
            </p>
            <InlineEditableField
              value={courseDetail?.description}
              editable={overviewEnabled && course.is_current_term}
              multiline
              onSave={async (newValue, message) => {
                try {
                  await create.mutateAsync({
                    course_section_id: course.course_section_id,
                    section_key: 'overview',
                    target_field: 'description',
                    proposed_value_json: { value: newValue },
                    reason: message,
                  })
                  toast.success('Sent to your Section Coordinator for review')
                } catch (err) {
                  toast.error(err instanceof ApiError ? err.detail : 'Unable to submit change')
                  throw err
                }
              }}
            />
          </div>
          <div>
            <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Objectives
            </p>
            <InlineEditableField
              value={courseVersion?.objectives}
              editable={overviewEnabled && course.is_current_term}
              multiline
              renderDisplay={(v) => <BulletList text={v} empty="No objectives on file." />}
              onSave={async (newValue, message) => {
                try {
                  await create.mutateAsync({
                    course_section_id: course.course_section_id,
                    section_key: 'overview',
                    target_field: 'objectives',
                    proposed_value_json: { value: newValue },
                    reason: message,
                  })
                  toast.success('Sent to your Section Coordinator for review')
                } catch (err) {
                  toast.error(err instanceof ApiError ? err.detail : 'Unable to submit change')
                  throw err
                }
              }}
            />
          </div>

          {requestsLoading ? (
            <Skeleton className="h-16 w-full" />
          ) : overviewRequests.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Field</TableHead>
                  <TableHead>Current</TableHead>
                  <TableHead>Proposed</TableHead>
                  <TableHead>Edited</TableHead>
                  <TableHead>Reason</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Submitted</TableHead>
                  <TableHead className="text-right">Review</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {overviewRequests.map((r) => (
                  <ChangeRequestRow key={r.id} request={r} />
                ))}
              </TableBody>
            </Table>
          ) : null}
        </CardContent>
      </Card>
    </div>
  )
}

function Field({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="font-medium">{value}</p>
    </div>
  )
}

function ContactInfoForm({ assignment }: { assignment: FacultyAssignment }) {
  const [officeLocation, setOfficeLocation] = React.useState(assignment.office_location ?? '')
  const [consultationHours, setConsultationHours] = React.useState(
    assignment.consultation_hours ?? '',
  )
  const [meetingLink, setMeetingLink] = React.useState(assignment.meeting_link ?? '')
  const [isSaving, setIsSaving] = React.useState(false)

  async function handleSave() {
    setIsSaving(true)
    try {
      await apiClient.patch(`/academic/faculty-assignments/${assignment.id}/contact-info`, {
        office_location: officeLocation || null,
        consultation_hours: consultationHours || null,
        meeting_link: meetingLink || null,
      })
      toast.success('Contact information saved')
    } catch (err) {
      toast.error(err instanceof ApiError ? err.detail : 'Failed to save')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="space-y-1.5">
        <Label htmlFor="office-location">Office & location</Label>
        <Input
          id="office-location"
          value={officeLocation}
          onChange={(e) => setOfficeLocation(e.target.value)}
          placeholder="Room 402, CSE Building"
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="consultation-hours">Consultation hours</Label>
        <Input
          id="consultation-hours"
          value={consultationHours}
          onChange={(e) => setConsultationHours(e.target.value)}
          placeholder="Sun/Tue 2-4pm"
        />
      </div>
      <div className="space-y-1.5">
        <Label htmlFor="meeting-link">Classroom / meeting link</Label>
        <Input
          id="meeting-link"
          value={meetingLink}
          onChange={(e) => setMeetingLink(e.target.value)}
          placeholder="https://meet.example.org/..."
        />
      </div>
      <Button onClick={handleSave} disabled={isSaving} className="self-start">
        {isSaving ? 'Saving…' : 'Save'}
      </Button>
    </div>
  )
}
