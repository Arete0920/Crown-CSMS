"""Read-only program projections. No custody mutations or settlement inference."""
from datetime import datetime, time, timedelta
from decimal import Decimal
from uuid import UUID
from zoneinfo import ZoneInfo

from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from aftercare.models import AftercareAttendance, AftercareEnrollment, AftercareProgramConfig
from ledger.models import Charge
from summer_camp.models import (
    SummerCampAttendance, SummerCampBillingLedgerLink, SummerCampEnrollment,
    SummerCampIncident, SummerCampProgramConfig,
)
from .payload_contract import build_dashboard_payload, metric, validate_dashboard_payload


PROGRAM_PERMISSIONS = {
    "summer-camp": "summer_camp.view",
    "extended-care": "extended_care.view",
}
UNAVAILABLE = "Not available"


def _windows(school):
    observed = timezone.now()
    if timezone.is_naive(observed) or not school.timezone:
        raise ValueError("A school timezone and aware observation are required.")
    local_tz = ZoneInfo(school.timezone)
    today = observed.astimezone(local_tz).date()
    day_start = datetime.combine(today, time.min, tzinfo=local_tz)
    day_end = datetime.combine(today + timedelta(days=1), time.min, tzinfo=local_tz)
    month_start = day_start.replace(day=1)
    return observed, today, day_start, day_end, month_start


def _payload(key, school, windows, metrics):
    observed, today, start, end, month = windows
    return build_dashboard_payload(key, metrics, [], [], meta={
        "served_from": "live_db", "school_id": str(school.id),
        "observed_at": observed.isoformat(),
        "aggregation_window": (
            f"timezone={school.timezone}; local-day=[{start.isoformat()},{end.isoformat()}); "
            f"month-to-observed=[{month.isoformat()},{observed.isoformat()}]; "
            + ("enrollment=registered/waitlisted-all-sessions; charges=all-recorded-linked-obligations"
               if key == "summer-camp" else f"enrollment=active-date-ranges-on:{today}")
        ),
        "source": "canonical_program_database_projection",
        # A query is source evidence, never independent operational certification.
        "certification_status": "not_independently_certified",
    })


def validate_program_payload(payload, school):
    validate_dashboard_payload(payload)
    meta = payload["meta"]
    observed = parse_datetime(meta.get("observed_at", ""))
    if (
        meta.get("served_from") != "live_db"
        or meta.get("school_id") != str(school.id)
        or observed is None or timezone.is_naive(observed)
        or not isinstance(meta.get("aggregation_window"), str)
        or not meta["aggregation_window"].strip()
        or meta.get("live_certified") is True
    ):
        raise ValueError("Program provenance unavailable.")


def _assessed_camp_charges(school):
    links = list(SummerCampBillingLedgerLink.objects.filter(
        school=school,
    ).exclude(status="CANCELLED").values("charge_id", "amount_cents", "enrollment__student__household_id", "enrollment__school_id", "enrollment__session__school_id", "enrollment__session__program__school_id", "enrollment__student__school_id"))
    if not links:
        return UNAVAILABLE
    try:
        ids = {UUID(row["charge_id"]) for row in links}
    except (ValueError, TypeError, AttributeError):
        return UNAVAILABLE
    charges = {row.id: row for row in Charge.objects.filter(
        id__in=ids, school_id=school.id, account__school_id=school.id,
        account__household__school_id=school.id, is_void=False,
    ).select_related("account")}
    for link in links:
        charge = charges.get(UUID(link["charge_id"]))
        amount = link["amount_cents"]
        if (any(link[field] != school.id for field in (
                "enrollment__school_id", "enrollment__session__school_id",
                "enrollment__session__program__school_id", "enrollment__student__school_id"))
                or charge is None or type(amount) is not int or amount < 0
                or charge.amount < 0 or not charge.amount.is_finite()
                or charge.amount * 100 != amount
                or charge.account.household_id != link["enrollment__student__household_id"]):
            return UNAVAILABLE
    # Multiple enrollment links to the same ledger fact cannot multiply money.
    total = sum((charge.amount for charge in charges.values()), Decimal("0"))
    return f"${total:,.2f}"


def _camp(school, windows):
    observed, today, start, _end, month = windows
    if not SummerCampProgramConfig.objects.filter(school=school).exists():
        raise ValueError("Camp configuration unavailable.")
    base = SummerCampEnrollment.objects.filter(school=school, status__in=["REGISTERED", "WAITLISTED"])
    valid = Q(
        session__school=school, session__program__school=school,
        student__school_id=school.id, student__household__school_id=school.id,
    )
    if base.exclude(valid).exists():
        raise ValueError("Unattributable Camp enrollment.")
    registered = base.filter(status="REGISTERED")
    attendance = SummerCampAttendance.objects.filter(school=school, date=today)
    owned = Q(session__school=school, session__program__school=school,
              student__school_id=school.id, student__household__school_id=school.id)
    if attendance.exclude(owned).exists():
        raise ValueError("Unattributable Camp attendance.")
    arrived = attendance.filter(checkin_time__gte=start, checkin_time__lte=observed)
    incidents = SummerCampIncident.objects.filter(
        school=school, created_at__gte=month, created_at__lte=observed,
    )
    incident_owner = Q(session__school=school, session__program__school=school) & (
        Q(student__isnull=True) | Q(student__school_id=school.id, student__household__school_id=school.id)
    )
    if incidents.exclude(incident_owner).exists():
        raise ValueError("Unattributable Camp incident.")
    return _payload("summer-camp", school, windows, [
        metric("Registered Campers", registered.values("student_id").distinct().count(), "Unique children with registered records; all sessions."),
        metric("Registration Records", registered.count(), "Registered rows, including repeat session registrations; not unique children."),
        metric("Waitlisted Children", base.filter(status="WAITLISTED").values("student_id").distinct().count()),
        metric("Children Arrived Today", arrived.values("student_id").distinct().count(), "Actual school-local-day check-ins; not current custody or scheduled sessions."),
        metric("Incidents MTD", incidents.count(), "School-local month through observed time."),
        metric("Assessed Camp Charges", _assessed_camp_charges(school), "Verified ledger-linked obligations; not cash collected or settled receipts. Missing or invalid links are unavailable."),
        metric("Settled Camp Receipts", UNAVAILABLE, "No authoritative program settlement mapping; paid registration status and ledger payments do not prove settlement."),
        metric("Staffed Sessions", UNAVAILABLE, "Staff coverage is not established by this projection."),
        metric("Transport Confirmed", UNAVAILABLE, "Transport confirmation records are not available."),
    ])


def _care(school, windows):
    observed, today, start, _end, month = windows
    if not AftercareProgramConfig.objects.filter(school_fk=school).exists():
        raise ValueError("Care configuration unavailable.")
    enrollments = AftercareEnrollment.objects.filter(
        school_fk=school, is_active=True, start_date__lte=today,
    ).filter(Q(end_date__isnull=True) | Q(end_date__gte=today))
    owned = Q(student_fk__school_id=school.id, student_fk__household__school_id=school.id, care_session__in=["AM", "PM"])
    attendance = AftercareAttendance.objects.filter(school_fk=school, date__range=(month.date(), today))
    if enrollments.exclude(owned).exists() or attendance.exclude(owned).exists():
        raise ValueError("Unattributable Care records.")
    arrivals = attendance.filter(date=today, checkin_time__gte=start, checkin_time__lte=observed)
    metrics = [metric("Enrolled Students", enrollments.values("student_fk_id").distinct().count(), "Unique children across AM and PM; active date ranges, not scheduled attendance."),
               metric("Attendance Today", arrivals.values("student_fk_id").distinct().count(), "Unique children with actual school-local-day check-ins; not current custody.")]
    for session in ("AM", "PM"):
        metrics.extend([
            metric(f"{session} Enrolled Students", enrollments.filter(care_session=session).values("student_fk_id").distinct().count()),
            metric(f"{session} Children Arrived Today", arrivals.filter(care_session=session).values("student_fk_id").distinct().count()),
            metric(f"{session} Attendance Sessions MTD", attendance.filter(care_session=session, checkin_time__gte=month, checkin_time__lte=observed).count(), "Recorded attendance sessions, not daily unique children."),
        ])
    metrics.extend([
        metric("Invoices Due", UNAVAILABLE, "No authoritative invoice projection is available."),
        metric("Staff Coverage", UNAVAILABLE, "Coverage is not established by this projection."),
        metric("Settled Care Receipts", UNAVAILABLE, "Assessed late fees and enrollment rates do not prove payment settlement."),
    ])
    return _payload("extended-care", school, windows, metrics)


def build_program_live_payload(key, school):
    windows = _windows(school)
    payload = {"summer-camp": _camp, "extended-care": _care}[key](school, windows)
    validate_program_payload(payload, school)
    return payload
