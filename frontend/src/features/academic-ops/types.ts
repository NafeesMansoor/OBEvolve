export interface CourseOffering {
  id: string
  course_version_id: string
  academic_term_id: string
  program_version_id: string | null
  created_at: string
  updated_at: string
}

export interface CourseSection {
  id: string
  course_offering_id: string
  section_code: string
  max_students: number | null
  created_at: string
  updated_at: string
}

export interface FacultyAssignment {
  id: string
  course_section_id: string
  faculty_user_id: string
  /** Resolved server-side — see backend FacultyAssignmentRead.faculty_name. */
  faculty_name: string | null
  role: 'coordinator' | 'instructor'
  created_at: string
  updated_at: string
}

export interface StudentEnrollment {
  id: string
  student_user_id: string
  course_section_id: string
  enrollment_status: string
  enrolled_at: string
}

export interface Student {
  user_id: string
  email: string
  full_name: string
  is_active: boolean
  student_code: string
  program_id: string | null
  program_version_id: string | null
  batch_year: number | null
  status: string
}
