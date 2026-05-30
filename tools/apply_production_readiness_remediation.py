from __future__ import annotations

from pathlib import Path


def _find_repo_root(start: Path) -> Path:
    # Walk upward until we find a directory that matches the expected repo shape.
    for candidate in [start, *start.parents]:
        if (candidate / "backend" / "crown_api" / "settings.py").exists():
            return candidate
    raise FileNotFoundError("could not locate repository root containing backend/crown_api/settings.py")


ROOT = _find_repo_root(Path.cwd())


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8-sig")


def write(path: str, text: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8", newline="\n")
    print(f"updated {path}")


def require(path: str) -> None:
    if not (ROOT / path).exists():
        raise FileNotFoundError(f"required file missing: {path}")


# ---------------------------------------------------------------------------
# Active Django custom user model setting
# ---------------------------------------------------------------------------
settings_path = "backend/crown_api/settings.py"
require(settings_path)
settings = read(settings_path)

if "AUTH_USER_MODEL" not in settings:
    marker = "WSGI_APPLICATION = 'crown_api.wsgi.application'"
    if marker not in settings:
        raise RuntimeError("could not locate WSGI_APPLICATION marker in settings.py")
    settings = settings.replace(
        marker,
        marker
        + '\n\n# Crown canonical user model. Required because core.UserAccount subclasses AbstractUser.\nAUTH_USER_MODEL = "core.UserAccount"',
        1,
    )
    write(settings_path, settings)
else:
    print("settings.py already contains AUTH_USER_MODEL")


# ---------------------------------------------------------------------------
# Release workflow strictness and frontend source-of-truth check
# ---------------------------------------------------------------------------
workflow_path = ".github/workflows/release-verify.yml"
require(workflow_path)
workflow = read(workflow_path)
workflow = workflow.replace("python backend/manage.py check --deploy || true", "python backend/manage.py check --deploy")
workflow = workflow.replace("python manage.py check --deploy || true", "python manage.py check --deploy")

frontend_check = """      - name: Frontend source-of-truth check
        shell: bash
        run: |
          test -f frontend/dashboards/package.json
          test -f frontend/dashboards/package-lock.json
"""
if "Frontend source-of-truth check" not in workflow:
    marker = "      - uses: actions/setup-node@"
    if marker not in workflow:
        raise RuntimeError("could not locate setup-node step in release-verify.yml")
    workflow = workflow.replace(marker, frontend_check + marker, 1)
write(workflow_path, workflow)


# ---------------------------------------------------------------------------
# Frontend audit should fail if expected frontend is absent.
# ---------------------------------------------------------------------------
audit_path = "tools/audit_frontend.ps1"
require(audit_path)
audit = read(audit_path)
audit = audit.replace(
    '  Write-Host "frontend/dashboards not found; skipping frontend audit" -ForegroundColor Yellow\n  exit 0',
    '  throw "frontend/dashboards not found; frontend audit cannot pass until the frontend source of truth is present."',
)
write(audit_path, audit)


# ---------------------------------------------------------------------------
# Aftercare discipline ID must store DisciplineIncident UUIDs.
# ---------------------------------------------------------------------------
aftercare_models_path = "backend/aftercare/models.py"
require(aftercare_models_path)
aftercare_models = read(aftercare_models_path)
aftercare_models = aftercare_models.replace(
    "discipline_record_id = models.IntegerField(null=True, blank=True)",
    "discipline_record_id = models.UUIDField(null=True, blank=True)",
)
write(aftercare_models_path, aftercare_models)


# ---------------------------------------------------------------------------
# Real Aftercare integration adapter.
# ---------------------------------------------------------------------------
integrations_path = "backend/aftercare/integrations.py"
integrations = '''from __future__ import annotations

from typing import Any

from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.utils import timezone

from core.models import School, Student as CoreStudent, UserAccount
from discipline.models import DisciplineAction, DisciplineIncident
from finance.models import FinanceObligation, MoneyStatus, ObligationType

from .models import AftercareEnrollment


def _resolve_school_from_aftercare(school_id: int) -> School:
    try:
        school = School.objects.filter(pk=school_id).first()
        if school:
            return school
    except Exception:
        pass

    enrollment = (
        AftercareEnrollment.objects
        .filter(school_id=school_id, school_fk__isnull=False)
        .select_related("school_fk")
        .order_by("-id")
        .first()
    )
    if enrollment and enrollment.school_fk:
        return enrollment.school_fk

    raise ImproperlyConfigured(
        "Aftercare legacy school_id could not be resolved to core.School. "
        "Populate aftercare school_fk or migrate Aftercare to canonical school FK."
    )


def _resolve_core_student_from_aftercare(school: School, legacy_school_id: int, student_id: int) -> CoreStudent:
    try:
        student = CoreStudent.objects.filter(pk=student_id, school=school).first()
        if student:
            return student
    except Exception:
        pass

    enrollment = (
        AftercareEnrollment.objects
        .filter(school_id=legacy_school_id, student_id=student_id)
        .select_related("student_fk", "school_fk")
        .order_by("-id")
        .first()
    )

    if enrollment and enrollment.student_fk:
        legacy_student: Any = enrollment.student_fk

        for attr in ("core_student", "core_student_fk", "student"):
            candidate = getattr(legacy_student, attr, None)
            if isinstance(candidate, CoreStudent) and candidate.school_id == school.id:
                return candidate

        first_name = getattr(legacy_student, "first_name", None)
        last_name = getattr(legacy_student, "last_name", None)
        dob = getattr(legacy_student, "dob", None) or getattr(legacy_student, "date_of_birth", None)

        if first_name and last_name and dob:
            matches = CoreStudent.objects.filter(
                school=school,
                first_name=first_name,
                last_name=last_name,
                dob=dob,
            )
            if matches.count() == 1:
                return matches.get()

    raise ImproperlyConfigured(
        "Aftercare legacy student_id could not be resolved to core.Student. "
        "Populate aftercare student canonical mapping before posting finance or discipline records."
    )


def _resolve_payer_user(student: CoreStudent) -> UserAccount:
    family = getattr(student, "family", None)
    if family is None:
        raise ImproperlyConfigured("core.Student has no family; cannot create finance obligation.")

    guardians = family.guardians.filter(portal_access=True).order_by("last_name", "first_name")
    if not guardians.exists():
        guardians = family.guardians.all().order_by("last_name", "first_name")

    for guardian in guardians:
        user = UserAccount.objects.filter(school=student.school, guardian=guardian, is_active=True).first()
        if user:
            return user

    raise ImproperlyConfigured(
        "No active payer UserAccount found for student's family guardians. "
        "Create/link a guardian portal account before posting Aftercare finance obligations."
    )


def _academic_year_label(student: CoreStudent) -> str:
    enrollment = student.enrollments.select_related("academic_year").order_by("-academic_year__start_date").first()
    if enrollment and enrollment.academic_year:
        return enrollment.academic_year.name
    return ""


@transaction.atomic
def create_aftercare_finance_obligation(school_id: int, student_id: int, amount_cents: int, description: str) -> int:
    if amount_cents <= 0:
        raise ValueError("amount_cents must be positive for an Aftercare finance obligation.")

    school = _resolve_school_from_aftercare(school_id)
    student = _resolve_core_student_from_aftercare(school, school_id, student_id)
    payer = _resolve_payer_user(student)

    obligation = FinanceObligation.objects.create(
        school=school,
        payer_user=payer,
        obligation_type=ObligationType.FEE,
        status=MoneyStatus.OPEN,
        description=description[:255],
        due_date=timezone.localdate(),
        amount_cents=amount_cents,
        currency="USD",
        academic_year_label=_academic_year_label(student),
        reference=f"aftercare:{school_id}:{student_id}:{timezone.now().strftime('%Y%m%d%H%M%S')}",
    )
    return int(obligation.id)


@transaction.atomic
def create_aftercare_discipline_incident(school_id: int, student_id: int, description: str, severity: str):
    school = _resolve_school_from_aftercare(school_id)
    student = _resolve_core_student_from_aftercare(school, school_id, student_id)

    normalized_severity = {
        "MINOR": "minor",
        "MODERATE": "moderate",
        "MAJOR": "major",
        "minor": "minor",
        "moderate": "moderate",
        "major": "major",
    }.get(severity, "minor")

    incident = DisciplineIncident.objects.create(
        school=school,
        student=student,
        occurred_at=timezone.now(),
        location="Aftercare",
        category="other",
        severity=normalized_severity,
        status="open",
        summary=description[:180],
        details=description,
        parent_notified=False,
    )
    DisciplineAction.objects.create(
        incident=incident,
        action_type="created",
        note="Created automatically from Aftercare incident workflow.",
    )
    return incident.id
'''
write(integrations_path, integrations)


# ---------------------------------------------------------------------------
# Replace fake Aftercare hook returns.
# ---------------------------------------------------------------------------
services_path = "backend/aftercare/services.py"
require(services_path)
services = read(services_path)

start = services.find("def create_ledger_charge_aftercare")
end = services.find("# ---------------------------------------------------------------------------\n# Core actions")
if start == -1 or end == -1 or end <= start:
    raise RuntimeError("could not locate Aftercare stub block in services.py")

replacement = '''def create_ledger_charge_aftercare(school_id: int, student_id: int, amount_cents: int, description: str) -> int:
    """
    Real Aftercare -> Finance hook.

    Creates a FinanceObligation and returns its ID.
    Fails closed if canonical school/student/payer mapping is missing.
    """
    from .integrations import create_aftercare_finance_obligation

    return create_aftercare_finance_obligation(
        school_id=school_id,
        student_id=student_id,
        amount_cents=amount_cents,
        description=description,
    )


def create_discipline_record_for_incident(school_id: int, student_id: int, description: str, severity: str):
    """
    Real Aftercare -> Discipline hook.

    Creates a DisciplineIncident and returns its UUID.
    Fails closed if canonical school/student mapping is missing.
    """
    from .integrations import create_aftercare_discipline_incident

    return create_aftercare_discipline_incident(
        school_id=school_id,
        student_id=student_id,
        description=description,
        severity=severity,
    )


'''
services = services[:start] + replacement + services[end:]
write(services_path, services)

print("Production readiness remediation patch applied. Now run makemigrations and verification.")
