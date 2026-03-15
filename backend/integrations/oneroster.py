"""
OneRoster 1.2 CSV export endpoint.

Produces a minimal bundle of OneRoster-compliant CSV files:
  - orgs.csv
  - academicSessions.csv
  - courses.csv
  - classes.csv  (sections mapped to OneRoster "class")
  - users.csv
  - enrollments.csv

References: 1EdTech OneRoster v1.2 CSV spec.
Crown stance: metadata-only export; no copyrighted content.

Endpoint:
    GET /api/integrations/oneroster/export/

Access: staff/admin only. Requires X-School-Id header.
"""
from __future__ import annotations

import csv
from io import StringIO
from datetime import UTC, datetime

from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError

from households.scoping import get_request_school_id
from core.models import School

# Import lightweight – academic models via relative import
from academics.models import Course, Section, Enrollment, Term


def _require_staff(user) -> bool:
    return bool(
        getattr(user, "is_authenticated", False)
        and (getattr(user, "is_staff", False) or getattr(user, "is_superuser", False))
    )


def _csv_string(header: list, rows: list[list]) -> str:
    buf = StringIO()
    w = csv.writer(buf)
    w.writerow(header)
    for row in rows:
        w.writerow(row)
    return buf.getvalue()


def _safe(val) -> str:
    """Convert any value to a safe CSV string (no None/UUID issues)."""
    if val is None:
        return ""
    return str(val)


# ---------------------------------------------------------------------------
# OneRoster file builders – each returns (filename, csv_string)
# ---------------------------------------------------------------------------

def _build_orgs(school: School) -> tuple[str, str]:
    header = [
        "sourcedId", "status", "dateLastModified",
        "type", "identifier", "name",
        "address", "city", "state", "zip", "country",
        "phone", "isoCountryCode",
        "parentSourcedId",
    ]
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows = [[
        _safe(school.id),          # sourcedId
        "active",                   # status
        now,                        # dateLastModified
        "school",                   # type
        _safe(school.id),          # identifier
        _safe(school.name) if hasattr(school, "name") else _safe(school.id),  # name
        "", "", "", "", "",          # address fields (optional)
        "",                         # phone
        "US",                       # isoCountryCode
        "",                         # parentSourcedId
    ]]
    return "orgs.csv", _csv_string(header, rows)


def _build_academic_sessions(school_id, terms) -> tuple[str, str]:
    header = [
        "sourcedId", "status", "dateLastModified",
        "title", "type", "startDate", "endDate",
        "schoolYear", "parentSourcedId",
    ]
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows = []
    for t in terms:
        rows.append([
            _safe(t.id),            # sourcedId
            "active",               # status
            now,
            _safe(t.name),          # title
            "term",                 # type
            _safe(t.start_date) if t.start_date else "",
            _safe(t.end_date) if t.end_date else "",
            _safe(t.school_year) if hasattr(t, "school_year") else "",
            "",                     # parentSourcedId
        ])
    return "academicSessions.csv", _csv_string(header, rows)


def _build_courses(school_id, courses) -> tuple[str, str]:
    header = [
        "sourcedId", "status", "dateLastModified",
        "schoolYearSourcedId", "title",
        "courseCode", "grades",
        "orgSourcedId", "subjects",
    ]
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows = []
    for c in courses:
        rows.append([
            _safe(c.id),                                    # sourcedId
            "active",
            now,
            "",                                             # schoolYearSourcedId
            _safe(c.name),                                  # title
            _safe(c.code),                                  # courseCode
            _safe(c.grade_band) if hasattr(c, "grade_band") else "",
            _safe(school_id),                               # orgSourcedId
            _safe(c.department) if hasattr(c, "department") else "",
        ])
    return "courses.csv", _csv_string(header, rows)


def _build_classes(school_id, sections) -> tuple[str, str]:
    header = [
        "sourcedId", "status", "dateLastModified",
        "title", "grades",
        "courseSourcedId", "classCode",
        "classType",
        "termSourcedIds", "orgSourcedId",
    ]
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows = []
    for s in sections:
        rows.append([
            _safe(s.id),
            "active",
            now,
            f"{s.course.code} - {s.term}",                 # title
            "",                                             # grades
            _safe(s.course_id),                             # courseSourcedId
            f"{s.course.code}-{s.term}",                    # classCode
            "scheduled",                                    # classType
            "",                                             # termSourcedIds
            _safe(school_id),                               # orgSourcedId
        ])
    return "classes.csv", _csv_string(header, rows)


def _build_enrollments(school_id, enrollments) -> tuple[str, str]:
    header = [
        "sourcedId", "status", "dateLastModified",
        "classSourcedId", "schoolSourcedId",
        "userSourcedId", "role",
        "primary", "beginDate", "endDate",
    ]
    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows = []
    for e in enrollments:
        rows.append([
            _safe(e.id),
            "active",
            now,
            _safe(e.section_id),                            # classSourcedId
            _safe(school_id),                               # schoolSourcedId
            _safe(e.student_id),                            # userSourcedId
            "student",                                      # role
            "true",                                         # primary
            "",                                             # beginDate
            "",                                             # endDate
        ])
    return "enrollments.csv", _csv_string(header, rows)


# ---------------------------------------------------------------------------
# Export endpoint
# ---------------------------------------------------------------------------

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def oneroster_export_bundle(request):
    """
    Export a minimal OneRoster 1.2 CSV bundle for the requesting school.
    Returns a multipart/mixed response containing each CSV file.

    Only school staff/admins may export roster data.
    """
    if not _require_staff(request.user):
        from rest_framework.response import Response
        from rest_framework import status
        return Response({"detail": "Staff access required to export OneRoster data."}, status=status.HTTP_403_FORBIDDEN)

    school_id = get_request_school_id(request)

    try:
        school = School.objects.get(pk=school_id)
    except School.DoesNotExist:
        raise ValidationError({"detail": "School not found."})

    # Fetch data – tenant-scoped throughout
    terms = Term.objects.filter(school_id=school_id).order_by("code")
    courses = Course.objects.filter(school_id=school_id).order_by("code")
    sections = (
        Section.objects.filter(school_id=school_id)
        .select_related("course")
        .order_by("course__code", "term")
    )
    enrollments = (
        Enrollment.objects.filter(school_id=school_id)
        .select_related("section", "student")
        .order_by("section_id")
    )

    # Build files
    files = [
        _build_orgs(school),
        _build_academic_sessions(school_id, terms),
        _build_courses(school_id, courses),
        _build_classes(school_id, sections),
        _build_enrollments(school_id, enrollments),
    ]

    # Wrap in multipart/mixed (simple deterministic format; clients can split on boundary)
    boundary = "CROWN_ONEROSTER_" + datetime.now(UTC).strftime("%Y%m%d%H%M%S")
    resp = HttpResponse(content_type=f"multipart/mixed; boundary={boundary}")
    resp["Content-Disposition"] = 'attachment; filename="oneroster_export.zip"'

    for filename, content in files:
        resp.write(f"--{boundary}\r\n".encode())
        resp.write(
            f'Content-Type: text/csv; charset=utf-8\r\n'
            f'Content-Disposition: attachment; filename="{filename}"\r\n\r\n'.encode()
        )
        resp.write(content.encode("utf-8"))
        resp.write(b"\r\n")

    resp.write(f"--{boundary}--\r\n".encode())
    return resp
