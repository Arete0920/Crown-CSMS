"""Stage fictional Aid budgets and explicit noncash SGO applicant/processor grants."""
from django.core.management.base import CommandError
from django.db import transaction
from core.models import AcademicYear, StudentIdentityLink, UserAccount, UserRole, RolePermission
from aid.models import AidPolicy
from jireh_sgo.models import SGOOrganization, SGOProgram, SGOFamilyGrant, SGOProcessorAssignment
from .universal_demo import require_local_presenter, _owned_school
from .universal_identity import presenter_username
from .models import SandboxEvent
from .management.commands.seed_hosted_jireh_buyer import _seed_fictional_aid_policy


def prepare_presenter_jireh(*, apply=False):
    require_local_presenter()
    with transaction.atomic():
        school = _owned_school()
        if school is None:
            raise CommandError("Prepare the owned presenter before Jireh staging.")
        if AidPolicy.objects.filter(school=school).exists() or SGOFamilyGrant.objects.filter(school_key=school.pk).exists():
            raise CommandError("Existing Jireh state cannot be overwritten or reset.")
        if not all(RolePermission.objects.filter(role_code="AID_DIRECTOR", permission__code=code).exists()
                   for code in ("financial_aid.view", "financial_aid.edit")):
            raise CommandError("Initialize the isolated database's existing seed_permissions catalog before Jireh staging; no grants were changed.")
        parent = UserAccount.objects.select_related("guardian").get(school=school, username=presenter_username("parent"), is_active=True)
        officer = UserAccount.objects.get(school=school, username=presenter_username("finance_director"), is_active=True, is_staff=False, is_superuser=False)
        learner = StudentIdentityLink.objects.select_related("core_student").get(
            school=school, compatibility_student__account__username=presenter_username("student"),
            verification_status=StudentIdentityLink.STATUS_VERIFIED).core_student
        if parent.guardian is None or learner.family_id != parent.guardian.family_id:
            raise CommandError("Verified canonical fictional parent and learner required.")
        year = AcademicYear.objects.get(school=school, is_current=True)
        result = {"mode": "PREFLIGHT", "school_id": str(school.pk), "release_certified": False}
        if not apply:
            return result
        _seed_fictional_aid_policy(school, year)
        UserRole.objects.get_or_create(school=school, user=officer, role_code="AID_DIRECTOR")
        for state, name in (("DE", "Delaware"), ("PA", "Pennsylvania")):
            # Same fictional partner shape as the existing buyer generator;
            # new independently owned records, never real organization access.
            organization = SGOOrganization.objects.create(
                legal_name=f"Fictional External {name} SGO (presenter)", state_of_domicile=state, active=True)
            program = SGOProgram.objects.create(organization=organization, name=f"Fictional {state} Partner 2026",
                code=f"fictional-partner-{state.lower()}", calendar_year=2026,
                funding_source=SGOProgram.PRIVATE, eligibility_rule_version=f"FICTIONAL_{state}_2026_V1")
            SGOFamilyGrant.objects.create(program=program, user=parent, student_key=learner.pk,
                school_key=school.pk, consent_version=f"FICTIONAL_{state}_CONSENT_V1", active=True)
            SGOProcessorAssignment.objects.create(program=program, user=officer, active=True)
        SandboxEvent.objects.create(event="universal_presenter_jireh_staged_v1", school=str(school.pk),
                                   track="school", guidance="ops", persona="operator")
        return {**result, "mode": "STAGED"}
