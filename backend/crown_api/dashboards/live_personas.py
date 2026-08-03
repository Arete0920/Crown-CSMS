"""Authoritative runtime summaries for the required persona dashboards.

These payloads are built only from persisted tenant-scoped records and the
current authenticated identity. They never substitute frontend/sample values.
"""

from django.db.models import Sum

from core.models import AcademicYear, Student as CoreStudent, UserRole
from crown_api.models_households import Student as IdentityStudent
from crown_api.models_identity import UserPersonLink
from finance.models import FinanceInvoice, MoneyStatus

from .payload_contract import alert, build_dashboard_payload, metric, queue_item


PERSONA_ROLE_CODES = {
    "teacher": "TEACHER",
    "parent": "PARENT",
    "student": "STUDENT",
}

LIVE_PERSONA_DASHBOARDS = frozenset(PERSONA_ROLE_CODES)


class PersonaDashboardPermissionDenied(Exception):
    pass


def _has_required_role(user, school, dashboard_key: str) -> bool:
    token_role = str(getattr(user, "role", "") or "").strip().lower()
    if token_role == dashboard_key:
        return True

    required_role = PERSONA_ROLE_CODES[dashboard_key]
    return UserRole.objects.filter(
        user=user,
        school=school,
        role_code=required_role,
    ).exists()


def _base_meta(*, dashboard_key: str, user, school) -> dict:
    return {
        "served_from": "live_db",
        "source": "core_identity",
        "dashboard_key": dashboard_key,
        "school_id": str(school.id),
        "user_id": str(user.id),
        "role": dashboard_key,
    }


def _teacher_payload(*, user, school):
    staff = getattr(user, "staff", None)
    staff_is_current = bool(staff and staff.school_id == school.id and staff.status == "ACTIVE")
    current_year = AcademicYear.objects.filter(school=school, is_current=True).first()
    active_students = CoreStudent.objects.filter(school=school, status="ACTIVE").count()
    role_count = UserRole.objects.filter(user=user, school=school).count()

    alerts = []
    if staff_is_current:
        alerts.append(alert("Teacher identity is linked to an active staff record", "Low"))
    else:
        alerts.append(
            alert(
                "Teacher login is not linked to an active staff record",
                "Medium",
                "Administrative follow-up is required before staff-only workflows are expanded.",
            )
        )

    return build_dashboard_payload(
        dashboard_key="teacher",
        metrics=[
            metric("Active staff profile", "Yes" if staff_is_current else "No"),
            metric("Assigned roles", role_count),
            metric("Active students at school", active_students),
            metric("Current academic year", current_year.name if current_year else "Not configured"),
        ],
        alerts=alerts,
        queue=[
            queue_item("Open the attendance workspace for assigned classroom work."),
            queue_item("Open the gradebook workspace for authorized grading work."),
        ],
        meta=_base_meta(dashboard_key="teacher", user=user, school=school),
    )


def _parent_payload(*, user, school):
    guardian = getattr(user, "guardian", None)
    guardian_is_current = bool(guardian and guardian.school_id == school.id and guardian.portal_access)
    family = guardian.family if guardian_is_current else None
    linked_students = CoreStudent.objects.filter(
        school=school,
        family=family,
        status="ACTIVE",
    ).count() if family else 0
    open_invoices = FinanceInvoice.objects.filter(
        school=school,
        payer_user=user,
        status=MoneyStatus.OPEN,
    )
    invoice_count = open_invoices.count()
    outstanding_cents = int(open_invoices.aggregate(total=Sum("total_cents"))["total"] or 0)

    alerts = []
    if not guardian_is_current:
        alerts.append(
            alert(
                "Parent login is not linked to an active guardian portal record",
                "Medium",
                "Family access must be reconciled before protected student details are shown.",
            )
        )
    elif linked_students == 0:
        alerts.append(
            alert(
                "No active students are linked to this guardian family",
                "Medium",
                "The dashboard is withholding student-specific records until the relationship exists.",
            )
        )
    else:
        alerts.append(alert("Guardian and student relationship is active", "Low"))

    return build_dashboard_payload(
        dashboard_key="parent",
        metrics=[
            metric("Guardian portal access", "Active" if guardian_is_current else "Not linked"),
            metric("Linked active students", linked_students),
            metric("Open invoices", invoice_count),
            metric("Outstanding family balance", f"${outstanding_cents / 100:,.2f}"),
        ],
        alerts=alerts,
        queue=[
            queue_item("Review linked student and family account information."),
            queue_item("Open communications for authorized family messages."),
        ],
        meta={
            **_base_meta(dashboard_key="parent", user=user, school=school),
            "guardian_linked": guardian_is_current,
            "family_id": str(family.id) if family else None,
        },
    )


def _student_payload(*, user, school):
    # Student identity must come from the canonical UserPersonLink. Never match
    # protected records by display name, email convention, or another guess.
    person_link = UserPersonLink.objects.select_related("person").filter(user=user).first()
    identity_student = None
    if person_link:
        identity_student = IdentityStudent.objects.filter(
            person=person_link.person,
            active=True,
        ).first()

    role_count = UserRole.objects.filter(user=user, school=school).count()
    alerts = []
    if identity_student:
        alerts.append(alert("Student login is linked to the canonical person identity", "Low"))
    else:
        alerts.append(
            alert(
                "Student login is not linked to a canonical student identity",
                "Medium",
                "Protected academic details remain withheld until UserPersonLink reconciliation is complete.",
            )
        )

    return build_dashboard_payload(
        dashboard_key="student",
        metrics=[
            metric("Student profile", "Linked" if identity_student else "Not linked"),
            metric("Current grade", identity_student.grade_level if identity_student else "Not linked"),
            metric("Student status", "ACTIVE" if identity_student else "Not linked"),
            metric("Assigned roles", role_count),
        ],
        alerts=alerts,
        queue=[
            queue_item("Review schedule and assignments after canonical student identity is linked."),
            queue_item("Open authorized student communications and next actions."),
        ],
        meta={
            **_base_meta(dashboard_key="student", user=user, school=school),
            "person_link_id": str(person_link.id) if person_link else None,
            "identity_student_id": str(identity_student.id) if identity_student else None,
        },
    )


def build_persona_dashboard_payload(*, dashboard_key: str, user, school):
    if dashboard_key not in LIVE_PERSONA_DASHBOARDS:
        return None
    if not _has_required_role(user, school, dashboard_key):
        raise PersonaDashboardPermissionDenied(dashboard_key)
    if dashboard_key == "teacher":
        return _teacher_payload(user=user, school=school)
    if dashboard_key == "parent":
        return _parent_payload(user=user, school=school)
    return _student_payload(user=user, school=school)
