"""Operator-only local staging of existing fictional care/Camp workflows."""
from decimal import Decimal
from django.core.management.base import CommandError
from django.db import transaction
from django.utils import timezone
from aftercare.models import AftercareEnrollment, AftercarePickupContact, AftercareProgramConfig
from core.models import StudentIdentityLink, UserAccount
from .fictional_care import seed_care_entitlements, seed_daycare_records
from .heritage_module_samples import SAMPLE_CARE_DAYS
from .models import SandboxEvent
from .services import _seed_fictional_camp
from .universal_demo import _owned_school
from .universal_runtime import require_presenter_runtime
from .universal_identity import presenter_username


def prepare_presenter_care(*, apply=False):
    require_presenter_runtime()
    with transaction.atomic():
        school = _owned_school()
        if school is None:
            raise CommandError("Prepare the owned local presenter before care staging.")
        # Reuse the hosted fixture's refusal to repurpose any operational
        # tenant/subscription; never renew suspended/expired entitlements.
        from .management.commands.provision_hosted_buyer_care_entitlements import _assert_empty
        from .management.commands.seed_hosted_buyer_daycare import _empty_synthetic_care
        _assert_empty(school)
        _empty_synthetic_care(school)
        if AftercareEnrollment.objects.filter(school_fk=school).exists() or AftercareProgramConfig.objects.filter(school_fk=school).exists():
            raise CommandError("Existing care configuration cannot be overwritten.")
        actors = {key: UserAccount.objects.get(school=school, username=presenter_username(key, school.pk),
            is_active=True, is_staff=False, is_superuser=False)
            for key in ("daycare_director", "daycare_staff")}
        learner = UserAccount.objects.get(school=school, username=presenter_username("student", school.pk))
        link = StudentIdentityLink.objects.select_related("compatibility_student__household").get(
            school=school, compatibility_student__account=learner,
            verification_status=StudentIdentityLink.STATUS_VERIFIED)
        child = link.compatibility_student
        if child.school_id != school.pk or child.household.school_id != school.pk:
            raise CommandError("Care learner requires the same-school canonical household.")
        result = {"mode": "PREFLIGHT", "school_id": str(school.pk), "release_certified": False}
        if not apply:
            return result
        seed_care_entitlements(school)
        result.update(seed_daycare_records(school, actors))
        AftercareProgramConfig.objects.create(school_fk=school, late_fee_per_10_min=Decimal("0.00"), late_fee_cap=Decimal("0.00"))
        for session in ("AM", "PM"):
            AftercareEnrollment.objects.create(school_fk=school, student_fk=child,
                care_session=session, start_date=timezone.localdate() - timezone.timedelta(days=1),
                days_of_week=list(SAMPLE_CARE_DAYS), billing_model="FLAT_MONTHLY",
                monthly_rate=Decimal("0.00"), is_active=True)
        AftercarePickupContact.objects.create(school_fk=school, student_fk=child,
            name="Miriam Reed", relationship="FICTIONAL PARENT", notes="Fictional presenter custody exercise only")
        result.update(_seed_fictional_camp(school, child))
        SandboxEvent.objects.create(event="universal_presenter_care_staged_v1", school=str(school.pk),
                                   track="school", guidance="ops", persona="operator")
        result.update(mode="STAGED", care_student_id=str(child.pk))
        return result
