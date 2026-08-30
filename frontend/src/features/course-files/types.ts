export interface CourseFileType {
  id: string
  key: string
  name: string
  category: string
  applicable_course_type: 'theory' | 'lab' | 'both'
  is_custom: boolean
}

export interface CourseFileRequirement {
  id: string
  academic_term_id: string
  course_file_type_id: string
  program_version_id: string | null
  course_type: 'theory' | 'lab' | null
  course_version_id: string | null
  is_required: boolean
  deadline: string | null
  soft_copy_required: boolean
  hard_copy_required: boolean
  created_at: string
  updated_at: string
}

export type CourseFileSubmissionStatus = 'pending' | 'approved' | 'rejected'

export interface CourseFileSubmission {
  id: string
  course_section_id: string
  course_file_type_id: string
  file_name: string
  file_size: number
  content_type: string
  version: number
  hard_copy_submitted: boolean
  status: CourseFileSubmissionStatus
  submitted_by: string | null
  submitted_at: string
  reviewed_by: string | null
  reviewed_at: string | null
  review_note: string | null
}

export interface CourseFileChecklistItem {
  file_type: CourseFileType
  requirement: CourseFileRequirement | null
  submission: CourseFileSubmission | null
}
