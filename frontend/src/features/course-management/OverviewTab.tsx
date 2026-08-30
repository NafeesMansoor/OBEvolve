import * as React from 'react'
import { toast } from 'sonner'

import type { FacultyAssignment } from '@/features/academic-ops/types'
import { useAuth } from '@/features/auth/useAuth'
import type { MyCourseCard } from '@/features/course-management/types'
import { ApiError, apiClient } from '@/lib/api-client'
import { useEntityList } from '@/lib/crud-hooks'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'

/** Faculty Module spec §4.1: read-only course info, plus the three fields
 * a faculty member can edit directly (office/consultation/meeting link) —
 * everything else in Course Settings routes through a change request. */
export function OverviewTab({ course }: { course: MyCourseCard }) {
  const { user } = useAuth()
  const { data: assignments, isLoading } = useEntityList<FacultyAssignment>(
    ['academic', 'faculty-assignments', course.course_section_id],
    '/academic/faculty-assignments',
    { course_section_id: course.course_section_id },
  )
  const mine = assignments?.find((a) => a.faculty_user_id === user?.id)

  return (
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
          <CardDescription>
            Shown to students for this section. Everything else on Course Settings
            requires a modification request.
          </CardDescription>
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
