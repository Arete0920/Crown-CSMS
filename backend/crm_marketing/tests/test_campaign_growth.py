import pytest
from django.utils import timezone

from applications.models import Application
from core.models import AcademicYear, Enrollment, Family, GradeLevel, School, Student
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
        start_date=timezone.datetime(2027, 8, 15).date(),
        end_date=timezone.datetime(2028, 6, 5).date(),
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
            dob=timezone.datetime(2015, 1, 1).date(),
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
