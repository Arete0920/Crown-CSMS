"""Microsoft School Data Sync (SDS) v2.1 CSV export.

This is intentionally separate from the legacy OneRoster 1.2 exporter. The first
Microsoft integration release exports the five-file SDS v2.1 class-roster set
for one CROWN school and one explicitly selected academic term:

- orgs.csv
- users.csv
- roles.csv
- classes.csv
- enrollments.csv

CROWN remains authoritative for school, section, roster, and teacher-assignment
truth. This endpoint only exports existing records; it never provisions or
mutates Microsoft 365.
"""
from __future__ import annotations

import csv
import uuid
import zipfile
from io import BytesIO, StringIO

from django.http import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

from academics.models import Enrollment, Section, TeacherAssignment, Term
from core.models import School
from core.permissions import CrownModulePermission
from households.scoping import get_request_school_id

SDS_FILENAMES = (
    "orgs.csv",
    "users.csv",
    "roles.csv",
    "classes.csv",
    "enrollments.csv",
)


def _clean(value) -> str:
    """Return an SDS-safe scalar without embedded CR/LF characters."""
    if value is None:
        return ""
    return str(value).replace("\r", " ").replace("\n", " ").strip()


def _csv_text(headers: tuple[str, ...], rows: list[tuple]) -> str:
    buffer = StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\r\n")
    writer.writerow(headers)
    for row in rows:
        writer.writerow([_clean(value) for value in row])
    return buffer.getvalue()


def _org_id(school_id) -> str:
    return f"school:{school_id}"


def _student_user_id(student_id) -> str:
    return f"student:{student_id}"


def _staff_user_id(staff_id) -> str:
    return f"staff:{staff_id}"


def _class_id(section_id) -> str:
    return f"section:{section_id}"


def _identity_username(record, *, kind: str) -> str:
    if kind == "student":
        account = getattr(record, "account", None)
        username = _clean(getattr(account, "email", "")) or _clean(
            getattr(account, "username", "")
        )
    else:
        username = _clean(getattr(record, "email", ""))

    # CROWN's first SDS profile matches source Username to Entra UserPrincipalName.
    # Requiring a domain prevents an accidental local username from silently
    # matching the wrong cloud identity.
    if not username or "@" not in username:
        raise ValidationError(
            {
                "detail": (
                    f"Microsoft SDS export blocked: {kind} {record.id} has no "
                    "domain-qualified username/email for Entra matching."
                ),
                "code": "sds_identity_missing",
            }
        )
    return username.lower()


def _build_sds_files(*, school, sections, student_enrollments, teacher_assignments):
    org = _org_id(school.id)

    student_by_id = {}
    for enrollment in student_enrollments:
        student_by_id[enrollment.student_id] = enrollment.student

    staff_by_id = {}
    for assignment in teacher_assignments:
        staff_by_id[assignment.staff_id] = assignment.staff

    users_rows = []
    roles_rows = []
    usernames = {}

    def register_username(username: str, sourced_id: str) -> None:
        existing = usernames.get(username)
        if existing and existing != sourced_id:
            raise ValidationError(
                {
                    "detail": (
                        f"Microsoft SDS export blocked: username {username} maps "
                        "to more than one CROWN identity."
                    ),
                    "code": "sds_identity_ambiguous",
                }
            )
        usernames[username] = sourced_id

    for student_id in sorted(student_by_id, key=str):
        student = student_by_id[student_id]
        username = _identity_username(student, kind="student")
        sourced_id = _student_user_id(student.id)
        register_username(username, sourced_id)
        users_rows.append(
            (
                sourced_id,
                username,
                student.last_name,
                student.first_name,
                username,
                str(student.id),
            )
        )
        roles_rows.append((sourced_id, org, "student", "true"))

    for staff_id in sorted(staff_by_id, key=str):
        staff = staff_by_id[staff_id]
        username = _identity_username(staff, kind="staff")
        sourced_id = _staff_user_id(staff.id)
        register_username(username, sourced_id)
        users_rows.append(
            (
                sourced_id,
                username,
                staff.last_name,
                staff.first_name,
                username,
                str(staff.id),
            )
        )
        roles_rows.append((sourced_id, org, "teacher", "true"))

    classes_rows = []
    for section in sections:
        title = f"{section.course.code} - {section.course.name}"
        classes_rows.append(
            (
                _class_id(section.id),
                org,
                title,
                f"{section.course.code}-{section.term}",
            )
        )

    enrollments_rows = []
    for enrollment in student_enrollments:
        enrollments_rows.append(
            (
                _class_id(enrollment.section_id),
                _student_user_id(enrollment.student_id),
                "student",
            )
        )
    for assignment in teacher_assignments:
        enrollments_rows.append(
            (
                _class_id(assignment.section_id),
                _staff_user_id(assignment.staff_id),
                "teacher",
            )
        )

    files = {
        "orgs.csv": _csv_text(
            ("sourcedId", "name", "type", "parentSourcedId"),
            [(org, school.name, "school", "")],
        ),
        "users.csv": _csv_text(
            (
                "sourcedId",
                "username",
                "familyName",
                "givenName",
                "email",
                "userNumber",
            ),
            users_rows,
        ),
        "roles.csv": _csv_text(
            ("userSourcedId", "orgSourcedId", "role", "isPrimary"),
            roles_rows,
        ),
        "classes.csv": _csv_text(
            ("sourcedId", "orgSourcedId", "title", "code"),
            classes_rows,
        ),
        "enrollments.csv": _csv_text(
            ("classSourcedId", "userSourcedId", "role"),
            enrollments_rows,
        ),
    }
    return files


def _zip_sds_files(files: dict[str, str]) -> bytes:
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for filename in SDS_FILENAMES:
            info = zipfile.ZipInfo(filename, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o600 << 16
            archive.writestr(info, files[filename].encode("utf-8"))
    return buffer.getvalue()


@api_view(["GET"])
@permission_classes([IsAuthenticated, CrownModulePermission("rosters.edit")])
def sds_v21_export(request):
    """Export one school's one-term roster as the SDS v2.1 five-file ZIP set."""
    school_id = get_request_school_id(request, required=True)
    school = School.objects.filter(pk=school_id, is_active=True).first()
    if school is None:
        raise ValidationError({"detail": "School not found.", "code": "school_not_found"})

    raw_term_id = _clean(request.query_params.get("term_id"))
    try:
        term_id = uuid.UUID(raw_term_id)
    except (ValueError, AttributeError):
        raise ValidationError(
            {
                "detail": "A valid term_id UUID is required for Microsoft SDS export.",
                "code": "sds_term_required",
            }
        )

    term = Term.objects.filter(pk=term_id, school_id=school_id, active=True).first()
    if term is None:
        raise ValidationError(
            {
                "detail": "The selected academic term is not active for this school.",
                "code": "sds_term_invalid",
            }
        )

    sections = list(
        Section.objects.filter(school_id=school_id, term_ref_id=term.id)
        .select_related("course")
        .order_by("course__code", "id")
    )
    if not sections:
        raise ValidationError(
            {
                "detail": "Microsoft SDS export blocked: the selected term has no classes.",
                "code": "sds_no_classes",
            }
        )

    student_enrollments = list(
        Enrollment.objects.filter(
            school_id=school_id,
            section_id__in=[section.id for section in sections],
            student__is_active=True,
        )
        .select_related("student", "student__account", "section")
        .order_by("section_id", "student_id")
    )

    teacher_assignments = list(
        TeacherAssignment.objects.filter(
            school_id=school_id,
            section_id__in=[section.id for section in sections],
            staff__status="ACTIVE",
        )
        .select_related("staff", "section")
        .order_by("section_id", "staff_id")
    )

    files = _build_sds_files(
        school=school,
        sections=sections,
        student_enrollments=student_enrollments,
        teacher_assignments=teacher_assignments,
    )
    payload = _zip_sds_files(files)

    response = HttpResponse(payload, content_type="application/zip")
    response["Content-Disposition"] = (
        f'attachment; filename="crown-sds-v2.1-{school.id}-{term.id}.zip"'
    )
    response["X-Crown-SDS-School-Id"] = str(school.id)
    response["X-Crown-SDS-Term-Id"] = str(term.id)
    response["X-Crown-SDS-Classes"] = str(len(sections))
    response["X-Crown-SDS-Students"] = str(
        len({item.student_id for item in student_enrollments})
    )
    response["X-Crown-SDS-Teachers"] = str(
        len({item.staff_id for item in teacher_assignments})
    )
    return response
