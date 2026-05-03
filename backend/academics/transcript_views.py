from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from django.db.models import Sum
from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from academics.models import Assignment, AssignmentCategory, Enrollment, TranscriptEntry
from gradebook.models import GradeEntry
from households.models import Student


def _letter_from_percent(pct: Optional[float]) -> str:
    if pct is None:
        return "N/A"
    if pct >= 90:
        return "A"
    if pct >= 80:
        return "B"
    if pct >= 70:
        return "C"
    if pct >= 60:
        return "D"
    return "F"


def _gpa_points(letter: str) -> float:
    return {"A": 4.0, "B": 3.0, "C": 2.0, "D": 1.0, "F": 0.0}.get(letter, 0.0)


def _simple_section_percent(
    school_id: str,
    section_id: UUID,
    student_id: UUID,
) -> Optional[float]:
    agg = (
        GradeEntry.objects
        .filter(school_id=school_id, section_id=section_id, student_id=student_id)
        .aggregate(
            earned=Sum("points_earned"),
            possible=Sum("points_possible"),
        )
    )
    earned = float(agg["earned"]) if agg["earned"] is not None else None
    possible = float(agg["possible"]) if agg["possible"] is not None else None
    if earned is not None and possible and possible > 0:
        return round((earned / possible) * 100.0, 1)
    return None


def _section_categories(school_id: str, section_id: UUID) -> List[AssignmentCategory]:
    return list(
        AssignmentCategory.objects.filter(
            school_id=school_id,
            section_id=section_id,
            is_active=True,
        ).order_by("sort_order")
    )


def _assignments_by_name(school_id: str, section_id: UUID) -> Dict[str, Assignment]:
    assignments: Dict[str, Assignment] = {}
    for assignment in Assignment.objects.filter(
        school_id=school_id,
        section_id=section_id,
        is_published=True,
    ).select_related("category"):
        assignments[assignment.name] = assignment
    return assignments


def _build_category_data(categories: List[AssignmentCategory]) -> Dict[UUID, Dict[str, Decimal]]:
    return {
        cat.id: {
            "earned": Decimal("0"),
            "possible": Decimal("0"),
            "weight": Decimal(str(cat.weight_percent)),
        }
        for cat in categories
    }


def _add_entry_points(category_bucket: Dict[str, Decimal], entry: GradeEntry) -> None:
    if entry.points_earned is not None:
        category_bucket["earned"] += Decimal(str(entry.points_earned))
    if entry.points_possible is not None:
        category_bucket["possible"] += Decimal(str(entry.points_possible))


def _weighted_percent_from_category_data(category_data: Dict[UUID, Dict[str, Decimal]]) -> Optional[float]:
    categories_with_points = [
        cat_id for cat_id, data in category_data.items()
        if data["possible"] > 0
    ]
    if not categories_with_points:
        return None

    total_included_weight = sum(category_data[cat_id]["weight"] for cat_id in categories_with_points)
    if total_included_weight == 0:
        return None

    weighted_sum = Decimal("0")
    for cat_id in categories_with_points:
        data = category_data[cat_id]
        category_percent = data["earned"] / data["possible"]
        renorm_weight = data["weight"] / total_included_weight
        weighted_sum += category_percent * renorm_weight

    return round(float(weighted_sum * 100), 1)


def _compute_section_final_percent(
    school_id: str,
    section_id: UUID,
    student_id: UUID,
) -> Optional[float]:
    """
    Compute final percent for a section using weighted grading if configured.

    Logic:
    1. If section has AssignmentCategory rows:
       - Check sum of active weights
       - If sum = 100: use weighted grading
       - If sum = 0: fallback to unweighted
    2. If no categories: use simple GradeEntry sum (current MVP behavior)

    Weighted calculation:
    - For each active category with points_possible > 0:
      - category_percent = earned / possible
      - Renormalize weights across categories with points
      - weighted_contrib = category_percent * (renorm_weight)
    - Final = sum(weighted_contrib) * 100

    Returns:
        Final percent (0-100) or None if no gradable data
    """
    categories = _section_categories(school_id, section_id)

    if not categories:
        return _simple_section_percent(school_id, section_id, student_id)

    total_weight = sum(Decimal(str(cat.weight_percent)) for cat in categories)
    if total_weight in (Decimal("0"), Decimal("100")):
        if total_weight == Decimal("0"):
            return _simple_section_percent(school_id, section_id, student_id)
    else:
        return _simple_section_percent(school_id, section_id, student_id)

    assignments_by_name = _assignments_by_name(school_id, section_id)
    category_data = _build_category_data(categories)

    grade_entries = GradeEntry.objects.filter(
        school_id=school_id,
        section_id=section_id,
        student_id=student_id,
    )
    for entry in grade_entries:
        assignment = assignments_by_name.get(entry.assignment_name)
        if not assignment:
            continue
        category_bucket = category_data.get(assignment.category_id)
        if not category_bucket:
            continue
        _add_entry_points(category_bucket, entry)

    return _weighted_percent_from_category_data(category_data)


@dataclass(frozen=True)
class CourseRow:
    section_id: str
    course_code: str
    course_name: str
    teacher_name: str
    final_percent: Optional[float]
    final_letter: str
    credits: float



@dataclass(frozen=True)
class TranscriptMeta:
    provider: str
    dual_enrollment_label: str


def _transcript_meta_maps(school_id: str, student_id: UUID):
    entries = list(
        TranscriptEntry.objects.filter(school_id=school_id, student_id=student_id)
    )
    by_course_term: Dict[Tuple[str, str], TranscriptMeta] = {}
    by_course: Dict[str, TranscriptMeta] = {}

    for entry in entries:
        meta = TranscriptMeta(
            provider=(entry.provider or "").strip(),
            dual_enrollment_label=(entry.dual_enrollment_label or "").strip(),
        )
        course_key = str(entry.course_id)
        term_key = str(entry.term_id or "")
        by_course_term[(course_key, term_key)] = meta
        if course_key not in by_course:
            by_course[course_key] = meta

    return by_course_term, by_course


def _resolve_transcript_meta(section, by_course_term, by_course) -> TranscriptMeta:
    course_key = str(getattr(section, "course_id", "") or "")
    term_key = str(getattr(section, "term_ref_id", "") or "")

    return (
        by_course_term.get((course_key, term_key))
        or by_course_term.get((course_key, ""))
        or by_course.get(course_key)
        or TranscriptMeta(provider="", dual_enrollment_label="")
    )


def _load_student_for_school(school_id: str, student_id: UUID):
    try:
        return Student.objects.get(pk=student_id, school_id=school_id), None
    except Student.DoesNotExist:
        return None, JsonResponse({"detail": "Student not found."}, status=404)


def _transcript_ro_course_row(section, student_id: UUID, school_id: str, by_course_term, by_course):
    final_percent = _compute_section_final_percent(school_id, section.id, student_id)
    letter = _letter_from_percent(final_percent)
    meta = _resolve_transcript_meta(section, by_course_term, by_course)
    return {
        "section_id": str(section.id),
        "course_code": getattr(section.course, "code", ""),
        "course_name": getattr(section.course, "name", ""),
        "teacher_name": getattr(section, "teacher_name", "") or "",
        "final_percent": final_percent,
        "final_letter": letter,
        "credits": 1.0,
        "provider": meta.provider,
        "dual_enrollment_label": meta.dual_enrollment_label,
    }


def _transcript_ro_grouped_data(enrollments, school_id: str, student_id: UUID, by_course_term, by_course):
    terms: Dict[str, Dict[str, Any]] = {}
    courses_by_term: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for enrollment in enrollments:
        section = enrollment.section
        term_id = str(getattr(section, "term_ref_id", None) or "")
        term_code = getattr(section, "term", None) or "UNKNOWN"
        term_key = term_id if term_id else f"TERM::{term_code}"
        terms.setdefault(term_key, {"term_id": term_id or None, "term_code": term_code})
        courses_by_term[term_key].append(
            _transcript_ro_course_row(section, student_id, school_id, by_course_term, by_course)
        )

    return terms, courses_by_term


def _transcript_ro_term_blocks(terms, courses_by_term):
    term_blocks: List[Dict[str, Any]] = []
    all_points: List[float] = []

    for term_key, term_meta in sorted(terms.items(), key=lambda kv: (kv[1]["term_code"], kv[0])):
        course_rows = courses_by_term.get(term_key, [])
        course_rows.sort(key=lambda r: (r["course_code"], r["course_name"], r["section_id"]))

        pts = [_gpa_points(r["final_letter"]) for r in course_rows if r["final_letter"] != "N/A"]
        term_gpa = round(sum(pts) / len(pts), 2) if pts else None
        if pts:
            all_points.extend(pts)

        term_blocks.append({
            "term_id": term_meta["term_id"],
            "term_code": term_meta["term_code"],
            "courses": course_rows,
            "term_gpa_mvp": term_gpa,
        })

    cumulative = round(sum(all_points) / len(all_points), 2) if all_points else None
    return term_blocks, cumulative


def _ensure_contract_term_block(by_year, by_term, school_year: str, term_id: str, term_name: str, term_code: str):
    by_year.setdefault(school_year, {"school_year": school_year, "terms": []})
    term_key = (school_year, term_id or term_code)
    if term_key not in by_term:
        term_block = {
            "term_id": term_id or None,
            "term_name": term_name,
            "courses": [],
        }
        by_term[term_key] = term_block
        by_year[school_year]["terms"].append(term_block)
    return term_key


def _contract_course_row(section, student_id: UUID, school_id: str, by_course_term, by_course):
    final_percent = _compute_section_final_percent(school_id, section.id, student_id)
    final_letter = _letter_from_percent(final_percent)
    final_grade = None if final_letter == "N/A" else final_letter
    meta = _resolve_transcript_meta(section, by_course_term, by_course)
    return {
        "section_id": str(section.id),
        "course_code": getattr(section.course, "code", ""),
        "course_name": getattr(section.course, "name", ""),
        "credits": str(getattr(section.course, "credits", "1.00")),
        "teacher": getattr(section, "teacher_name", ""),
        "final_grade": final_grade,
        "status": "in_progress" if final_grade is None else "final",
        "provider": meta.provider,
        "dual_enrollment_label": meta.dual_enrollment_label,
    }


def _sorted_school_years(by_year):
    school_years = list(by_year.values())
    school_years.sort(key=lambda row: row["school_year"])
    for year in school_years:
        year["terms"].sort(key=lambda t: (t["term_name"], t["term_id"] or ""))
        for term in year["terms"]:
            term["courses"].sort(key=lambda c: (c["course_code"], c["course_name"], c["section_id"]))
    return school_years

class TranscriptROView(APIView):
    """
    Read-only transcript summary derived from:
      - Enrollments (what the student is taking)
      - GradeEntry (current demo-grade source of truth for term/course totals)

    MVP constraints:
      - GPA values are placeholders (simple letter->points average, unweighted).
      - Credits default to 1.0 unless you add a real credit model later.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, student_id: UUID):
        school_id = request.headers.get("X-School-Id")
        if not school_id:
            return JsonResponse({"detail": "Missing X-School-Id header."}, status=400)

        student, student_error = _load_student_for_school(school_id, student_id)
        if student_error:
            return student_error

        enrollments = (
            Enrollment.objects
            .filter(school_id=school_id, student_id=student_id)
            .select_related("section__course", "section__term_ref")
        )

        by_course_term, by_course = _transcript_meta_maps(school_id, student_id)
        terms, courses_by_term = _transcript_ro_grouped_data(
            enrollments,
            school_id,
            student_id,
            by_course_term,
            by_course,
        )
        term_blocks, cumulative = _transcript_ro_term_blocks(terms, courses_by_term)

        return JsonResponse({
            "student": {
                "student_id": str(student.id),
                "first_name": student.first_name,
                "last_name": student.last_name,
                "grade_level": getattr(student, "grade_level", None),
            },
            "terms": term_blocks,
            "cumulative_gpa_mvp": cumulative,
            "notes": [],
        }, status=200)

def _term_school_year(term) -> str:
    return (
        getattr(term, "school_year", "")
        or getattr(getattr(term, "academic_year", None), "name", "")
        or "UNKNOWN"
    )


def _term_display_name(term, fallback_code: str) -> str:
    return getattr(term, "name", "") or fallback_code or "UNKNOWN"


class StudentTranscriptContractView(APIView):
    """
    Read-only transcript contract (student-centric, buyer-facing shape).

    Shape:
      student_id, student_name, school_years -> terms -> courses
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, student_id: UUID):
        school_id = request.headers.get("X-School-Id")
        if not school_id:
            return JsonResponse({"detail": "Missing X-School-Id header."}, status=400)

        student, student_error = _load_student_for_school(school_id, student_id)
        if student_error:
            return student_error

        enrollments = (
            Enrollment.objects
            .filter(school_id=school_id, student_id=student_id)
            .select_related("section__course", "section__term_ref", "section__term_ref__academic_year")
        )
        by_course_term, by_course = _transcript_meta_maps(school_id, student_id)

        by_year: Dict[str, Dict[str, Any]] = {}
        by_term: Dict[Tuple[str, str], Dict[str, Any]] = {}

        for enrollment in enrollments:
            section = enrollment.section
            term_ref = section.term_ref
            term_code = getattr(section, "term", "") or "UNKNOWN"
            school_year = _term_school_year(term_ref)
            term_id = str(getattr(term_ref, "id", "") or "")
            term_name = _term_display_name(term_ref, term_code)

            term_key = _ensure_contract_term_block(
                by_year,
                by_term,
                school_year,
                term_id,
                term_name,
                term_code,
            )
            by_term[term_key]["courses"].append(
                _contract_course_row(section, student_id, school_id, by_course_term, by_course)
            )

        school_years = _sorted_school_years(by_year)

        return JsonResponse({
            "student_id": str(student.id),
            "student_name": f"{student.first_name} {student.last_name}".strip(),
            "school_years": school_years,
        }, status=200)

