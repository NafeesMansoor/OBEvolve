/**
 * Groups the free-text `course_type` field (DATABASE_PLAN.md §C — kept as a
 * free string since institution-specific category naming varies, e.g. ULAB
 * CSE's real catalog has 22 distinct raw values like "Concentration
 * Elective (Data Science)" and "Concentration Elective (Security)") into a
 * small, stable set of secondary tabs for the Courses list. Substring
 * matching, not an exact lookup table, so a new raw value an institution
 * introduces later (a new concentration track, say) still lands in a
 * sensible bucket automatically instead of needing a code change —
 * "extensible" in the sense the product brief asked for.
 */

export const COURSE_TYPE_CATEGORIES = [
  'Major Core',
  'Concentration Elective',
  'General Education',
  'Minor Offering',
  'Science & Math',
  'Other',
] as const

export type CourseTypeCategory = (typeof COURSE_TYPE_CATEGORIES)[number]

export function categorizeCourseType(courseType: string | null): CourseTypeCategory {
  if (!courseType) return 'Other'
  const t = courseType.toLowerCase()
  if (t.includes('major core')) return 'Major Core'
  if (t.includes('concentration elective')) return 'Concentration Elective'
  if (t.includes('general education') || t.startsWith('ged') || t.includes('ged ')) {
    return 'General Education'
  }
  if (t.includes('minor offering')) return 'Minor Offering'
  if (
    t.includes('basic science') ||
    t.includes('mathematics') ||
    t.includes('statistics') ||
    t.includes('other engineering')
  ) {
    return 'Science & Math'
  }
  return 'Other'
}
