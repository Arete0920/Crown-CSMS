"""Bounded owned-generation rollover, preserving immutable history and customer scopes."""
from dataclasses import replace
from uuid import UUID
from django.core.management.base import CommandError
from django.db import transaction
from core.models import School, UserAccount, UserRole
from .models import SandboxEvent
from .catalog import SANDBOX_PERSONAS
from .services import _PRESENTER_BOOTSTRAP_CAPABILITY, seed_fictional_school, proof_metrics
from .academic_seed import seed_heritage_teacher_academics
from .universal_demo import _owned_school
from .universal_identity import (UNIVERSAL_SCHOOL_ID, GENERATION_EVENT, MAX_GENERATION,
    generation_school, generation_number, presenter_username)
from .universal_runtime import require_presenter_runtime
from .universal_access import presenter_passwords, initialize_presenter_passwords
from .universal_family import seed_presenter_family
from .universal_care import prepare_presenter_care
from .universal_jireh import prepare_presenter_jireh
from .universal_admissions import prepare_presenter_admissions


def _assert_no_open_custody(school):
    from aftercare.models import DaycareAttendance, AftercareAttendance
    from summer_camp.models import SummerCampAttendance
    if (DaycareAttendance.objects.filter(school=school, custody_release__isnull=True).exists()
            or AftercareAttendance.objects.filter(school_fk=school, checkout_time__isnull=True).exists()
            or SummerCampAttendance.objects.filter(school=school, checkout_time__isnull=True).exists()):
        raise CommandError("Presenter rollover refused unresolved custody; complete authorized handoff or reconciliation first.")


def rollover_presenter(*, expected_current, request_key, apply=False, enable_password_login=False):
    require_presenter_runtime()
    try:
        expected = UUID(str(expected_current))
        key = UUID(str(request_key))
        if key.version != 4:
            raise ValueError
    except (ValueError, TypeError, AttributeError) as exc:
        raise CommandError("Expected current school UUID and a fresh UUID4 request key required.") from exc
    if enable_password_login and not apply:
        raise CommandError("Credential initialization requires explicit --apply.")
    if apply and not enable_password_login:
        raise CommandError("Rollover requires explicit initialization of new-generation normal login; existing credentials are never rotated.")
    passwords = presenter_passwords() if enable_password_login else {}
    with transaction.atomic():
        # _owned_school locks the stable root, including when it is retired.
        # All concurrent generation decisions therefore serialize on one row.
        current = _owned_school()
        if current is None:
            raise CommandError("An owned presenter generation is required.")
        retry = SandboxEvent.objects.filter(event=GENERATION_EVENT, route=str(key), invite=None).first()
        if retry is not None:
            if retry.tour != str(expected) or retry.school != str(current.pk):
                raise CommandError("Request key belongs to another or superseded rollover.")
            return {"mode": "ALREADY_APPLIED", "school_id": retry.school, "generation": retry.step,
                    "history_retained": True, "release_certified": False}
        if current.pk != expected:
            raise CommandError("Stale presenter school; no rollover or credential changes committed.")
        number = generation_number(current.pk)
        if number >= MAX_GENERATION:
            raise CommandError("Reviewed retained-generation capacity reached; no automatic expansion or history deletion.")
        # Admission services lock these exact active-child rows. Lock before
        # checking custody, then retire them in this transaction so a waiting
        # admission rechecks its active-child predicate after the rollover.
        from households.models import Student as PortalStudent
        from aftercare.models import DaycareChild
        portal_children = list(PortalStudent.objects.select_for_update().filter(school_id=current.pk))
        daycare_children = list(DaycareChild.objects.select_for_update().filter(school=current))
        if any(child.household.school_id != current.pk or
               (child.account_id and child.account.school_id != current.pk) for child in portal_children):
            raise CommandError("Presenter child relationships cross a school boundary; no records retired.")
        _assert_no_open_custody(current)
        accounts = list(UserAccount.objects.select_for_update().filter(school=current))
        if UserRole.objects.select_for_update().filter(user_id__in=[user.pk for user in accounts]).exclude(school=current).exists():
            raise CommandError("Presenter principals have foreign or unscoped role associations; no accounts retired.")
        if any((user.staff_id and user.staff.school_id != current.pk) or
               (user.guardian_id and user.guardian.school_id != current.pk) for user in accounts):
            raise CommandError("Presenter principal relationships cross a school boundary; no accounts retired.")
        expected_names = {presenter_username(key, current.pk) for key in SANDBOX_PERSONAS}
        if ({user.username for user in accounts} != expected_names
                or any(user.is_staff or user.is_superuser for user in accounts)):
            raise CommandError("Presenter principal inventory changed; manual scope review required.")
        spec = generation_school(number + 1)
        if School.objects.filter(pk=spec.id).exists():
            raise CommandError("Reserved next generation already exists; never adopt or overwrite it.")
        result = {"mode": "PREFLIGHT", "previous_school_id": str(current.pk), "school_id": spec.id,
                  "generation": number + 1, "history_retained": True, "release_certified": False}
        if not apply:
            return result
        # No delete, credential hash rewrite, historical role removal or record
        # copy. The new generation is built solely from fictional templates.
        for child in [*portal_children, *daycare_children]:
            child.is_active = False
            child.save(update_fields=["is_active"])
        for user in accounts:
            user.is_active = False
            user.save(update_fields=["is_active"])
        current.is_active = False
        current.save(update_fields=["is_active"])
        new_school = School.objects.create(id=UUID(spec.id), name=spec.name, timezone="America/New_York", is_active=True)
        SandboxEvent.objects.create(event=GENERATION_EVENT, school=spec.id, step=number + 1,
            route=str(key), tour=str(current.pk), track="school", guidance="ops", persona="operator")
        personas = {key: replace(persona, email=presenter_username(key, new_school.pk))
                    for key, persona in SANDBOX_PERSONAS.items()}
        seed_fictional_school(school_spec=spec, personas=personas,
            _presenter_bootstrap_capability=_PRESENTER_BOOTSTRAP_CAPABILITY, _presenter_rebuild=True)
        seed_heritage_teacher_academics(school_id=new_school.pk, teacher_username=presenter_username("teacher", new_school.pk))
        seed_presenter_family(new_school)
        initialize_presenter_passwords(new_school, passwords)
        care = prepare_presenter_care(apply=True)
        prepare_presenter_jireh(apply=True)
        admissions = prepare_presenter_admissions(apply=True)
        return {**result, **proof_metrics(new_school), "mode": "ROLLED_OVER", "care": care, "admissions": admissions,
                "usernames": {key: presenter_username(key, new_school.pk) for key in SANDBOX_PERSONAS}}
