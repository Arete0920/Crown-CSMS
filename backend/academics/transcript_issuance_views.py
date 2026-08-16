from __future__ import annotations

import base64
import hashlib
import io
import json
import uuid
from datetime import timezone as dt_timezone

from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from audit.models import AuditLog
from core.models import School, UserRole
from households.models import Student
from households.scoping import get_request_school_id

from .transcript_access_views import _can_disclose_transcript
from .transcript_service import build_transcript_snapshot


ISSUANCE_ACTION = "TRANSCRIPT_ISSUED"
ISSUANCE_MODEL = "academics.TranscriptIssuance"
ISSUER_ROLES = frozenset({"HEAD_OF_SCHOOL", "REGISTRAR"})
PDF_CONTENT_TYPE = "application/pdf"


def _role_codes(user, school_id) -> set[str]:
    if not user or not getattr(user, "is_authenticated", False):
        return set()
    return set(
        UserRole.objects.filter(user=user, school_id=school_id).values_list(
            "role_code", flat=True
        )
    )


def _can_issue(user, school_id) -> bool:
    if not user or not getattr(user, "is_authenticated", False) or not getattr(user, "is_active", False):
        return False
    if getattr(user, "is_superuser", False):
        return True
    return bool(_role_codes(user, school_id).intersection(ISSUER_ROLES))


def _student_for_school(school_id, student_id):
    return (
        Student.objects.filter(
            id=student_id,
            school_id=school_id,
            is_active=True,
            household__school_id=school_id,
            household__is_active=True,
        )
        .select_related("household", "account")
        .first()
    )


def _canonical_json(payload) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _render_pdf(*, school_name: str, snapshot: dict, issuance_id: str, issued_at: str, source_digest: str) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.55 * inch,
        leftMargin=0.55 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch,
        title="Official Academic Transcript",
        author=school_name,
    )
    styles = getSampleStyleSheet()
    story = [
        Paragraph(school_name, styles["Title"]),
        Paragraph("Official Academic Transcript", styles["Heading2"]),
        Spacer(1, 8),
    ]

    student = snapshot["student"]
    student_name = f"{student['first_name']} {student['last_name']}".strip()
    meta = [
        ["Student", student_name, "Grade Level", student.get("grade_level") or "-"],
        ["Student ID", student["student_id"], "Issued", issued_at],
        ["Issuance ID", issuance_id, "Cumulative GPA", snapshot.get("cumulative_gpa") or "-"],
        ["Earned Credits", snapshot.get("earned_credits") or "0.00", "Attempted Credits", snapshot.get("attempted_credits") or "0.00"],
    ]
    meta_table = Table(meta, colWidths=[0.9 * inch, 2.35 * inch, 1.05 * inch, 2.2 * inch])
    meta_table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.extend([meta_table, Spacer(1, 12)])

    for term in snapshot.get("terms", []):
        heading = term.get("term_name") or term.get("term_code") or "Term"
        gpa = term.get("term_gpa") or "-"
        story.append(Paragraph(f"{heading} &nbsp;&nbsp; GPA: {gpa}", styles["Heading3"]))
        rows = [["Course", "Title", "Grade", "Credits", "Earned", "Status", "Provider"]]
        for course in term.get("courses", []):
            rows.append(
                [
                    course.get("course_code") or "",
                    course.get("course_name") or "",
                    course.get("final_letter") or "-",
                    course.get("credits") or "0.00",
                    course.get("earned_credits") or "0.00",
                    "Final" if course.get("record_status") == "final" else "In Progress",
                    course.get("provider") or course.get("dual_enrollment_label") or "",
                ]
            )
        table = Table(
            rows,
            repeatRows=1,
            colWidths=[0.75 * inch, 1.75 * inch, 0.5 * inch, 0.55 * inch, 0.55 * inch, 0.75 * inch, 1.25 * inch],
        )
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E9EDF2")),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 7.5),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#B8C1CC")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 3),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                    ("TOPPADDING", (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ]
            )
        )
        story.extend([table, Spacer(1, 10)])

    story.extend(
        [
            Spacer(1, 6),
            Paragraph(
                "Verification: this artifact was generated from the immutable issuance snapshot recorded by CROWN. "
                f"Source SHA-256: {source_digest}",
                styles["Normal"],
            ),
        ]
    )
    doc.build(story)
    return buffer.getvalue()


def _issuance_log(issuance_id):
    return AuditLog.objects.filter(
        id=issuance_id,
        action=ISSUANCE_ACTION,
        model=ISSUANCE_MODEL,
    ).first()


def _safe_metadata(log: AuditLog) -> dict:
    metadata = dict(log.metadata or {})
    metadata.pop("artifact_b64", None)
    return metadata


class TranscriptIssuanceCollectionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, student_id):
        school_id = get_request_school_id(request, required=True)
        student = _student_for_school(school_id, student_id)
        if student is None:
            return JsonResponse({"detail": "Student not found."}, status=404)
        if not _can_issue(request.user, school_id):
            return JsonResponse({"detail": "Transcript issuance permission denied."}, status=403)

        snapshot = build_transcript_snapshot(school_id=school_id, student=student)
        if not snapshot.get("terms"):
            return JsonResponse({"detail": "Transcript has no academic records to issue."}, status=400)

        source_bytes = _canonical_json(snapshot)
        source_digest = _sha256(source_bytes)
        issuance_id = uuid.uuid4()
        issued_at_dt = timezone.now().astimezone(dt_timezone.utc)
        issued_at = issued_at_dt.isoformat().replace("+00:00", "Z")
        school = School.objects.filter(pk=school_id).first()
        school_name = getattr(school, "name", "") or "CROWN School"
        filename = f"official-transcript-{student.id}-{issuance_id}.pdf"
        pdf_bytes = _render_pdf(
            school_name=school_name,
            snapshot=snapshot,
            issuance_id=str(issuance_id),
            issued_at=issued_at,
            source_digest=source_digest,
        )
        artifact_digest = _sha256(pdf_bytes)

        AuditLog.objects.create(
            id=issuance_id,
            user_id=request.user.id,
            action=ISSUANCE_ACTION,
            model=ISSUANCE_MODEL,
            object_id=str(student.id),
            metadata={
                "school_id": str(school_id),
                "student_id": str(student.id),
                "issued_at": issued_at,
                "issued_by_user_id": str(request.user.id),
                "issued_by_email": getattr(request.user, "email", "") or "",
                "source_sha256": source_digest,
                "artifact_sha256": artifact_digest,
                "artifact_content_type": PDF_CONTENT_TYPE,
                "artifact_filename": filename,
                "artifact_b64": base64.b64encode(pdf_bytes).decode("ascii"),
                "snapshot": snapshot,
            },
        )

        return JsonResponse(
            {
                "issuance_id": str(issuance_id),
                "student_id": str(student.id),
                "issued_at": issued_at,
                "source_sha256": source_digest,
                "artifact_sha256": artifact_digest,
                "download_url": f"/api/v1/academics/transcript-issuances/{issuance_id}/pdf/",
            },
            status=201,
        )


class TranscriptIssuanceDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, issuance_id):
        school_id = get_request_school_id(request, required=True)
        log = _issuance_log(issuance_id)
        if log is None:
            return JsonResponse({"detail": "Transcript issuance not found."}, status=404)
        metadata = log.metadata or {}
        if str(metadata.get("school_id")) != str(school_id):
            return JsonResponse({"detail": "Transcript issuance not found."}, status=404)
        student = _student_for_school(school_id, metadata.get("student_id"))
        if student is None or not _can_disclose_transcript(request, student, school_id):
            return JsonResponse({"detail": "Transcript issuance not found."}, status=404)
        return JsonResponse({"issuance_id": str(log.id), **_safe_metadata(log)}, status=200)


class TranscriptIssuancePdfView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, issuance_id):
        school_id = get_request_school_id(request, required=True)
        log = _issuance_log(issuance_id)
        if log is None:
            return JsonResponse({"detail": "Transcript issuance not found."}, status=404)
        metadata = log.metadata or {}
        if str(metadata.get("school_id")) != str(school_id):
            return JsonResponse({"detail": "Transcript issuance not found."}, status=404)
        student = _student_for_school(school_id, metadata.get("student_id"))
        if student is None or not _can_disclose_transcript(request, student, school_id):
            return JsonResponse({"detail": "Transcript issuance not found."}, status=404)

        try:
            artifact = base64.b64decode(metadata.get("artifact_b64") or "", validate=True)
        except (ValueError, TypeError):
            return JsonResponse({"detail": "Transcript artifact integrity verification failed."}, status=409)
        if not artifact or _sha256(artifact) != metadata.get("artifact_sha256"):
            return JsonResponse({"detail": "Transcript artifact integrity verification failed."}, status=409)

        response = HttpResponse(artifact, content_type=PDF_CONTENT_TYPE)
        response["Content-Disposition"] = f'attachment; filename="{metadata.get("artifact_filename") or "official-transcript.pdf"}"'
        response["X-CROWN-Transcript-Issuance"] = str(log.id)
        response["X-CROWN-Artifact-SHA256"] = metadata.get("artifact_sha256") or ""
        return response
