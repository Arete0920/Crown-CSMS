from __future__ import annotations

from collections import OrderedDict
from decimal import Decimal
from uuid import UUID

from .models import TeacherAssignment


def _decimal(value) -> Decimal:
    if value is None:
        return Decimal("0.00")
    return Decimal(str(value))


def faculty_load_summary(
    school_id: UUID,
    *,
    term: str | None = None,
    academic_year_id: UUID | None = None,
) -> list[dict]:
    """Return deterministic faculty load totals from section teacher assignments."""

    qs = (
        TeacherAssignment.objects.filter(school_id=school_id)
        .select_related("staff", "section", "section__course", "section__term_ref")
        .order_by(
            "staff__last_name",
            "staff__first_name",
            "staff__id",
            "section__course__code",
            "section__id",
        )
    )

    if term:
        qs = qs.filter(section__term=term)

    if academic_year_id:
        qs = qs.filter(section__term_ref__academic_year_id=academic_year_id)

    rows: OrderedDict[str, dict] = OrderedDict()

    for assignment in qs:
        staff = assignment.staff
        section = assignment.section
        course = section.course

        key = str(staff.id)
        if key not in rows:
            rows[key] = {
                "staff_id": key,
                "staff_name": f"{staff.last_name}, {staff.first_name}".strip(", "),
                "staff_email": staff.email,
                "role_type": staff.role_type,
                "section_count": 0,
                "credit_load": Decimal("0.00"),
                "sections": [],
            }

        credit_value = _decimal(getattr(course, "credits", Decimal("0.00")))

        rows[key]["section_count"] += 1
        rows[key]["credit_load"] += credit_value
        rows[key]["sections"].append(
            {
                "section_id": str(section.id),
                "course_id": str(course.id),
                "course_code": course.code,
                "course_name": course.name,
                "term": section.term,
                "credits": credit_value,
            }
        )

    return list(rows.values())


def faculty_load_conflicts(
    school_id: UUID,
    *,
    term: str | None = None,
    academic_year_id: UUID | None = None,
    max_sections: int | None = None,
    max_credits: Decimal | str | None = None,
) -> list[dict]:
    """Return faculty load conflicts against explicit section/credit thresholds."""

    credit_threshold = _decimal(max_credits) if max_credits is not None else None
    conflicts: list[dict] = []

    for row in faculty_load_summary(
        school_id,
        term=term,
        academic_year_id=academic_year_id,
    ):
        reasons: list[str] = []

        if max_sections is not None and row["section_count"] > max_sections:
            reasons.append("SECTION_OVERLOAD")

        if credit_threshold is not None and row["credit_load"] > credit_threshold:
            reasons.append("CREDIT_OVERLOAD")

        if reasons:
            conflicts.append(
                {
                    "staff_id": row["staff_id"],
                    "staff_name": row["staff_name"],
                    "section_count": row["section_count"],
                    "credit_load": row["credit_load"],
                    "conflict_types": reasons,
                    "sections": row["sections"],
                }
            )

    return conflicts
