from datetime import date, timedelta
import json
from django.utils import timezone

import pytest

from applications.models import Application, ApplicationEvent
from core.models import AcademicYear, CrownPermission, Enrollment, Family, GradeLevel, RolePermission, School, Student, UserAccount, UserRole
from crm_marketing.models import LeadStage, MarketingCampaign, MarketingLead
from crm_marketing.services import build_campaign_snapshot, register_admissions_submit
from enrollment_period_wizard.models import GradeCapacity
from households.models import Household
from spiritual_life.formation_models import PortraitDomain

pytestmark = pytest.mark.django_db


def _year(school):
    return AcademicYear.objects.create(
        school=school,
        name="2027-2028",
        start_date=date(2027, 8, 15),
        end_date=date(2028, 6, 5),
        is_current=True,
    )


def test_capacity_growth_snapshot_connects_capacity_portrait_and_economics():
    school = School.objects.create(name="Capacity Growth School")
    year = _year(school)
    grade = GradeLevel.objects.create(school=school, code="6", label="Grade 6", sort_order=6)
    GradeCapacity.objects.create(
        school=school,
        academic_year=year,
        grade_code="6",
        target_seats=40,
        new_students_allowed=True,
    )
    family = Family.objects.create(school=school, family_name="Existing")
    for index in range(30):
        student = Student.objects.create(
            school=school,
            family=family,
            student_number=f"S-{index}",
            first_name="Student",
            last_name=str(index),
            dob=date(2015, 1, 1),
            status="ACTIVE",
            current_grade_level=grade,
        )
        Enrollment.objects.create(
            school=school,
            student=student,
            academic_year=year,
            grade_level=grade,
            start_date=year.start_date,
            status="ENROLLED",
        )

    portrait = PortraitDomain.objects.create(
        school=school,
        name="Servant Leadership",
        description="Leads with conviction, humility, and service.",
        scripture_anchor="Mark 10:45",
        is_active=True,
    )
    campaign = MarketingCampaign.objects.create(
        school=school,
        academic_year=year,
        name="Grade 6 Capacity Growth",
        campaign_type="capacity_growth",
        status="active",
        target_grade_code="6",
        enrollment_goal=6,
        budget_cents=400000,
        tuition_per_student_cents=1500000,
        expected_retention_years=7,
        portrait_domain_ids=[str(portrait.id)],
        aid_strategy={"planned_aid_per_enrollment_cents": 300000},
    )

    snapshot = build_campaign_snapshot(campaign)

    assert snapshot["capacity"]["target_seats"] == 40
    assert snapshot["capacity"]["current_enrolled"] == 30
    assert snapshot["capacity"]["empty_seats"] == 10
    assert snapshot["portrait"][0]["name"] == "Servant Leadership"
    assert snapshot["economics"]["projected_gross_tuition_cents"] == 9000000
    assert snapshot["economics"]["projected_aid_cents"] == 1800000
    assert snapshot["economics"]["projected_net_first_year_cents"] == 6800000
    assert snapshot["economics"]["projected_lifetime_net_tuition_cents"] == 50000000
    assert snapshot["aid"]["campaign_attribution_verified"] is False
    assert snapshot["economics"]["actual_net_after_aid_cents"] is None


def test_admissions_submit_preserves_existing_campaign_attribution():
    school = School.objects.create(name="CRM Attribution School")
    year = _year(school)
    household = Household.objects.create(school_id=school.id, name="Prospect Household")
    application = Application.objects.create(
        school_id=school.id,
        household=household,
        status="SUBMITTED",
    )
    campaign = MarketingCampaign.objects.create(
        school=school,
        academic_year=year,
        name="Referral Capacity Campaign",
        campaign_type="referral",
        status="active",
    )
    lead = MarketingLead.objects.create(
        school=school,
        campaign=campaign,
        application=application,
        stage=LeadStage.INQUIRY,
        first_source="Parent Referral",
        primary_source="Parent Referral",
    )

    leads = register_admissions_submit(
        application,
        source="Parent Referral",
        start_term=year.name,
    )

    lead.refresh_from_db()
    assert len(leads) == 1
    assert leads[0].id == lead.id
    assert lead.campaign_id == campaign.id
    assert lead.stage == LeadStage.APPLICATION_SUBMITTED
    assert MarketingLead.objects.filter(application=application).count() == 1


def test_campaign_enrollment_requires_canonical_confirmation_and_counts_families_once():
    school = School.objects.create(name="Confirmed Campaign School")
    household = Household.objects.create(school_id=school.id, name="Confirmed Household")
    application = Application.objects.create(school_id=school.id, household=household, status="SUBMITTED")
    campaign = MarketingCampaign.objects.create(school=school, name="Confirmation", tuition_per_student_cents=100000)
    for _ in range(2):
        MarketingLead.objects.create(school=school, campaign=campaign, application=application, stage=LeadStage.ENROLLED,
                                     next_follow_up_at=timezone.now() - timedelta(days=1))
    snapshot = build_campaign_snapshot(campaign)
    assert snapshot["funnel"]["enrolled"] == 0
    assert snapshot["funnel"]["unverified_enrollment_leads"] == 2
    assert snapshot["funnel"]["followups_due"] == 2
    assert snapshot["economics"]["actual_gross_tuition_cents"] is None
    assert snapshot["economics"]["estimated_gross_tuition_from_confirmed_applications_cents"] == 0
    ApplicationEvent.objects.create(school_id=school.id, application=application, event_type="enrollment_confirmed")
    snapshot = build_campaign_snapshot(campaign)
    assert snapshot["funnel"]["enrolled"] == 1
    assert snapshot["funnel"]["unverified_enrollment_leads"] == 0
    assert snapshot["funnel"]["followups_due"] == 0
    assert snapshot["economics"]["actual_gross_tuition_cents"] is None
    assert snapshot["economics"]["estimated_gross_tuition_from_confirmed_applications_cents"] == 100000


@pytest.fixture
def campaign_client(client):
    school = School.objects.create(name="Campaign API School")
    user = UserAccount.objects.create_user(username="campaign-editor", email="campaign-editor@example.com")
    UserRole.objects.create(user=user, school=school, role_code="campaign_editor_test")
    for code in ("marketing.view", "marketing.edit"):
        permission, _ = CrownPermission.objects.get_or_create(code=code)
        RolePermission.objects.get_or_create(role_code="campaign_editor_test", permission=permission)
    client.force_login(user)
    return client, school


@pytest.mark.parametrize("extra", [
    {"academic_year_id": "invalid"},
    {"portrait_domain_ids": "invalid"},
    {"portrait_domain_ids": ["invalid"]},
    {"budget_cents": -1},
    {"budget_cents": 1.5},
    {"budget_cents": True},
    {"budget_cents": 2**63},
    {"enrollment_goal": 2**31},
    {"expected_retention_years": 0},
    {"expected_retention_years": 32768},
    {"aid_strategy": {"planned_aid_per_enrollment_cents": "invalid"}},
    {"aid_strategy": {"planned_aid_per_enrollment_cents": -1}},
    {"aid_strategy": []},
    {"target_segment": []},
])
def test_campaign_rejects_invalid_input_without_persisting(campaign_client, extra):
    client, school = campaign_client
    response = client.post("/api/v1/crm/campaigns/", data=json.dumps({"name": "Invalid", **extra}),
                           content_type="application/json", HTTP_X_SCHOOL_ID=str(school.id))
    assert response.status_code == 400
    assert not MarketingCampaign.objects.filter(school=school).exists()


def test_campaign_creation_and_read_are_tenant_scoped(campaign_client):
    client, school = campaign_client
    response = client.post("/api/v1/crm/campaigns/", data=json.dumps({"name": "Verified", "budget_cents": 100}),
                           content_type="application/json", HTTP_X_SCHOOL_ID=str(school.id))
    assert response.status_code == 201
    campaign_id = response.json()["campaign_id"]
    assert MarketingCampaign.objects.get(id=campaign_id).school_id == school.id
    user = UserAccount.objects.get(username="campaign-editor")
    user.is_superuser = True
    user.save(update_fields=["is_superuser"])
    other_school = School.objects.create(name="Other Campaign School")
    denied = client.get(f"/api/v1/crm/campaigns/{campaign_id}/", HTTP_X_SCHOOL_ID=str(other_school.id))
    assert denied.status_code in (403, 404)
    denied = client.post("/api/v1/crm/campaigns/", data=json.dumps({"name": "Cross-school"}),
                         content_type="application/json", HTTP_X_SCHOOL_ID=str(other_school.id))
    assert denied.status_code in (403, 404)
    assert not MarketingCampaign.objects.filter(school=other_school).exists()
    denied = client.get("/api/v1/marketing/metrics/", HTTP_X_SCHOOL_ID=str(other_school.id))
    assert denied.status_code in (403, 404)


def test_campaign_view_permission_cannot_create(campaign_client):
    client, school = campaign_client
    RolePermission.objects.filter(role_code="campaign_editor_test", permission__code="marketing.edit").delete()
    response = client.post("/api/v1/crm/campaigns/", data=json.dumps({"name": "Read-only"}),
                           content_type="application/json", HTTP_X_SCHOOL_ID=str(school.id))
    assert response.status_code == 403
    assert not MarketingCampaign.objects.filter(school=school).exists()


def test_campaign_touchpoint_persists_only_valid_tenant_lead(campaign_client):
    client, school = campaign_client
    campaign = MarketingCampaign.objects.create(school=school, name="Touchpoint")
    lead = MarketingLead.objects.create(school=school, campaign=campaign)
    url = f"/api/v1/crm/campaigns/{campaign.id}/touchpoints/"
    for lead_id, expected in [("invalid", 400), (str(lead.id), 201)]:
        response = client.post(url, data=json.dumps({"lead_id": lead_id, "channel": "phone", "summary": "Called family"}),
                               content_type="application/json", HTTP_X_SCHOOL_ID=str(school.id))
        assert response.status_code == expected
    touchpoint = campaign.touchpoints.get()
    assert touchpoint.school_id == school.id
    assert touchpoint.lead_id == lead.id
