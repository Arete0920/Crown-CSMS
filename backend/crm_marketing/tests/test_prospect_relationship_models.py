import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from applications.models import Application
from core.models import School
from crm_marketing.models import (
    EnrollmentInterest,
    MarketingLead,
    ProspectContact,
    ProspectGroup,
    ProspectGroupMember,
)
from households.models import Household


pytestmark = pytest.mark.django_db


def test_prospective_siblings_and_entry_years_are_distinct_from_sis():
    school = School.objects.create(name="Provisional relations school")
    lead = MarketingLead.objects.create(school=school)
    group = ProspectGroup.objects.create(school=school, lead=lead, label="Prospect family")
    person = ProspectContact.objects.create(
        school=school, display_name="Morgan", email="MORGAN@example.test",
    )
    ProspectGroupMember.objects.create(school=school, group=group, contact=person)
    siblings = [
        EnrollmentInterest.objects.create(
            school=school, group=group, learner_number=n,
            grade_interest="6", entry_year="2027-2028",
        )
        for n in (1, 2)
    ]
    other_year = EnrollmentInterest.objects.create(
        school=school, group=group, learner_number=1,
        grade_interest="7", entry_year="2028-2029",
    )
    person.refresh_from_db()
    assert person.email == "morgan@example.test"
    assert len({*map(lambda row: row.id, siblings), other_year.id}) == 3
    assert group.members.count() == 1
    assert Household.objects.count() == Application.objects.count() == 0


def test_cross_tenant_prospect_relations_reject_before_save():
    a = School.objects.create(name="First CRM school")
    b = School.objects.create(name="Second CRM school")
    lead_b = MarketingLead.objects.create(school=b)
    with pytest.raises(ValidationError):
        ProspectGroup.objects.create(school=a, lead=lead_b, label="Not ours")
    group_a = ProspectGroup.objects.create(school=a, label="Our prospect group")
    person_b = ProspectContact.objects.create(school=b, display_name="Other person")
    with pytest.raises(ValidationError):
        ProspectGroupMember.objects.create(school=a, group=group_a, contact=person_b)
    with pytest.raises(ValidationError):
        EnrollmentInterest.objects.create(
            school=b, group=group_a, learner_number=1,
            grade_interest="5", entry_year="2027-2028",
        )
    household_b = Household.objects.create(school_id=b.id, name="Other household")
    application_b = Application.objects.create(
        school_id=b.id, household=household_b, status="SUBMITTED",
    )
    with pytest.raises(ValidationError):
        EnrollmentInterest.objects.create(
            school=a, group=group_a, learner_number=1,
            grade_interest="5", entry_year="2027-2028", application=application_b,
        )
    assert EnrollmentInterest.objects.count() == 0


def test_unique_opportunity_per_learner_per_year_and_one_application_link():
    school = School.objects.create(name="Opportunity uniqueness school")
    group = ProspectGroup.objects.create(school=school, label="Prospective family")
    EnrollmentInterest.objects.create(
        school=school, group=group, learner_number=1,
        grade_interest="4", entry_year="2027-2028",
    )
    with pytest.raises(ValidationError):
        EnrollmentInterest.objects.create(
            school=school, group=group, learner_number=1,
            grade_interest="4", entry_year="2027-2028",
        )
    with pytest.raises(ValidationError):
        EnrollmentInterest.objects.create(
            school=school, group=group, learner_number=0,
            grade_interest="4", entry_year="2028-2029",
        )
    EnrollmentInterest.objects.create(
        school=school, group=group, learner_number=1,
        grade_interest="5", entry_year="2028-2029",
    )


def test_same_email_is_not_a_global_identity_key():
    a = School.objects.create(name="Marketing tenant A")
    b = School.objects.create(name="Marketing tenant B")
    x = ProspectContact.objects.create(
        school=a, display_name="Parent One", email="common@example.test",
    )
    y = ProspectContact.objects.create(
        school=a, display_name="Parent Two", email="common@example.test",
    )
    z = ProspectContact.objects.create(
        school=b, display_name="Parent Three", email="common@example.test",
    )
    assert len({x.id, y.id, z.id}) == 3
    assert ProspectContact.objects.filter(school=a).count() == 2


def test_database_uniqueness_still_guards_bulk_create_bypassing_model_save():
    school = School.objects.create(name="Database uniqueness school")
    group = ProspectGroup.objects.create(school=school, label="Family")
    EnrollmentInterest.objects.create(
        school=school, group=group, learner_number=1,
        grade_interest="5", entry_year="2027-2028",
    )
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            EnrollmentInterest.objects.bulk_create([
                EnrollmentInterest(
                    school=school, group=group, learner_number=1,
                    grade_interest="5", entry_year="2027-2028",
                ),
            ])
    assert EnrollmentInterest.objects.count() == 1
