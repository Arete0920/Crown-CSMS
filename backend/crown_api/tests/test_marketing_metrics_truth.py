import pytest
from django.test import Client

from applications.models import Application, Applicant, ApplicationEvent
from core.models import CrownPermission, RolePermission, School, UserAccount, UserRole
from households.models import Household

pytestmark = pytest.mark.django_db


def _grant_marketing_view(user, school):
    role_code = "marketing_truth_tester"
    UserRole.objects.create(user=user, school=school, role_code=role_code)
    permission, _ = CrownPermission.objects.get_or_create(code="marketing.view")
    RolePermission.objects.get_or_create(role_code=role_code, permission=permission)


def test_marketing_metrics_are_tenant_scoped_and_admissions_derived():
    school = School.objects.create(name="Marketing Truth School")
    other_school = School.objects.create(name="Other Marketing School")
    user = UserAccount.objects.create_user(
        username="marketing-truth",
        email="marketing-truth@example.com",
        password="pass12345",
    )
    _grant_marketing_view(user, school)

    household = Household.objects.create(school_id=school.id, name="Truth Household")
    application = Application.objects.create(
        school_id=school.id,
        household=household,
        status="SUBMITTED",
    )
    Applicant.objects.create(
        school_id=school.id,
        application=application,
        first_name="Avery",
        last_name="Truth",
        grade_applying_for="6",
        source="Church Referral",
    )
    ApplicationEvent.objects.create(
        school_id=school.id,
        application=application,
        event_type="inquiry_created",
    )
    ApplicationEvent.objects.create(
        school_id=school.id,
        application=application,
        event_type="tour_scheduled",
    )
    ApplicationEvent.objects.create(
        school_id=school.id,
        application=application,
        event_type="enrollment_confirmed",
    )

    other_household = Household.objects.create(school_id=other_school.id, name="Other Household")
    other_application = Application.objects.create(
        school_id=other_school.id,
        household=other_household,
        status="SUBMITTED",
    )
    Applicant.objects.create(
        school_id=other_school.id,
        application=other_application,
        first_name="Other",
        last_name="Family",
        source="Paid Social",
    )
    ApplicationEvent.objects.create(
        school_id=other_school.id,
        application=other_application,
        event_type="inquiry_created",
    )

    client = Client()
    client.force_login(user)
    response = client.get(
        "/api/v1/marketing/metrics/",
        HTTP_X_SCHOOL_ID=str(school.id),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["inquiries"] == 1
    assert payload["tours_scheduled"] == 1
    assert payload["applications"] == 1
    assert payload["enrolled"] == 1
    assert payload["overall_application_to_enrollment_pct"] == 100.0
    assert payload["source_attribution"] == [
        {
            "source": "Church Referral",
            "applications": 1,
            "enrolled": 1,
            "conversion_pct": 100.0,
        }
    ]
    assert payload["market_intelligence"]["status"] == "not_configured"
    assert payload["advertising"]["status"] == "not_configured"
    assert payload["_meta"]["source"] == "live"
    assert payload["_meta"]["scope"] == "tenant"


def test_captured_inquiries_preserve_family_denominator_and_tenant_scope():
    from datetime import timedelta
    from django.utils import timezone
    from crm_marketing.models import MarketingLead

    school = School.objects.create(name="Inquiry Metrics School")
    other = School.objects.create(name="Other Inquiry Metrics School")
    user = UserAccount.objects.create_user(username="inquiry-metrics", email="metrics@example.com")
    _grant_marketing_view(user, school)
    now = timezone.now()
    open_inquiry = MarketingLead.objects.create(
        school=school, inquiry_received_at=now, first_source="Church referral",
        next_follow_up_at=now - timedelta(hours=1),
    )
    MarketingLead.objects.create(
        school=other, inquiry_received_at=now, first_source="Other school only",
    )
    household = Household.objects.create(school_id=school.id, name="Two children")
    draft = Application.objects.create(school_id=school.id, household=household, status="DRAFT")
    open_inquiry.application = draft
    open_inquiry.save(update_fields=["application"])
    open_inquiry.applications.add(draft)
    children = [Application.objects.create(school_id=school.id, household=household, status="SUBMITTED") for _ in range(2)]
    submitted = MarketingLead.objects.create(
        school=school, inquiry_received_at=now, application_started_at=now,
        first_source="Church referral", stage="application_submitted", application=children[0],
    )
    submitted.applications.add(*children)
    for app in children:
        ApplicationEvent.objects.create(school_id=school.id, application=app, event_type="inquiry_created")
        ApplicationEvent.objects.create(school_id=school.id, application=app, event_type="enrollment_confirmed")
    legacy = Application.objects.create(school_id=school.id, household=household, status="SUBMITTED")
    ApplicationEvent.objects.create(school_id=school.id, application=legacy, event_type="inquiry_created")

    client = Client()
    client.force_login(user)
    response = client.get("/api/v1/marketing/metrics/", HTTP_X_SCHOOL_ID=str(school.id))
    assert response.status_code == 200
    data = response.json()
    assert data["inquiry_capture"] == {
        "captured": 2, "active": 1, "unassigned": 1, "followups_due": 1,
        "application_started": 1, "application_submitted": 1, "enrolled": 1,
        "unit": "family_inquiry", "enrollment_basis": "at_least_one_confirmed_application",
        "legacy_inquiry_applications": 1,
    }
    assert data["inquiry_source_attribution"] == [{
        "source": "Church referral", "inquiries": 2, "families_applied": 1,
        "families_enrolled": 1, "applications": 2, "confirmed_applications": 2,
        "inquiry_to_application_pct": 50.0, "inquiry_to_enrollment_pct": 50.0,
    }]
    assert data["applications"] == 3
    assert data["enrolled"] == 2
    assert data["action_queue"][0]["href"] == "/admissions/inquiries"
    assert "Other school only" not in response.content.decode()
