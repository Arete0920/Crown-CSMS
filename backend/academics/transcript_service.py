from __future__ import annotations

from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from uuid import UUID

from django.db.models import Sum

from gradebook.models import GradeEntry

from .models import Assignment, AssignmentCategory, Enrollment, TranscriptEntry


ZERO = Decimal("0.00")
GPA_QUANTUM = Decimal("0.01")
LETTER_POINTS = {
    "A": Decimal("4.00"),
    "B": Decimal("3.00"),
    "C": Decimal("2.00"),
    "D": Decimal("1.00"),
    "F": Decimal("0.00"),
}
PASSING_LETTERS = frozenset({"A", "B", "C", "D"})


def letter_from_percent(value: Decimal | None) -> str | None:
    if value is None:
        return None
    if value >= Decimal("90"):
        return "A"
    if value >= Decimal("80"):
        return "B"
    if value >= Decimal("70"):
        return "C"
    if value >= Decimal("60"):
        return "D"
    return "F"


def _simple_section_percent(school_id, section_id, student_id) -> Decimal | None:
    aggregate = GradeEntry.objects.filter(
        school_id=school_id,
        section_id=section_id,
        student_id=student_id,
    ).aggregate(earned=Sum("points_earned"), possible=Sum("points_possible"))
    earned = aggregate["earned"]
    possible = aggregate["possible"]
    if earned is None or possible is None or Decimal(str(possible)) <= 0:
        return None
    return (Decimal(str(earned)) / Decimal(str(possible)) * 100).quantize(
        Decimal("0.1"), rounding=ROUND_HALF_UP
    )


def compute_section_percent(school_id, section_id, student_id) -> Decimal | None:
    categories = list(
        AssignmentCategory.objects.filter(
            school_id=school_id,
            section_id=section_id,
            is_active=True,
        ).order_by("sort_order")
    )
    if not categories:
        return _simple_section_percent(school_id, section_id, student_id)

    total_weight = sum((Decimal(str(row.weight_percent)) for row in categories), ZERO)
    if total_weight != Decimal("100"):
        return _simple_section_percent(school_id, section_id, student_id)

    assignment_rows = list(
        Assignment.objects.filter(
            school_id=school_id,
            section_id=section_id,
            is_published=True,
        )
    )
    assignments_by_id = {row.id: row for row in assignment_rows}
    assignments_by_name = {row.name: row for row in assignment_rows}
    buckets: dict[UUID, dict[str, Decimal]] = {
        row.id: {
            "earned": ZERO,
            "possible": ZERO,
            "weight": Decimal(str(row.weight_percent)),
        }
        for row in categories
    }
    for entry in GradeEntry.objects.filter(
        school_id=school_id,
        section_id=section_id,
        student_id=student_id,
    ):
        assignment = assignments_by_id.get(entry.assignment_id)
        if assignment is None:
            assignment = assignments_by_name.get(entry.assignment_name)
        if assignment is None:
            continue
        bucket = buckets.get(assignment.category_id)
        if bucket is None:
            continue
        if entry.points_earned is not None:
            bucket["earned"] += Decimal(str(entry.points_earned))
        if entry.points_possible is not None:
            bucket["possible"] += Decimal(str(entry.points_possible))

    included = [row for row in buckets.values() if row["possible"] > 0]
    if not included:
        return None
    included_weight = sum((row["weight"] for row in included), ZERO)
    if included_weight <= 0:
        return None

    result = ZERO
    for row in included:
        result += (row["earned"] / row["possible"]) * (row["weight"] / included_weight)
    return (result * 100).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def _entry_map(school_id, student_id):
    entries = TranscriptEntry.objects.filter(
        school_id=school_id,
        student_id=student_id,
    ).select_related("course", "term")
    exact = {}
    course_fallback = {}
    for entry in entries:
        exact[(entry.course_id, entry.term_id)] = entry
        if entry.term_id is None:
            course_fallback[entry.course_id] = entry
    return exact, course_fallback


def _is_finalized(entry: TranscriptEntry | None) -> bool:
    if entry is None:
        return False
    return bool((entry.final_letter_grade or "").strip()) or entry.final_percentage is not None


def _decimal_string(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return str(value.quantize(GPA_QUANTUM, rounding=ROUND_HALF_UP))


def _term_identity(section):
    term = section.term_ref
    term_code = section.term or "UNKNOWN"
    term_id = str(getattr(term, "id", "") or "")
    term_name = getattr(term, "name", "") or term_code
    school_year = (
        getattr(term, "school_year", "")
        or getattr(getattr(term, "academic_year", None), "name", "")
        or "UNKNOWN"
    )
    ordering = getattr(term, "ordering", 0) if term is not None else 0
    return term_id, term_code, term_name, school_year, ordering


def _course_row(*, school_id, student_id, section, transcript_entry):
    finalized = _is_finalized(transcript_entry)
    calculated_percent = compute_section_percent(school_id, section.id, student_id)
    provider = (getattr(transcript_entry, "provider", "") or "").strip()
    dual_label = (getattr(transcript_entry, "dual_enrollment_label", "") or "").strip()

    if finalized:
        final_percent = (
            Decimal(str(transcript_entry.final_percentage))
            if transcript_entry.final_percentage is not None
            else calculated_percent
        )
        final_letter = (transcript_entry.final_letter_grade or "").strip().upper() or letter_from_percent(final_percent)
        credits = Decimal(str(transcript_entry.credit_value or 0))
        gpa_points = Decimal(str(transcript_entry.gpa_points)) if final_letter in LETTER_POINTS else None
        status = "final"
    else:
        final_percent = calculated_percent
        final_letter = letter_from_percent(calculated_percent)
        credits = Decimal(str(getattr(section.course, "credits", 0) or 0))
        gpa_points = LETTER_POINTS.get(final_letter) if final_letter else None
        status = "in_progress"

    gpa_included = bool(finalized and final_letter in LETTER_POINTS and credits > 0)
    earned_credits = credits if finalized and final_letter in PASSING_LETTERS else ZERO
    attempted_credits = credits if finalized else ZERO

    term_id, term_code, term_name, school_year, ordering = _term_identity(section)
    return {
        "section_id": str(section.id),
        "course_id": str(section.course_id),
        "course_code": getattr(section.course, "code", ""),
        "course_name": getattr(section.course, "name", ""),
        "teacher_name": getattr(section, "teacher_name", "") or "",
        "final_percent": float(final_percent) if final_percent is not None else None,
        "final_letter": final_letter,
        "credits": _decimal_string(credits),
        "attempted_credits": _decimal_string(attempted_credits),
        "earned_credits": _decimal_string(earned_credits),
        "gpa_points": _decimal_string(gpa_points),
        "gpa_included": gpa_included,
        "record_status": status,
        "provider": provider,
        "dual_enrollment_label": dual_label,
        "term_id": term_id or None,
        "term_code": term_code,
        "term_name": term_name,
        "school_year": school_year,
        "term_ordering": ordering,
    }


def _weighted_gpa(rows: list[dict[str, Any]]) -> Decimal | None:
    included = [row for row in rows if row["gpa_included"]]
    denominator = sum((Decimal(row["attempted_credits"]) for row in included), ZERO)
    if denominator <= 0:
        return None
    numerator = sum(
        (
            Decimal(row["gpa_points"]) * Decimal(row["attempted_credits"])
            for row in included
        ),
        ZERO,
    )
    return (numerator / denominator).quantize(GPA_QUANTUM, rounding=ROUND_HALF_UP)


def build_transcript_snapshot(*, school_id, student) -> dict[str, Any]:
    enrollments = list(
        Enrollment.objects.filter(
            school_id=school_id,
            student_id=student.id,
        )
        .select_related(
            "section__course",
            "section__term_ref",
            "section__term_ref__academic_year",
        )
        .order_by("section__term_ref__ordering", "section__term", "section__course__code", "section_id")
    )
    exact_entries, course_fallback = _entry_map(school_id, student.id)

    rows = []
    for enrollment in enrollments:
        section = enrollment.section
        entry = exact_entries.get((section.course_id, section.term_ref_id)) or course_fallback.get(section.course_id)
        rows.append(
            _course_row(
                school_id=school_id,
                student_id=student.id,
                section=section,
                transcript_entry=entry,
            )
        )

    terms: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        key = (row["term_id"] or row["term_code"], row["school_year"])
        block = terms.setdefault(
            key,
            {
                "term_id": row["term_id"],
                "term_code": row["term_code"],
                "term_name": row["term_name"],
                "school_year": row["school_year"],
                "term_ordering": row["term_ordering"],
                "courses": [],
            },
        )
        block["courses"].append(row)

    term_blocks = []
    for block in sorted(
        terms.values(),
        key=lambda value: (value["school_year"], value["term_ordering"], value["term_code"]),
    ):
        block["courses"].sort(key=lambda row: (row["course_code"], row["section_id"]))
        term_gpa = _weighted_gpa(block["courses"])
        block["term_gpa"] = _decimal_string(term_gpa)
        block["attempted_credits"] = _decimal_string(
            sum((Decimal(row["attempted_credits"]) for row in block["courses"]), ZERO)
        )
        block["earned_credits"] = _decimal_string(
            sum((Decimal(row["earned_credits"]) for row in block["courses"]), ZERO)
        )
        block.pop("term_ordering", None)
        term_blocks.append(block)

    cumulative_gpa = _weighted_gpa(rows)
    return {
        "student": {
            "student_id": str(student.id),
            "first_name": student.first_name,
            "last_name": student.last_name,
            "grade_level": getattr(student, "grade_level", None),
        },
        "terms": term_blocks,
        "cumulative_gpa": _decimal_string(cumulative_gpa),
        "attempted_credits": _decimal_string(
            sum((Decimal(row["attempted_credits"]) for row in rows), ZERO)
        ),
        "earned_credits": _decimal_string(
            sum((Decimal(row["earned_credits"]) for row in rows), ZERO)
        ),
        "notes": [
            "GPA and earned-credit totals include finalized transcript entries only.",
            "In-progress course grades are calculated from the current gradebook and are excluded from official GPA totals until finalized.",
            "Dual-enrollment/provider labels do not change GPA points unless finalized transcript data explicitly records different GPA points.",
        ],
    }


def build_student_contract(snapshot: dict[str, Any]) -> dict[str, Any]:
    by_year: dict[str, dict[str, Any]] = defaultdict(lambda: {"school_year": "", "terms": []})
    for term in snapshot["terms"]:
        year = term["school_year"]
        if not by_year[year]["school_year"]:
            by_year[year]["school_year"] = year
        by_year[year]["terms"].append(
            {
                "term_id": term["term_id"],
                "term_name": term["term_name"],
                "term_code": term["term_code"],
                "term_gpa": term["term_gpa"],
                "attempted_credits": term["attempted_credits"],
                "earned_credits": term["earned_credits"],
                "courses": [
                    {
                        "section_id": row["section_id"],
                        "course_code": row["course_code"],
                        "course_name": row["course_name"],
                        "credits": row["credits"],
                        "attempted_credits": row["attempted_credits"],
                        "earned_credits": row["earned_credits"],
                        "teacher": row["teacher_name"],
                        "final_grade": row["final_letter"],
                        "final_percent": row["final_percent"],
                        "gpa_points": row["gpa_points"],
                        "gpa_included": row["gpa_included"],
                        "status": row["record_status"],
                        "provider": row["provider"],
                        "dual_enrollment_label": row["dual_enrollment_label"],
                    }
                    for row in term["courses"]
                ],
            }
        )

    student = snapshot["student"]
    return {
        "student_id": student["student_id"],
        "student_name": f"{student['first_name']} {student['last_name']}".strip(),
        "cumulative_gpa": snapshot["cumulative_gpa"],
        "attempted_credits": snapshot["attempted_credits"],
        "earned_credits": snapshot["earned_credits"],
        "school_years": [by_year[key] for key in sorted(by_year)],
    }
