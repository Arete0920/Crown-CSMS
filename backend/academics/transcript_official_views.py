from __future__ import annotations

import hashlib
import io
import json
from collections import defaultdict
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any
from uuid import UUID, uuid4

from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from reportlab.lib.pagesizes import LETTER
from reportlab.pdfgen import canvas
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from core.models import School, UserRole
from core.permissions import user_has_permission
from crown_api.audit_models import AuditEvent
from households.models import Student
from households.scoping import get_request_school_id

from .models import Enrollment, TranscriptEntry
from .transcript_views import _compute_section_final_percent, _letter_from_percent


TRANSCRIPT_ISSUE_PERMISSION = "transcript.issue"
ISSUANCE_ACTION = "transcript.issued"
ISSUANCE_SCHEMA = "crown.official-transcript.v1"
GPA_LETTERS = frozenset({"A", "B", "C", "D", "F"})
EARNED_CREDIT_GRADES = frozenset({"A", "B", "C", "D", "P"})
ATTEMPTED_CREDIT_GRADES = frozenset({"A", "B", "C", "D", "F", "P"})


def _decimal_string(value: Decimal | str | int | float | None) -> str:
    if value is None:
        value = Decimal("0")
    return str(Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _gpa_string(numerator: Decimal, denominator: Decimal) -> str | None:
    if denominator <= 0:
        return None
    return str((numerator / denominator).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _entry_maps(school_id, student_id):
    exact: dict[tuple[str, str], TranscriptEntry] = {}
    course_only: dict[str, TranscriptEntry] = {}
    entries = TranscriptEntry.objects.filter(
        school_id=school_id,
        student_id=student_id,
    ).select_related("course", "term")
    for entry in entries:
        course_key = str(entry.course_id)
        term_key = str(entry.term_id or "")
        exact[(course_key, term_key)] = entry
        if entry.term_id is None:
            course_only[course_key] = entry
    return exact, course_only


def _entry_for_section(section, exact, course_only):
    course_key = str(section.course_id)
    term_key = str(getattr(section, "term_ref_id", "") or "")
    return exact.get((course_key, term_key)) or course_only.get(course_key)


def _term_school_year(section) -> str:
    term = getattr(section, "term_ref", None)
    return (
        getattr(term, "school_year", "")
        or getattr(getattr(term, "academic_year", None), "name", "")
        or "UNKNOWN"
    )


def _term_name(section) -> str:
    term = getattr(section, "term_ref", None)
    return getattr(term, "name", "") or getattr(section, "term", "") or "UNKNOWN"


def _course_row(section, student_id, school_id, exact, course_only) -> dict[str, Any]:
    entry = _entry_for_section(section, exact, course_only)
    recorded_grade = (entry.final_letter_grade or "").strip().upper() if entry else ""

    if entry is not None and recorded_grade:
        credits = Decimal(str(entry.credit_value or 0))
        gpa_points = Decimal(str(entry.gpa_points or 0))
        attempted = credits if recorded_grade in ATTEMPTED_CREDIT_GRADES else Decimal("0")
        earned = credits if recorded_grade in EARNED_CREDIT_GRADES else Decimal("0")
        gpa_credits = credits if recorded_grade in GPA_LETTERS else Decimal("0")
        return {
            "section_id": str(section.id),
            "course_code": section.course.code,
            "course_name": section.course.name,
            "teacher_name": getattr(section, "teacher_name", "") or "",
            "final_percent": float(entry.final_percentage) if entry.final_percentage is not None else None,
            "final_letter": recorded_grade,
            "credits": _decimal_string(credits),
            "attempted_credits": _decimal_string(attempted),
            "earned_credits": _decimal_string(earned),
            "gpa_points": _decimal_string(gpa_points) if gpa_credits > 0 else None,
            "gpa_included": gpa_credits > 0,
            "status": "recorded",
            "grade_source": "transcript_entry",
            "credit_source": "transcript_entry",
            "provider": (entry.provider or "").strip(),
            "dual_enrollment_label": (entry.dual_enrollment_label or "").strip(),
            "_gpa_numerator": gpa_points * gpa_credits,
            "_gpa_denominator": gpa_credits,
        }

    final_percent = _compute_section_final_percent(school_id, section.id, student_id)
    preview_letter = _letter_from_percent(final_percent)
    preview_letter = None if preview_letter == "N/A" else preview_letter
    return {
        "section_id": str(section.id),
        "course_code": section.course.code,
        "course_name": section.course.name,
        "teacher_name": getattr(section, "teacher_name", "") or "",
        "final_percent": final_percent,
        "final_letter": preview_letter,
        "credits": _decimal_string(section.course.credits),
        "attempted_credits": "0.00",
        "earned_credits": "0.00",
        "gpa_points": None,
        "gpa_included": False,
        "status": "in_progress",
        "grade_source": "gradebook_preview",
        "credit_source": "course_preview",
        "provider": "",
        "dual_enrollment_label": "",
        "_gpa_numerator": Decimal("0"),
        "_gpa_denominator": Decimal("0"),
    }


def build_authoritative_transcript(*, school_id, student: Student) -> dict[str, Any]:
    enrollments = (
        Enrollment.objects.filter(school_id=school_id, student=student)
        .select_related("section__course", "section__term_ref", "section__term_ref__academic_year")
        .order_by("section__term", "section__course__code", "section_id")
    )
    exact, course_only = _entry_maps(school_id, student.id)

    term_rows: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    term_meta: dict[tuple[str, str], dict[str, str]] = {}
    for enrollment in enrollments:
        section = enrollment.section
        year = _term_school_year(section)
        term_id = str(getattr(section, "term_ref_id", "") or "")
        term_key = (year, term_id or getattr(section, "term", "") or "UNKNOWN")
        term_meta[term_key] = {
            "school_year": year,
            "term_id": term_id,
            "term_name": _term_name(section),
        }
        term_rows[term_key].append(
            _course_row(section, student.id, school_id, exact, course_only)
        )

    terms = []
    cumulative_num = Decimal("0")
    cumulative_den = Decimal("0")
    total_attempted = Decimal("0")
    total_earned = Decimal("0")

    for term_key in sorted(term_rows, key=lambda key: (key[0], term_meta[key]["term_name"], key[1])):
        rows = term_rows[term_key]
        term_num = sum((row.pop("_gpa_numerator") for row in rows), Decimal("0"))
        term_den = sum((row.pop("_gpa_denominator") for row in rows), Decimal("0"))
        attempted = sum((Decimal(row["attempted_credits"]) for row in rows), Decimal("0"))
        earned = sum((Decimal(row["earned_credits"]) for row in rows), Decimal("0"))
        cumulative_num += term_num
        cumulative_den += term_den
        total_attempted += attempted
        total_earned += earned
        meta = term_meta[term_key]
        terms.append(
            {
                "school_year": meta["school_year"],
                "term_id": meta["term_id"] or None,
                "term_name": meta["term_name"],
                "term_gpa": _gpa_string(term_num, term_den),
                "attempted_credits": _decimal_string(attempted),
                "earned_credits": _decimal_string(earned),
                "courses": rows,
            }
        )

    return {
        "schema": ISSUANCE_SCHEMA,
        "student": {
            "student_id": str(student.id),
            "first_name": student.first_name,
            "last_name": student.last_name,
            "grade_level": getattr(student, "grade_level", None),
        },
        "terms": terms,
        "cumulative_gpa": _gpa_string(cumulative_num, cumulative_den),
        "attempted_credits": _decimal_string(total_attempted),
        "earned_credits": _decimal_string(total_earned),
        "calculation_policy": {
            "gpa_method": "credit_weighted_transcript_entry_points",
            "gpa_grades": sorted(GPA_LETTERS),
            "earned_credit_grades": sorted(EARNED_CREDIT_GRADES),
            "attempted_credit_grades": sorted(ATTEMPTED_CREDIT_GRADES),
            "in_progress_in_official_gpa": False,
            "weighting_source": "TranscriptEntry.gpa_points; no label-based inference",
        },
    }


def _contract_payload(snapshot: dict[str, Any]) -> dict[str, Any]:
    by_year: dict[str, dict[str, Any]] = {}
    for term in snapshot["terms"]:
        year = term["school_year"]
        block = by_year.setdefault(year, {"school_year": year, "terms": []})
        block["terms"].append(
            {
                "term_id": term["term_id"],
                "term_name": term["term_name"],
                "term_gpa": term["term_gpa"],
                "attempted_credits": term["attempted_credits"],
                "earned_credits": term["earned_credits"],
                "courses": [
                    {
                        "section_id": row["section_id"],
                        "course_code": row["course_code"],
                        "course_name": row["course_name"],
                        "credits": row["credits"],
                        "teacher": row["teacher_name"],
                        "final_grade": row["final_letter"],
                        "final_percent": row["final_percent"],
                        "gpa_points": row["gpa_points"],
                        "status": row["status"],
                        "provider": row["provider"],
                        "dual_enrollment_label": row["dual_enrollment_label"],
                    }
                    for row in term["courses"]
                ],
            }
        )
    return {
        "student_id": snapshot["student"]["student_id"],
        "student_name": f"{snapshot['student']['first_name']} {snapshot['student']['last_name']}".strip(),
        "school_years": [by_year[key] for key in sorted(by_year)],
        "cumulative_gpa": snapshot["cumulative_gpa"],
        "attempted_credits": snapshot["attempted_credits"],
        "earned_credits": snapshot["earned_credits"],
        "calculation_policy": snapshot["calculation_policy"],
    }


def _student_for_school(school_id, student_id):
    return Student.objects.filter(
        id=student_id,
        school_id=school_id,
        is_active=True,
        household__school_id=school_id,
        household__is_active=True,
    ).first()


def _canonical_json(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _render_pdf(snapshot: dict[str, Any], *, issuance_id: UUID, issued_at: datetime) -> bytes:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=LETTER, invariant=1, pageCompression=0)
    width, height = LETTER
    y = height - 54

    def line(text: str, *, size: int = 9, gap: int = 14):
        nonlocal y
        if y < 54:
            pdf.showPage()
            y = height - 54
        pdf.setFont("Helvetica", size)
        pdf.drawString(54, y, text[:110])
        y -= gap

    student = snapshot["student"]
    pdf.setTitle(f"Official Transcript - {student['first_name']} {student['last_name']}")
    line("CROWN — Official Student Transcript", size=14, gap=20)
    line(f"Student: {student['first_name']} {student['last_name']}  ID: {student['student_id']}")
    line(f"Issued: {issued_at.isoformat()}  Issuance ID: {issuance_id}")
    line(f"Cumulative GPA: {snapshot['cumulative_gpa'] or 'N/A'}  Earned credits: {snapshot['earned_credits']}")
    y -= 6

    for term in snapshot["terms"]:
        line(f"{term['school_year']} — {term['term_name']} — GPA {term['term_gpa'] or 'N/A'}", size=11, gap=17)
        for row in term["courses"]:
            provider = f" | {row['provider']}" if row["provider"] else ""
            dual = f" | {row['dual_enrollment_label']}" if row["dual_enrollment_label"] else ""
            line(
                f"{row['course_code']} {row['course_name']} | {row['final_letter'] or 'In Progress'} | "
                f"credits {row['credits']} | {row['status']}{provider}{dual}"
            )
        y -= 4

    source_hash = hashlib.sha256(_canonical_json(snapshot)).hexdigest()
    y -= 8
    line(f"Source SHA-256: {source_hash}", size=8, gap=11)
    line(f"Schema: {ISSUANCE_SCHEMA}", size=8, gap=11)
    pdf.save()
    return buffer.getvalue()


def _school_and_permission(request, school_id):
    school = School.objects.filter(id=school_id).first()
    if school is None:
        return None, JsonResponse({"detail": "School not found."}, status=404)
    if not user_has_permission(request.user, TRANSCRIPT_ISSUE_PERMISSION, school=school):
        return None, JsonResponse({"detail": "Transcript issuance permission denied."}, status=403)
    return school, None


def _actor_role(user, school_id) -> str:
    return (
        UserRole.objects.filter(user=user, school_id=school_id)
        .order_by("role_code")
        .values_list("role_code", flat=True)
        .first()
        or ""
    )


class TranscriptROView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, student_id: UUID):
        school_id = get_request_school_id(request, required=True)
        student = _student_for_school(school_id, student_id)
        if student is None:
            return JsonResponse({"detail": "Student not found."}, status=404)
        return JsonResponse(build_authoritative_transcript(school_id=school_id, student=student), status=200)


class StudentTranscriptContractView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, student_id: UUID):
        school_id = get_request_school_id(request, required=True)
        student = _student_for_school(school_id, student_id)
        if student is None:
            return JsonResponse({"detail": "Student not found."}, status=404)
        snapshot = build_authoritative_transcript(school_id=school_id, student=student)
        return JsonResponse(_contract_payload(snapshot), status=200)


class OfficialTranscriptIssueView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, student_id: UUID):
        school_id = get_request_school_id(request, required=True)
        _, permission_error = _school_and_permission(request, school_id)
        if permission_error:
            return permission_error

        student = _student_for_school(school_id, student_id)
        if student is None:
            return JsonResponse({"detail": "Student not found."}, status=404)

        snapshot = build_authoritative_transcript(school_id=school_id, student=student)
        if not any(row["status"] == "recorded" for term in snapshot["terms"] for row in term["courses"]):
            return JsonResponse(
                {"detail": "Official transcript requires at least one recorded TranscriptEntry."},
                status=409,
            )

        issuance_id = uuid4()
        issued_at = timezone.now()
        source_hash = hashlib.sha256(_canonical_json(snapshot)).hexdigest()
        pdf_bytes = _render_pdf(snapshot, issuance_id=issuance_id, issued_at=issued_at)
        document_hash = hashlib.sha256(pdf_bytes).hexdigest()
        filename = f"official-transcript-{student.id}-{issuance_id}.pdf"

        event = AuditEvent.objects.create(
            id=issuance_id,
            ts=issued_at,
            school_id=school_id,
            actor_id=request.user.id,
            actor_role=_actor_role(request.user, school_id),
            action=ISSUANCE_ACTION,
            object_type="households.Student",
            object_id=student.id,
            meta={
                "schema": ISSUANCE_SCHEMA,
                "snapshot": snapshot,
                "source_sha256": source_hash,
                "document_sha256": document_hash,
                "filename": filename,
            },
        )
        return JsonResponse(
            {
                "issuance_id": str(event.id),
                "issued_at": event.ts.isoformat(),
                "student_id": str(student.id),
                "source_sha256": source_hash,
                "document_sha256": document_hash,
                "filename": filename,
            },
            status=201,
        )


class OfficialTranscriptDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, issuance_id: UUID):
        school_id = get_request_school_id(request, required=True)
        _, permission_error = _school_and_permission(request, school_id)
        if permission_error:
            return permission_error

        event = AuditEvent.objects.filter(
            id=issuance_id,
            school_id=school_id,
            action=ISSUANCE_ACTION,
        ).first()
        if event is None:
            return JsonResponse({"detail": "Transcript issuance not found."}, status=404)

        snapshot = event.meta.get("snapshot") or {}
        source_hash = hashlib.sha256(_canonical_json(snapshot)).hexdigest()
        if source_hash != event.meta.get("source_sha256"):
            return JsonResponse({"detail": "Transcript issuance source integrity check failed."}, status=409)

        pdf_bytes = _render_pdf(snapshot, issuance_id=event.id, issued_at=event.ts)
        document_hash = hashlib.sha256(pdf_bytes).hexdigest()
        if document_hash != event.meta.get("document_sha256"):
            return JsonResponse({"detail": "Transcript issuance document integrity check failed."}, status=409)

        response = HttpResponse(pdf_bytes, content_type="application/pdf")
        filename = event.meta.get("filename") or f"official-transcript-{event.id}.pdf"
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        response["X-Transcript-Source-SHA256"] = source_hash
        response["X-Transcript-Document-SHA256"] = document_hash
        return response
