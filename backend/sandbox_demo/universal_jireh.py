"""Stage fictional Aid budgets and explicit noncash SGO applicant/processor grants."""
from django.core.management.base import CommandError
from django.db import transaction
from core.models import AcademicYear, StudentIdentityLink, UserAccount, UserRole, RolePermission
from aid.models import AidPolicy
from jireh_sgo.models import SGOOrganization, SGOProgram, SGOFamilyGrant, SGOProcessorAssignment
from .universal_demo import _owned_school
from .universal_runtime import require_presenter_runtime
from .universal_identity import presenter_username
from .models import SandboxEvent
from .management.commands.seed_hosted_jireh_buyer import _seed_fictional_aid_policy


def prepare_presenter_jireh(*, apply=False, aid_only=False):
    require_presenter_runtime()
    with transaction.atomic():
        school = _owned_school()
        if school is None:
            raise CommandError("Prepare the owned presenter before Jireh staging.")
        if AidPolicy.objects.filter(school=school).exists() or SGOFamilyGrant.objects.filter(school_key=school.pk).exists():
            raise CommandError("Existing Jireh state cannot be overwritten or reset.")
        if not all(RolePermission.objects.filter(role_code="AID_DIRECTOR", permission__code=code).exists()
                   for code in ("financial_aid.view", "financial_aid.edit")):
            raise CommandError("Initialize the isolated database's existing seed_permissions catalog before Jireh staging; no grants were changed.")
        parent = UserAccount.objects.select_related("guardian").get(school=school, username=presenter_username("parent", school.pk), is_active=True)
        officer = UserAccount.objects.get(school=school, username=presenter_username("finance_director", school.pk), is_active=True, is_staff=False, is_superuser=False)
        learner = StudentIdentityLink.objects.select_related("core_student").get(
            school=school, compatibility_student__account__username=presenter_username("student", school.pk),
            verification_status=StudentIdentityLink.STATUS_VERIFIED).core_student
        if parent.guardian is None or learner.family_id != parent.guardian.family_id:
            raise CommandError("Verified canonical fictional parent and learner required.")
        year = AcademicYear.objects.get(school=school, is_current=True)
        result = {"mode": "PREFLIGHT", "school_id": str(school.pk), "release_certified": False}
        if not apply:
            return result
        _seed_fictional_aid_policy(school, year)
        UserRole.objects.get_or_create(school=school, user=officer, role_code="AID_DIRECTOR")
        if aid_only:
            SandboxEvent.objects.create(
                event="universal_presenter_jireh_aid_only_staged_v1", school=str(school.pk),
                track="school", guidance="ops", persona="operator",
            )
            return {**result, "mode": "STAGED", "scope": "FINANCIAL_AID_ONLY"}
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

@transaction.atomic
def stage_owner_fictional_aid_case():
    """Stage an explicitly authorized, synthetic case; never a public API write.

    Invoked only inside the exact-SHA, owner-confirmed, atomic initial presenter
    provision. All transactions use the existing financial-aid business logic.
    No parent/officer is impersonated and no Payment is produced.
    """
    from types import SimpleNamespace
    from aid.hosted_demo_intake import fictional_family_response
    from aid.models import AidApplication, AidAward, AidAuditEvent, AidFinancialProfile
    from aid.services.ledger_bridge import approve_award
    from core.models import Student
    from ledger.models import Credit, Payment
    from .website_presenter import website_financial_aid_ready

    require_presenter_runtime()
    school = _owned_school()
    if school is None:
        raise CommandError("Owned fictional presenter school required.")
    if SandboxEvent.objects.filter(
        event="universal_presenter_jireh_aid_only_staged_v1", school=str(school.pk),
    ).count() != 1 or SGOFamilyGrant.objects.filter(school_key=school.pk).exists():
        raise CommandError("Exact financial-aid-only staging provenance required.")

    parent = UserAccount.objects.select_related("guardian__family").get(
        school=school, username=presenter_username("parent", school.pk),
        is_active=True, is_staff=False, is_superuser=False,
    )
    officer = UserAccount.objects.get(
        school=school, username=presenter_username("finance_director", school.pk),
        is_active=True, is_staff=False, is_superuser=False,
    )
    if not UserRole.objects.filter(
        school=school, user=parent, role_code="PARENT",
    ).exists() or not UserRole.objects.filter(
        school=school, user=officer, role_code="AID_DIRECTOR",
    ).exists():
        raise CommandError("Canonical parent and Aid director roles required.")
    guardian = parent.guardian
    family = guardian.family if guardian else None
    if family is None or family.school_id != school.pk or family.family_name != "Reed Family":
        raise CommandError("Canonical fictional Reed family required.")
    students = list(Student.objects.filter(
        school=school, family=family, status="ACTIVE",
    ).order_by("first_name", "pk"))
    if len(students) != 2 or {
        (student.first_name, student.last_name) for student in students
    } != {("Avery", "Reed"), ("Jordan", "Reed")}:
        raise CommandError("Exactly two fictional Reed students required.")
    year = AcademicYear.objects.get(school=school, is_current=True)
    if (AidApplication.objects.filter(school=school).exists()
            or AidFinancialProfile.objects.filter(school=school).exists()
            or AidAward.objects.filter(school=school).exists()
            or Payment.objects.filter(school_id=school.pk).exists()):
        raise CommandError("Preexisting financial records refuse synthetic staging.")

    # Reuse the fixed-scenario submission path; record the CLI as the source,
    # not a fictitious parent's authenticated decision.
    submitted = fictional_family_response(
        SimpleNamespace(
            method="POST", user=None,
            data={
                "fictional_acknowledged": True,
                "scenario": "fictional_modest",
                "household_size": 4,
                "academic_year_id": str(year.pk),
                "student_ids": [str(student.pk) for student in students],
            },
        ),
        family, school.pk, source="owner_authorized_synthetic_jireh_case",
    )
    if submitted.status_code != 201:
        raise CommandError("Synthetic application staging refused; transaction rolled back.")
    application = AidApplication.objects.get(pk=submitted.data["application"]["id"])
    award = AidAward.objects.create(
        school=school, academic_year=year, student=students[0],
        aid_application=application, award_type=AidAward.TYPE_NEED,
        awarded_cents=25_000, recommended_award_cents=25_000,
        decision_status=AidAward.DECISION_OFFERED,
        explanation_json={
            "source": "owner_authorized_synthetic_jireh_case",
            "synthetic_only": True,
        },
    )
    AidAuditEvent.log(
        school=school, entity_type=AidAuditEvent.ENTITY_AWARD,
        entity_id=award.pk, action="AWARD_STAGED", actor_user=None,
        details={"source": "owner_authorized_synthetic_jireh_case",
                 "synthetic_only": True, "awarded_cents": 25_000},
    )
    approve_award(
        award=award, actor_user=None,
        reason="Synthetic presentation case only; not a real aid decision",
    )
    award.refresh_from_db()
    credit = Credit.objects.filter(
        school_id=school.pk, source=Credit.SOURCE_FINANCIAL_AID,
        reference=f"aid_award:{award.pk}", is_void=False,
    )
    if (award.decision_status != AidAward.DECISION_ACCEPTED
            or award.ledger_entry_id is None or credit.count() != 1
            or Payment.objects.filter(school_id=school.pk).exists()
            or not website_financial_aid_ready(school)):
        raise CommandError("Synthetic case integrity check failed; rolled back.")
    SandboxEvent.objects.create(
        event="universal_presenter_jireh_case_staged_v1",
        school=str(school.pk), track="school", guidance="ops", persona="operator",
    )
    return {"mode": "SYNTHETIC_CASE_STAGED", "case_ready": True,
            "student_count": 2, "award_cents": 25_000,
            "release_certified": False}
