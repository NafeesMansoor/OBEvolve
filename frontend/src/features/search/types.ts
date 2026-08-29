export type SearchResultType =
  | 'course'
  | 'student'
  | 'faculty'
  | 'assessment'
  | 'program_outcome'
  | 'course_outcome'
  | 'program'

export interface SearchResult {
  type: SearchResultType
  id: string
  title: string
  subtitle: string | null
  url_hint: string
}

export interface SearchResponse {
  results: SearchResult[]
}

export const SEARCH_TYPE_LABELS: Record<SearchResultType, string> = {
  course: 'Courses',
  student: 'Students',
  faculty: 'Faculty',
  assessment: 'Assessments',
  program_outcome: 'Program outcomes',
  course_outcome: 'Course outcomes',
  program: 'Programs',
}
