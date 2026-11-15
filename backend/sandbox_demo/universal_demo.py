"""Local-only presenter foundation. Never a hosted provisioning authority.

Reuse the Heritage generators with explicit identities. No catalog mutation,
customer-data copying, payment provider, authorization exemption or migration.
"""
import os
from dataclasses import replace
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.management.base import CommandError
from django.db import connection, transaction
from django.db.models.deletion import Collector, ProtectedError

from core.models import School
from .academic_seed import seed_heritage_teacher_academics
from .catalog import SANDBOX_PERSONAS, SANDBOX_SCHOOLS
from .models import SandboxBuyerWorkspace, SandboxEvent
from .services import _PRESENTER_BOOTSTRAP_CAPABILITY, proof_metrics, seed_fictional_school
from .universal_identity import UNIVERSAL_SCHOOL, UNIVERSAL_SCHOOL_ID, presenter_username

LOCAL_DB = Path(__file__).resolve().parents[2] / ".local-backups/universal-demo/universal.sqlite3"
PROVENANCE = "universal_presenter_created_v1"

# Explicit reset inventory, children before parents. Unknown future module data
# blocks reset until its lifecycle and custody/audit retention are reviewed.
RESET_MODELS = (
    "core.StudentIdentityLink", "academics.Grade", "academics.Submission",
    "academics.LessonResource", "academics.LessonPlan", "academics.Assignment",
    "academics.AssignmentCategory", "academics.Enrollment", "academics.TeacherAssignment",
    "crown_api.AttendanceRecord", "academics.Section", "academics.Lesson", "academics.Unit", "academics.Course",
    "academics.CurriculumSource", "academics.Term",
    "households.Guardian", "households.Student", "households.Household",
    "finance.FinanceInvoiceLine", "finance.FinanceInvoice", "finance.FinanceObligation",
    "core.UserRole", "core.UserAccount", "core.StudentTuition", "core.Enrollment",
    "core.Student", "core.Guardian", "core.Staff", "core.Family", "core.TuitionPlan",
    "core.GradeLevel", "core.AcademicYear",
)


def require_local_presenter():
    """Check the actual connection as well as configuration, before any query."""
    db = connection.settings_dict
    outbound_disabled = (
        getattr(settings, "CROWN_SANDBOX_OUTBOUND_DISABLED", False) is True
        or os.environ.get("CROWN_SANDBOX_OUTBOUND_DISABLED", "").strip().lower()
        in {"1", "true", "yes", "on"}
    )
    if (
        getattr(settings, "CROWN_ENV", "") != "local" or settings.DEBUG is not True
        or connection.vendor != "sqlite"
        or Path(str(db["NAME"])).resolve() != LOCAL_DB.resolve()
        or getattr(settings, "CROWN_DEMO_MODE", True) is not False
        or getattr(settings, "CROWN_SANDBOX_ALLOW_OPEN_SESSION", True) is not False
        or not outbound_disabled
        or str(SANDBOX_SCHOOLS["heritage-core"].id) == str(UNIVERSAL_SCHOOL_ID)
        or any(os.environ.get(key) for key in (
            "WEBSITE_HOSTNAME", "WEBSITE_INSTANCE_ID", "WEBSITE_SITE_NAME", "IDENTITY_ENDPOINT", "AZURE_CLIENT_ID",
        ))
        or any(str(value or "").strip().lower() not in {"", "local"}
               for key in ("CROWN_ENV", "DJANGO_ENV", "AZURE_ENVIRONMENT", "ENVIRONMENT", "APP_ENV")
               for value in (os.environ.get(key), getattr(settings, key, None)))
    ):
        raise CommandError("Universal presenter requires its dedicated local SQLite runtime with egress disabled and open sessions disabled.")


def _owned_school():
    school = School.objects.select_for_update().filter(pk=UNIVERSAL_SCHOOL_ID).first()
    marker = SandboxEvent.objects.filter(event=PROVENANCE, school=str(UNIVERSAL_SCHOOL_ID), invite=None)
    if school is None:
        if marker.exists():
            raise CommandError("Presenter provenance exists without its school; manual review required.")
        return None
    if (
        school.name != UNIVERSAL_SCHOOL.name or not school.is_active
        or not marker.exists()
        or SandboxBuyerWorkspace.objects.filter(school=school).exists()
    ):
        raise CommandError("Reserved presenter identity is not an owned presenter school.")
    return school


def _scoped(model):
    if model._meta.label == "finance.FinanceInvoiceLine":
        return model.objects.filter(invoice__school_id=UNIVERSAL_SCHOOL_ID)
    if model._meta.label == "crown_api.AttendanceRecord":
        return model.objects.filter(student__school_id=UNIVERSAL_SCHOOL_ID)
    return model.objects.filter(school_id=UNIVERSAL_SCHOOL_ID)


def _assert_owned_rows(rows):
    for row in rows:
        owner = getattr(row, "school_id", None)
        if row._meta.label == "finance.FinanceInvoiceLine":
            owner = row.invoice.school_id
        if row._meta.label == "crown_api.AttendanceRecord":
            owner = row.student.school_id
            if row.section_id and str(row.section.school_id) != str(owner):
                raise CommandError("Presenter reset refused a foreign attendance relationship.")
        if str(owner) != str(UNIVERSAL_SCHOOL_ID):
            raise CommandError("Presenter reset refused an unscoped or foreign cascade/update.")


def _delete_owned(queryset):
    # Django cascades and SET_NULL updates may reach rows outside the root
    # filter. Inspect both, including fast-deletes, before invoking normal ORM
    # deletion. PROTECT remains authoritative. Every step is in one transaction.
    collector = Collector(using=connection.alias)
    collector.collect(queryset)
    for rows in collector.data.values():
        _assert_owned_rows(rows)
    for rows in collector.fast_deletes:
        _assert_owned_rows(rows)
    for groups in collector.field_updates.values():
        for rows in groups:
            _assert_owned_rows(rows)
    queryset.delete()


def _reset():
    allowed = set(RESET_MODELS)
    for model in apps.get_models():
        # Proxy models share the concrete table already covered by inventory.
        if model._meta.proxy:
            continue
        if any(field.attname == "school_id" for field in model._meta.fields):
            if model._meta.label not in allowed and _scoped(model).exists():
                raise CommandError(f"Presenter reset refused unreviewed module records ({model._meta.label}); no data changed.")
    try:
        for label in RESET_MODELS:
            _delete_owned(_scoped(apps.get_model(label)))
    except ProtectedError as exc:
        raise CommandError("Presenter reset refused protected relationships; no data changed.") from exc


def prepare_presenter(*, apply=False, reset=False, enable_password_login=False):
    require_local_presenter()
    if enable_password_login and not apply:
        raise CommandError("Password initialization requires explicit --apply.")
    from .universal_access import presenter_passwords
    passwords = presenter_passwords() if enable_password_login else {}
    return _prepare_presenter(apply=apply, reset=reset, passwords=passwords)


@transaction.atomic
def _prepare_presenter(*, apply, reset, passwords):
    school = _owned_school()
    if reset and (not apply or school is None):
        raise CommandError("Reset requires --apply and an existing owned presenter school.")
    if not apply:
        return {"school_id": str(UNIVERSAL_SCHOOL_ID), "exists": school is not None,
                "mode": "PRECHECK_ONLY", "release_certified": False}
    if school is not None and not reset:
        raise CommandError("Presenter already exists; use an explicit controlled reset, never silently overwrite transactions.")
    if reset:
        _reset()
    personas = {
        key: replace(SANDBOX_PERSONAS[key], email=presenter_username(key))
        for key in SANDBOX_PERSONAS
    }
    metrics = seed_fictional_school(
        school_spec=UNIVERSAL_SCHOOL, personas=personas,
        _presenter_bootstrap_capability=_PRESENTER_BOOTSTRAP_CAPABILITY,
    )
    metrics.update(seed_heritage_teacher_academics(
        school_id=UNIVERSAL_SCHOOL_ID, teacher_username=presenter_username("teacher"),
    ))
    SandboxEvent.objects.create(
        event="universal_presenter_reset_v1" if reset else PROVENANCE,
        school=str(UNIVERSAL_SCHOOL_ID), track="school", guidance="ops", persona="operator",
    )
    from .universal_family import seed_presenter_family
    metrics.update(seed_presenter_family(School.objects.get(pk=UNIVERSAL_SCHOOL_ID)))
    metrics.update(proof_metrics(School.objects.get(pk=UNIVERSAL_SCHOOL_ID)))
    if passwords:
        from .universal_access import initialize_presenter_passwords
        initialize_presenter_passwords(School.objects.get(pk=UNIVERSAL_SCHOOL_ID), passwords)
    return {**metrics, "mode": "RESET" if reset else "CREATED", "release_certified": False}
