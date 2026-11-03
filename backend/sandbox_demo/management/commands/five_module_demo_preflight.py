"""Read-only acceptance inventory for the isolated, fictional five-module demo.

Not a deployment, fixture seeder, permission grant, or substitute for browser QA.
Use after scripts/demo/start_heritage_local.py --prepare-only.
"""
from __future__ import annotations

import re
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError
from django.utils import timezone

from sandbox_demo.catalog import SANDBOX_SCHOOLS


ROOT = Path(__file__).resolve().parents[4]
LOCAL_DB = ROOT / ".local-backups" / "heritage-demo" / "heritage.sqlite3"

# Route constants and rendered components must both be present in router.jsx.
FRONTEND_EXPECTATIONS = {
    "Jireh Financial Aid": (
        (r"\bPATHS\.FINANCIAL_AID\b", r"\bFinancialAidDashboard\b"),
        (r"\bPATHS\.PARENT_FINANCIAL_AID\b", r"\bParentFinancialAidPreparationPage\b"),
    ),
    "Jireh SGO": (
        (r"\bPATHS\.[A-Z0-9_]*SGO[A-Z0-9_]*\b",
         r"\b(?:JirehSGO|SGODashboard|SgoDashboard)\w*\b"),
    ),
    "Extended Care": (
        (r"\bPATHS\.BEFORECARE_DIRECTOR\b", r"\bCareSessionDirectorDashboard\b"),
        (r"\bPATHS\.AFTERCARE_DIRECTOR\b", r"\bCareSessionDirectorDashboard\b"),
    ),
    "Diadem Daycare": (
        (r"\bPATHS\.[A-Z0-9_]*(?:DIADEM|DAYCARE)[A-Z0-9_]*\b",
         r"\b(?:DiademDirectorRosterPage|DaycareDirectorPage)\b"),
    ),
    "Summer Camp": (
        (r"\bPATHS\.SUMMER_CAMP_ROSTER\b", r"\bSummerCampRosterPage\b"),
    ),
}


def frontend_route_evidence(paths_text: str, router_text: str) -> dict[str, bool]:
    """Source-level smoke check. Browser interaction is separately required."""
    results = {}
    for module, route_pairs in FRONTEND_EXPECTATIONS.items():
        results[module] = all(
            re.search(path_pattern, router_text) is not None
            and re.search(path_pattern.replace(r"\bPATHS\.", ""), paths_text) is not None
            and re.search(component_pattern, router_text) is not None
            for path_pattern, component_pattern in route_pairs
        )
    return results


def _require_isolated_local_database() -> None:
    database = settings.DATABASES["default"]
    if (
        not settings.DEBUG
        or getattr(settings, "CROWN_ENV", None) != "local"
        or not database["ENGINE"].endswith(".sqlite3")
        or Path(str(database["NAME"])).resolve() != LOCAL_DB.resolve()
    ):
        raise CommandError(
            "Five-module demo audit is restricted to the isolated Heritage local SQLite database."
        )


def _model_count(app_label: str, model_name: str, **filters) -> tuple[int | None, str]:
    try:
        model = apps.get_model(app_label, model_name)
    except LookupError:
        return None, f"{app_label}.{model_name} is not installed in this source"
    try:
        return model.objects.filter(**filters).count(), ""
    except (DatabaseError, ValueError, TypeError) as exc:
        return None, f"schema or query is not ready ({type(exc).__name__})"


def camp_entitlement_evidence(school_id) -> bool:
    """Use the same DB-backed module gate as the real Camp API, not route presence."""
    from subscriptions.gates import school_has_module

    return bool(school_has_module(school_id, "little_lambs"))


class Command(BaseCommand):
    help = "Read-only five-module Heritage local demo acceptance inventory."

    def add_arguments(self, parser):
        parser.add_argument(
            "--strict", action="store_true",
            help="Return a failure if any required module route or synthetic record is unavailable.",
        )

    def handle(self, *args, **options):
        _require_isolated_local_database()
        from core.models import School

        findings: list[tuple[bool, str]] = []

        def record(label, passed, detail):
            findings.append((bool(passed), f"{label}: {detail}"))

        school_id = SANDBOX_SCHOOLS["heritage-core"].id
        school = School.objects.filter(pk=school_id, is_active=True).first()
        if school is None:
            raise CommandError("Heritage school seed is missing; prepare the local demo first.")
        try:
            day = timezone.now().astimezone(ZoneInfo(school.timezone)).date()
        except (ZoneInfoNotFoundError, ValueError, TypeError, AttributeError) as exc:
            raise CommandError("Heritage school timezone is unavailable or invalid.") from exc

        frontend = ROOT / "frontend" / "dashboards" / "src" / "routes"
        try:
            paths_text = (frontend / "paths.js").read_text(encoding="utf-8")
            router_text = (frontend / "router.jsx").read_text(encoding="utf-8")
        except OSError as exc:
            raise CommandError("Dashboard route source is missing from the local checkout.") from exc

        for module, exists in frontend_route_evidence(paths_text, router_text).items():
            record(f"{module} frontend", exists, "routed" if exists else "no verified routed page")

        def require_count(label, app_label, model_name, **filters):
            count, error = _model_count(app_label, model_name, **filters)
            record(label, count is not None and count > 0,
                   error or f"fictional records={count}")
            return count or 0

        # Jireh Setup operates on canonical aid models, not legacy financial_aid
        # rows. An award must be from this school's same-year, same-family
        # application for a school-owned student; no unrelated award suffices.
        from django.db.models import F

        require_count(
            "Jireh canonical applications", "aid", "AidApplication",
            school_id=school.id, family__school_id=school.id,
            academic_year__school_id=school.id,
            status__in=("SUBMITTED", "UNDER_REVIEW", "NEEDS_INFO", "APPROVED"),
        )
        require_count(
            "Jireh canonical offered awards", "aid", "AidAward",
            school_id=school.id, student__school_id=school.id,
            student__family__school_id=school.id,
            academic_year__school_id=school.id,
            aid_application__isnull=False,
            aid_application__school_id=school.id,
            aid_application__family_id=F("student__family_id"),
            aid_application__academic_year_id=F("academic_year_id"),
            decision_status__in=("OFFERED", "ACCEPTED"),
            awarded_cents__gt=0,
        )

        require_count(
            "Jireh SGO noncash applications", "jireh_sgo",
            "SGOApplication", school_key=school.id,
        )
        for session in ("AM", "PM"):
            require_count(
                f"Extended Care {session} enrollments", "aftercare",
                "AftercareEnrollment", school_fk_id=school.id,
                is_active=True, care_session=session,
            )

        require_count(
            "Diadem Daycare active enrollments", "aftercare",
            "DaycareEnrollment", school_id=school.id, status="ACTIVE",
        )
        # Even complete fictional session records are not operational proof
        # if the school would receive MODULE_NOT_ENABLED from the Camp API.
        entitlement_active = camp_entitlement_evidence(school.id)
        record(
            "Summer Camp entitlement",
            entitlement_active,
            "authorized for fictional school" if entitlement_active
            else "missing, inactive, suspended or expired; Camp API access is denied",
        )
        try:
            from summer_camp.models import SummerCampSession, SummerCampEnrollment
            sessions = SummerCampSession.objects.filter(
                school_id=school.id, status="PUBLISHED",
                start_date__lte=day, end_date__gte=day,
            )
            record("Summer Camp session", sessions.exists(),
                   f"published sessions for local {day}: {sessions.count()}")
            current = SummerCampEnrollment.objects.filter(
                school_id=school.id, status="REGISTERED", session__in=sessions,
            ).count()
            record("Summer Camp registrations", current > 0,
                   f"registered campers for local {day}: {current}")
        except (DatabaseError, ValueError) as exc:
            record("Summer Camp session/registrations", False,
                   f"schema not ready ({type(exc).__name__})")

        failed = 0
        for passed, message in findings:
            if passed:
                self.stdout.write(self.style.SUCCESS("PASS " + message))
            else:
                failed += 1
                self.stdout.write(self.style.ERROR("FAIL " + message))
        self.stdout.write(
            f"Local five-module evidence: pass={len(findings)-failed} fail={failed}. "
            "Source and data only; a real Windows browser walkthrough is still required."
        )
        if options["strict"] and failed:
            raise CommandError(
                f"Five-module local demo is not ready: {failed} failed evidence gate(s)."
            )
