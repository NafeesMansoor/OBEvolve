"""Course catalog (DATABASE_PLAN.md §C — catalog implemented, delivery
still planned).
"""

from app.models.tenant.courses.catalog import Course, CourseVersion

__all__ = ["Course", "CourseVersion"]
