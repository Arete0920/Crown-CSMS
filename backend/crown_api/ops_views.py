"""
DEV-only ops endpoints for CI automation.
Guarded by X-Admin-Ops-Secret header.
"""
from __future__ import annotations

import logging
import os
from uuid import UUID

logger = logging.getLogger(__name__)

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from core.models import School, UserRole
from core.seed_helpers import ensure_deterministic_school


def _dev_ops_enabled() -> bool:
    # Only allow in DEV; keep this strict.
    return bool(getattr(settings, "DEV_OPS_SECRET", "")) and getattr(settings, "ENVIRONMENT", "dev") == "dev"


def _dev_only():
    """Raise Http404 if running in production. Call at the top of every dev/ops view."""
    from django.http import Http404
    env = (
        os.getenv("ENVIRONMENT") or
        os.getenv("CROWN_ENV") or
        os.getenv("DJANGO_ENV") or
        ""
    ).strip().lower()
    if env in {"prod", "production", "live"}:
        raise Http404


def _check_ops_secret(request) -> bool:
    header = request.headers.get("X-Admin-Ops-Secret", "") or request.META.get("HTTP_X_ADMIN_OPS_SECRET", "")
    expected = getattr(settings, "DEV_OPS_SECRET", "")
    return bool(expected) and header == expected


def _require_ops_secret(request):
    expected = getattr(settings, "DEV_OPS_SECRET", None) or os.getenv("DEV_OPS_SECRET")
    provided = request.headers.get("X-DevOps-Secret") or request.META.get("HTTP_X_DEVOPS_SECRET")
    if not expected or provided != expected:
        return JsonResponse({"detail": "forbidden"}, status=403)
    return None


@api_view(["POST"])
@permission_classes([AllowAny])
def ensure_ci_user(request):
    """
    DEV-only: Idempotently ensure CI smoke user exists and return JWT.
    Reads credentials from Azure App Service settings (CI_SMOKE_*).
    Guarded by X-Admin-Ops-Secret header.
    
    Returns JWT for immediate use in smoke tests.
    """
    if not _dev_ops_enabled():
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if not _check_ops_secret(request):
        return Response({"detail": "Forbidden."}, status=status.HTTP_403_FORBIDDEN)

    # Read from server-side env vars (Azure App Service settings)
    username = os.getenv("CI_SMOKE_USERNAME", "").strip()
    password = os.getenv("CI_SMOKE_PASSWORD", "").strip()
    school_id_raw = os.getenv("CI_SMOKE_SCHOOL_ID", "").strip()

    if not username or not password or not school_id_raw:
        return Response(
            {"detail": "Server misconfigured: missing CI_SMOKE_USERNAME, CI_SMOKE_PASSWORD, or CI_SMOKE_SCHOOL_ID"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    try:
        school_id = UUID(school_id_raw)
    except Exception:
        return Response(
            {"detail": "Server misconfigured: CI_SMOKE_SCHOOL_ID must be valid UUID"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Use canonical helper for deterministic school creation
    school, created = ensure_deterministic_school(school_id)

    User = get_user_model()
    lookup_field = getattr(User, "USERNAME_FIELD", "username")
    lookup = {lookup_field: username}

    user, created = User.objects.get_or_create(defaults={}, **lookup)

    # Ensure account is usable for smoke tests
    user.is_active = True
    if hasattr(user, "is_staff"):
        user.is_staff = True

    # Idempotent password reset (matches Azure setting)
    user.set_password(password)
    
    # Bind tenant context
    if hasattr(user, "school_id"):
        user.school_id = school_id
    if hasattr(user, "school"):
        user.school = school
    user.save()

    # Ensure CI user has director role for smoke tests
    UserRole.objects.update_or_create(
        user=user,
        defaults={"school": school, "role_code": "AID_DIRECTOR"}
    )

    # Ensure CI user can perform billing actions
    finance_group, _ = Group.objects.get_or_create(name="Business Manager")
    user.groups.add(finance_group)

    # Generate JWT
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)

    return Response(
        {
            "ok": True,
            "created": created,
            "username": username,
            "school_id": str(school_id),
            "access": access_token,
        },
        status=status.HTTP_200_OK,
    )


@require_GET
def demo_school(request):
    """
    DEV-only ops endpoint that returns the canonical demo school UUID.
    Used to set CI_SMOKE_SCHOOL_ID deterministically.
    """
    env = os.getenv("ENVIRONMENT", "").lower()
    if env not in {"dev", "development"}:
        return JsonResponse({"detail": "not allowed outside dev"}, status=403)

    forbidden = _require_ops_secret(request)
    if forbidden:
        return forbidden

    # If you already have a canonical "demo school id" env var, use it.
    school_id = os.getenv("DEMO_SCHOOL_ID") or os.getenv("DEFAULT_SCHOOL_ID")
    if school_id:
        return JsonResponse({"school_id": school_id}, status=200)

    # Otherwise: fetch the first School row (deterministic enough for DEV)
    try:
        from core.models import School
    except Exception:
        return JsonResponse({"detail": "School model import failed"}, status=500)

    school = School.objects.order_by("created_at", "id").first()
    if not school:
        return JsonResponse({"detail": "No School rows found. Seed DEV first."}, status=500)

    return JsonResponse({"school_id": str(school.id), "name": getattr(school, "name", "")}, status=200)


# ---- Ops Summary (for demo dashboard) ----


def _safe_count(model):
    """Count rows in model; return None if fails."""
    try:
        return model.objects.count()
    except Exception:
        return None


@require_GET
def ops_summary(request):
    """
    Read-only ops summary for demo/proof runs.
    Returns build SHA, demo mode, seed timestamps, and real counts across major modules.
    No auth assumptions here; keep it simple for demo hardening.
    """
    _dev_only()
    from django.utils import timezone
    from core.models import AcademicYear

    # Build + mode
    build_sha = os.environ.get("BUILD_SHA") or "local-dev"
    demo_mode = getattr(settings, "CROWN_DEMO_MODE", False)

    # SeedRun (if present)
    seed_last = None
    try:
        from core.models import SeedRun
        sr = SeedRun.objects.order_by("-created_at").first()
        if sr:
            seed_last = {
                "name": sr.name,
                "created_at": sr.created_at.isoformat(),
                "meta": sr.meta if hasattr(sr, "meta") else None,
            }
    except Exception:
        seed_last = None

    # Current school/year (best-effort)
    school = School.objects.order_by("-created_at").first()
    year = AcademicYear.objects.filter(school=school).order_by("-created_at").first() if school else None

    # Counts (best-effort imports)
    students = households = admissions_apps = invoices = grade_entries = comm_threads = comm_messages = None

    try:
        from students.models import Student
        students = _safe_count(Student)
    except Exception:
        pass

    try:
        from households.models import Household
        households = _safe_count(Household)
    except Exception:
        pass

    try:
        from admissions.models import AdmissionsApplication
        admissions_apps = _safe_count(AdmissionsApplication)
    except Exception:
        pass

    try:
        from billing.models import Invoice
        invoices = _safe_count(Invoice)
    except Exception:
        pass

    try:
        from gradebook.models import GradeEntry
        grade_entries = _safe_count(GradeEntry)
    except Exception:
        pass

    try:
        from comms.models import Thread, Message
        comm_threads = _safe_count(Thread)
        comm_messages = _safe_count(Message)
    except Exception:
        pass

    payload = {
        "ok": True,
        "ts": timezone.now().isoformat(),
        "build_sha": build_sha,
        "demo_mode": demo_mode,
        "seed_last": seed_last,
        "school": {"id": str(school.id), "name": school.name} if school else None,
        "academic_year": {"id": str(year.id), "label": getattr(year, "label", None)} if year else None,
        "counts": {
            "students": students,
            "households": households,
            "admissions_applications": admissions_apps,
            "invoices": invoices,
            "grade_entries": grade_entries,
            "comms_threads": comm_threads,
            "comms_messages": comm_messages,
        },
    }
    return JsonResponse(payload)


# ---- Predictive Alerts Lite ----


@require_GET
def ops_alerts(request):
    """
    Predictive Alerts Lite:
    - Deterministic rule checks based on current DB state.
    - No external services, no background jobs.
    - Tracks dependency imports so failures are visible (not silent).
    - Strict mode (?strict=1) returns 500 if imports fail (useful for CI).
    """
    _dev_only()
    from django.utils import timezone
    from django.db.models import Max

    ts = timezone.now().isoformat()
    alerts = []
    deps = {"admissions": False, "finance": False, "gradebook": False}
    errors = []
    
    # Strict mode: if any import fails + strict=1, return 500
    strict = request.GET.get("strict") == "1"

    # --- Helper to append alerts consistently ---
    def add_alert(alert_id, severity, title, detail, metric=None, value=None, threshold=None):
        alerts.append({
            "id": alert_id,
            "severity": severity,   # "critical" | "warning" | "info"
            "title": title,
            "detail": detail,
            "metric": metric,
            "value": value,
            "threshold": threshold,
            "ts": ts,
        })

    # --- Defensive imports inside try blocks (track failures) ---
    Application = None
    Invoice = None
    Payment = None
    GradeEntry = None

    try:
        from admissions.models import AdmissionsApplication
        Application = AdmissionsApplication
        deps["admissions"] = True
    except Exception as e:
        errors.append(f"admissions import failed: {type(e).__name__}")

    try:
        from billing.models import Invoice
        from ledger.models import Payment
        deps["finance"] = True
    except Exception as e:
        errors.append(f"finance import failed: {type(e).__name__}")

    try:
        from gradebook.models import GradeEntry
        deps["gradebook"] = True
    except Exception as e:
        errors.append(f"gradebook import failed: {type(e).__name__}")

    # --- Rule 1: Demo looks empty (critical) ---
    # If all core counts are extremely low, the demo will feel hollow.
    core_counts = {}
    try:
        core_counts["admissions_applications"] = Application.objects.count() if Application else None
    except Exception:
        core_counts["admissions_applications"] = None

    try:
        core_counts["invoices"] = Invoice.objects.count() if Invoice else None
    except Exception:
        core_counts["invoices"] = None

    try:
        core_counts["grade_entries"] = GradeEntry.objects.count() if GradeEntry else None
    except Exception:
        core_counts["grade_entries"] = None

    # Only evaluate if we actually have at least 2 metrics available
    available = [v for v in core_counts.values() if isinstance(v, int)]
    if len(available) >= 2:
        if all(v < 5 for v in available):
            add_alert(
                "demo_empty",
                "critical",
                "Demo data looks sparse",
                f"Core demo counts are low: {core_counts}. Seed the demo dataset before presenting.",
                metric="core_counts",
                value=core_counts,
                threshold=">=5 in each core area",
            )

    # --- Rule 2: Admissions present, but finance missing (warning) ---
    if isinstance(core_counts.get("admissions_applications"), int) and isinstance(core_counts.get("invoices"), int):
        if core_counts["admissions_applications"] >= 5 and core_counts["invoices"] == 0:
            add_alert(
                "finance_missing",
                "warning",
                "Admissions present but finance is empty",
                "You have applications but no invoices. Run finance seed so the story flows into billing.",
                metric="invoices",
                value=core_counts["invoices"],
                threshold=">0",
            )

    # --- Rule 3: Gradebook missing (warning) ---
    if isinstance(core_counts.get("grade_entries"), int):
        if core_counts["grade_entries"] == 0:
            add_alert(
                "gradebook_missing",
                "warning",
                "Gradebook has no entries",
                "No grade entries found. Seed gradebook so the academic side is believable.",
                metric="grade_entries",
                value=core_counts["grade_entries"],
                threshold=">0",
            )

    # --- Rule 4: Payments trail invoices too much (info/warning) ---
    # If payments are far behind, it can be a good "collections" story, but you want it intentional.
    if Invoice and Payment:
        try:
            invoice_count = Invoice.objects.count()
            payment_count = Payment.objects.count()
            if invoice_count >= 10 and payment_count == 0:
                add_alert(
                    "no_payments",
                    "warning",
                    "Invoices exist but no payments recorded",
                    "This is fine if intentional, but most demos benefit from a few payments to show the loop.",
                    metric="payments",
                    value=payment_count,
                    threshold=">=1",
                )
            elif invoice_count >= 20 and payment_count / max(invoice_count, 1) < 0.05:
                add_alert(
                    "low_payment_ratio",
                    "info",
                    "Low payment-to-invoice ratio",
                    "Payment activity is low relative to invoices. Consider seeding a few payments for realism.",
                    metric="payment_ratio",
                    value=round(payment_count / max(invoice_count, 1), 3),
                    threshold=">=0.05",
                )
        except Exception:
            logger.debug("health rule: payment ratio check failed", exc_info=True)

    # --- Rule 5: Stale data indicator (info) ---
    # Uses max created/updated timestamps if available on one known model.
    # Keep it defensive to avoid field errors.
    if Application:
        try:
            last = Application.objects.aggregate(m=Max("created_at"))["m"]
            if last:
                age_days = (timezone.now() - last).days
                if age_days >= 7:
                    add_alert(
                        "stale_admissions",
                        "info",
                        "Admissions data may be stale",
                        f"Most recent application is {age_days} days old. Fresh data reads better in live demos.",
                        metric="admissions_last_created_days",
                        value=age_days,
                        threshold="<7",
                    )
        except Exception:
            logger.debug("health rule: stale data check failed", exc_info=True)

    # --- Strict mode: if imports failed + strict=1, return 500 for CI visibility ---
    if strict and errors:
        return JsonResponse(
            {
                "ok": False,
                "error": "Strict mode: dependencies failed to import",
                "errors": errors,
                "deps": deps,
                "ts": ts,
            },
            status=500,
        )

    # --- Build SHA support (for deployment/verification) ---
    import os
    build_sha = os.environ.get("BUILD_SHA", "local-dev")

    return JsonResponse(
        {
            "ok": True,
            "build_sha": build_sha,
            "ts": ts,
            "alerts": alerts,
            "deps": deps,
            "errors": errors,
        }
    )
