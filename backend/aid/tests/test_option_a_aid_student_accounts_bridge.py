from datetime import date
from decimal import Decimal

import pytest

from aid.models import AidAuditEvent, AidAward, AidBudgetTracker
from aid.services.ledger_bridge import approve_award
from core.models import AcademicYear, Family, HouseholdFamilyLink, School, Student
from finance.models import ChartAccount
from households.models import Household
from ledger.models import Credit, Payment

pytestmark = pytest.mark.django_db


def _fixture(*, linked):
    school = School.objects.create(name="Option A Aid School")
    year = AcademicYear.objects.create(school=school, name="2026-27", start_date=date(2026, 8, 1), end_date=date(2027, 5, 31))
    family = Family.objects.create(school=school, family_name="Doe")
    student = Student.objects.create(school=school, family=family, student_number="S001", first_name="Jane", last_name="Doe", dob=date(2012, 3, 15))
    if linked:
        household = Household.objects.create(school_id=school.id, name="Doe Household")
        HouseholdFamilyLink.objects.create(school=school, household_id=household.id, family=family, source=HouseholdFamilyLink.SOURCE_MANUAL)
    ChartAccount.objects.create(school=school, code="AID", name="Financial Aid", account_type="INCOME")
    AidBudgetTracker.objects.create(school=school, academic_year=year, bucket=AidAward.TYPE_NEED, allocated_cents=1_000_000, awarded_cents=0)
    award = AidAward.objects.create(school=school, academic_year=year, student=student, award_type=AidAward.TYPE_NEED, awarded_cents=25_000)
    return school, award


def _credit_qs(school, award):
    return Credit.objects.filter(school_id=school.id, source=Credit.SOURCE_FINANCIAL_AID, reference=f"aid_award:{award.id}")


def test_approval_dual_writes_financial_aid_as_credit_not_payment():
    school, award = _fixture(linked=True)
    approve_award(award=award, actor_user=None, reason="Option A proof")
    award.refresh_from_db()

    assert _credit_qs(school, award).get().amount == Decimal("250.00")
    assert not Payment.objects.filter(school_id=school.id, source="FINANCIAL_AID").exists()
    assert award.ledger_entry_id is not None
    assert AidAuditEvent.objects.filter(school=school, entity_id=award.id, action="STUDENT_ACCOUNT_CREDIT_POSTED").count() == 1


def test_approval_retry_repairs_credit_without_double_budget_or_duplicate_credit():
    school, award = _fixture(linked=False)
    approve_award(award=award, actor_user=None, reason="First")
    budget = AidBudgetTracker.objects.get(school=school, academic_year=award.academic_year, bucket=award.award_type)
    assert budget.awarded_cents == 25_000
    assert Credit.objects.filter(school_id=school.id).count() == 0
    assert AidAuditEvent.objects.filter(school=school, entity_id=award.id, action="STUDENT_ACCOUNT_CREDIT_DEFERRED").count() == 1

    household = Household.objects.create(school_id=school.id, name="Doe Household")
    HouseholdFamilyLink.objects.create(school=school, household_id=household.id, family=award.student.family, source=HouseholdFamilyLink.SOURCE_MANUAL)
    approve_award(award=award, actor_user=None, reason="Retry after mapping repair")

    budget.refresh_from_db()
    assert budget.awarded_cents == 25_000
    assert _credit_qs(school, award).count() == 1
