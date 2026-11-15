"""Existing fictional accepted-applicant fixture under independent presenter scope."""
from django.core.management.base import CommandError
from django.db import transaction
from admissions.models import AdmissionsApplication
from core.models import UserAccount
from .admissions_conversion_seed import seed_fictional_admissions_conversion
from .universal_runtime import require_presenter_runtime
from .universal_demo import _owned_school
from .universal_identity import presenter_username
from .models import SandboxEvent


def prepare_presenter_admissions(*, apply=False):
    require_presenter_runtime()
    with transaction.atomic():
        school = _owned_school()
        if school is None:
            raise CommandError("Prepare the owned fictional presenter first.")
        if AdmissionsApplication.objects.filter(school=school).exists():
            raise CommandError("Existing admissions state is retained; no reset or overwrite allowed.")
        director = UserAccount.objects.get(school=school, username=presenter_username("admissions_director"),
            is_active=True, is_staff=False, is_superuser=False)
        from core.permissions import user_has_permission
        if not user_has_permission(director, "admissions.edit", school=school):
            raise CommandError("Existing approved registrar permission catalog required; no grants changed.")
        result = {"mode": "PREFLIGHT", "school_id": str(school.pk), "release_certified": False}
        if not apply:
            return result
        result.update(seed_fictional_admissions_conversion(school, director))
        SandboxEvent.objects.create(event="universal_presenter_admissions_staged_v1", school=str(school.pk),
                                   track="school", guidance="ops", persona="operator")
        return {**result, "mode": "STAGED"}
