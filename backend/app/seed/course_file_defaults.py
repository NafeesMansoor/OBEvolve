"""Loads the fixed default `course_file_types` catalogue (Faculty Module
spec §6-8) into a tenant schema. Idempotent — safe to call against a schema
that already has some or all rows (check-by-key pattern, mirrors
`app.seed.assessment_defaults`)."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.tenant.course_files import CourseFileType

# (key, name, category, applicable_course_type) — spec §6 (theory) / §7 (lab).
# `applicable_course_type` is "both" for slots common to both course kinds,
# "theory"/"lab" for the ones each spec section calls out as exclusive to
# that kind (e.g. CEP is theory-track, list-of-lab-tasks/OEP are lab-track).
DEFAULT_COURSE_FILE_TYPES: list[tuple[str, str, str, str]] = [
    # Basic
    ("course_outline", "Course Outline", "admin", "both"),
    # Attendance (§6.2 / §7)
    ("class_attendance", "Class Attendance", "attendance", "both"),
    ("midterm_attendance", "Mid-Term Attendance", "attendance", "both"),
    ("final_attendance", "Final-Term Attendance", "attendance", "both"),
    # Mid-term examination files (§6.3, theory only)
    ("midterm_moderation", "Mid-Term Question Moderation", "exam_mid", "theory"),
    ("midterm_question", "Mid-Term Question", "exam_mid", "theory"),
    ("midterm_script_highest", "Highest Sample Answer Script (Mid-Term)", "exam_mid", "theory"),
    ("midterm_script_median", "Medium Sample Answer Script (Mid-Term)", "exam_mid", "theory"),
    ("midterm_script_lowest", "Lowest Sample Answer Script (Mid-Term)", "exam_mid", "theory"),
    # Final examination files (§6.4, theory only)
    ("final_moderation", "Final Question Moderation", "exam_final", "theory"),
    ("final_question", "Final Question", "exam_final", "theory"),
    ("final_script_highest", "Highest Sample Answer Script (Final)", "exam_final", "theory"),
    ("final_script_median", "Medium Sample Answer Script (Final)", "exam_final", "theory"),
    ("final_script_lowest", "Lowest Sample Answer Script (Final)", "exam_final", "theory"),
    # Grade/marks (§6.5-6.6 / §7)
    ("final_grade_report", "Final Grade Report", "grade", "both"),
    ("marks_excel_breakdown", "Marks Excel Breakdown", "grade", "both"),
    # Complex Engineering Project — dominant theory courses only (§6.7)
    ("cep_form", "Complex Engineering Project Form", "cep", "theory"),
    ("cep_report", "Complex Engineering Project Report", "cep", "theory"),
    ("cep_rubric_highest", "Highest Rubric / Sample (CEP)", "cep", "theory"),
    ("cep_rubric_median", "Medium Rubric / Sample (CEP)", "cep", "theory"),
    ("cep_rubric_lowest", "Lowest Rubric / Sample (CEP)", "cep", "theory"),
    # Laboratory-only (§7)
    ("lab_task_list", "List of Lab Tasks", "lab", "lab"),
    ("oep_form", "Open-Ended Lab Form", "oep", "lab"),
    ("oep_report", "Open-Ended Lab Report", "oep", "lab"),
    ("oep_rubric_highest", "Highest Rubric / Sample (OEP)", "oep", "lab"),
    ("oep_rubric_median", "Medium Rubric / Sample (OEP)", "oep", "lab"),
    ("oep_rubric_lowest", "Lowest Rubric / Sample (OEP)", "oep", "lab"),
    # Complex Engineering Project — dominant lab courses only (§7)
    ("lab_cep_form", "Complex Engineering Project Form (Lab)", "cep", "lab"),
    ("lab_cep_report", "Complex Engineering Project Report (Lab)", "cep", "lab"),
    ("lab_cep_rubric_highest", "Highest Rubric / Sample (Lab CEP)", "cep", "lab"),
    ("lab_cep_rubric_median", "Medium Rubric / Sample (Lab CEP)", "cep", "lab"),
    ("lab_cep_rubric_lowest", "Lowest Rubric / Sample (Lab CEP)", "cep", "lab"),
    # Additional files common to both (§6.8 / §7)
    ("co_po_excel", "CO-PO Excel File", "admin", "both"),
    ("cqi_form", "CQI Form", "admin", "both"),
    ("excuse_absent_form", "Excuse Absent Form", "admin", "both"),
    ("class_summary_report", "Class Summary Report", "admin", "both"),
]


def seed_default_course_file_types(db: Session) -> dict[str, CourseFileType]:
    """Insert any catalogue course-file types missing from this schema.

    Returns a `key -> CourseFileType` map (including pre-existing rows).
    """
    existing = {cft.key: cft for cft in db.query(CourseFileType).all()}
    for key, name, category, applicable_course_type in DEFAULT_COURSE_FILE_TYPES:
        if key in existing:
            continue
        course_file_type = CourseFileType(
            key=key,
            name=name,
            category=category,
            applicable_course_type=applicable_course_type,
            is_custom=False,
        )
        db.add(course_file_type)
        existing[key] = course_file_type
    db.flush()
    return existing
