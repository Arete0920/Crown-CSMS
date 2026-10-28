from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from aid.models import AidAuditEvent, AidAward, AidBudgetTracker
from aid.services.ledger_bridge import approve_award
from core.models import AcademicYear, Family, HouseholdFamilyLink, School, Student
from finance.models import ChartAccount
from households.models import Household
from ledger.models import Credit, LedgerAccount, Payment

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


def test_approved_award_retry_rejects_changed_amount_without_reposting_credit():
    school, award = _fixture(linked=True)
    approve_award(award=award, actor_user=None, reason="Initial accepted award")
    award.refresh_from_db()
    original_entry_id = award.ledger_entry_id
    original_credit = _credit_qs(school, award).get()

    # Simulate a subsequent unexpected mutation of the accepted award amount.
    # A previous immutable non-cash credit must not be treated as matching.
    award.awarded_cents = 26_000
    award.save(update_fields=["awarded_cents"])
    with pytest.raises(ValidationError, match="controlled reconciliation"):
        approve_award(award=award, actor_user=None, reason="Invalid replay")

    award.refresh_from_db()
    assert award.ledger_entry_id == original_entry_id
    assert _credit_qs(school, award).count() == 1
    assert _credit_qs(school, award).get().amount == original_credit.amount
    assert not Payment.objects.filter(school_id=school.id, source="FINANCIAL_AID").exists()


def test_approved_award_retry_rejects_voided_credit_without_resurrection():
    school, award = _fixture(linked=True)
    approve_award(award=award, actor_user=None, reason="Initial accepted award")
    from ledger.services import void_account_credit

    original = _credit_qs(school, award).get()
    void_account_credit(credit=original)
    with pytest.raises(ValidationError, match="controlled reconciliation"):
        approve_award(award=award, actor_user=None, reason="Voided credit replay")

    original.refresh_from_db()
    assert original.is_void
    assert _credit_qs(school, award).count() == 1
    assert not Payment.objects.filter(school_id=school.id, source="FINANCIAL_AID").exists()


def test_approval_rejects_family_link_to_other_school_household():
    school, award = _fixture(linked=False)
    other_school = School.objects.create(name="Other school for negative credit")
    foreign_household = Household.objects.create(
        school_id=other_school.id, name="Foreign household",
    )
    HouseholdFamilyLink.objects.create(
        school=school,
        family=award.student.family,
        household_id=foreign_household.id,
        source=HouseholdFamilyLink.SOURCE_MANUAL,
    )

    approve_award(award=award, actor_user=None, reason="Tenant denial check")
    award.refresh_from_db()
    assert award.ledger_entry_id is not None  # Legacy-only migration path retained.
    assert not _credit_qs(school, award).exists()
    assert not Payment.objects.filter(school_id=school.id, source="FINANCIAL_AID").exists()
    assert not LedgerAccount.objects.filter(household_id=foreign_household.id).exists()
    events = AidAuditEvent.objects.filter(
        school=school, entity_id=str(award.id),
        action="STUDENT_ACCOUNT_CREDIT_DEFERRED",
    )
    assert events.count() == 1
    assert events.first().details_json["reason"] == "household_missing_or_wrong_school"


def test_decline_voids_credit_and_reverses_legacy_exactly_once():
    from core.models import LedgerEntry

    school, award = _fixture(linked=True)
    approve_award(award=award, actor_user=None)
    award.refresh_from_db()
    original = award.ledger_entry_id
    award.mark_declined_and_reverse()
    award.refresh_from_db()
    assert award.decision_status == AidAward.DECISION_DECLINED
    credit = _credit_qs(school, award).get()
    assert credit.is_void
    assert LedgerEntry.objects.filter(reversal_of_id=original).count() == 1
    assert sum(LedgerEntry.objects.filter(school=school).values_list("amount_cents", flat=True)) == 0
    budget = AidBudgetTracker.objects.get(school=school, academic_year=award.academic_year, bucket=award.award_type)
    assert budget.awarded_cents == 0
    assert not Payment.objects.filter(school_id=school.id, source="FINANCIAL_AID").exists()

    audit_count = AidAuditEvent.objects.filter(school=school, entity_id=str(award.id)).count()
    award.mark_declined_and_reverse()
    budget.refresh_from_db()
    assert budget.awarded_cents == 0
    assert LedgerEntry.objects.filter(reversal_of_id=original).count() == 1
    assert AidAuditEvent.objects.filter(school=school, entity_id=str(award.id)).count() == audit_count


def test_decline_without_household_link_never_fabricates_credit():
    from core.models import LedgerEntry

    school, award = _fixture(linked=False)
    approve_award(award=award, actor_user=None)
    award.refresh_from_db()
    award.mark_declined_and_reverse()
    assert not _credit_qs(school, award).exists()
    assert LedgerEntry.objects.filter(reversal_of_id=award.ledger_entry_id).count() == 1
    assert AidBudgetTracker.objects.get(school=school, academic_year=award.academic_year, bucket=award.award_type).awarded_cents == 0
    assert not Payment.objects.filter(school_id=school.id, source="FINANCIAL_AID").exists()


def test_decline_fails_closed_for_wrong_tenant_credit_account():
    from unittest.mock import patch

    school, award = _fixture(linked=True)
    approve_award(award=award, actor_user=None)
    award.refresh_from_db()
    with patch("ledger.services.void_account_credit", side_effect=RuntimeError("synthetic void failure")):
        with pytest.raises(RuntimeError, match="synthetic void failure"):
            award.mark_declined_and_reverse()
    award.refresh_from_db()
    assert award.decision_status == AidAward.DECISION_ACCEPTED
    assert not _credit_qs(school, award).get().is_void
    assert AidBudgetTracker.objects.get(school=school, academic_year=award.academic_year, bucket=award.award_type).awarded_cents == 25_000


def test_decline_rolls_back_credit_void_when_legacy_reversal_fails():
    from unittest.mock import patch
    from core.models import LedgerEntry

    school, award = _fixture(linked=True)
    approve_award(award=award, actor_user=None)
    award.refresh_from_db()
    with patch.object(LedgerEntry, "create_reversal", side_effect=RuntimeError("synthetic reversal failure")):
        with pytest.raises(RuntimeError, match="synthetic reversal failure"):
            award.mark_declined_and_reverse()
    award.refresh_from_db()
    assert award.decision_status == AidAward.DECISION_ACCEPTED
    assert not _credit_qs(school, award).get().is_void
    assert AidBudgetTracker.objects.get(school=school, academic_year=award.academic_year, bucket=award.award_type).awarded_cents == 25_000
    assert LedgerEntry.objects.filter(reversal_of_id=award.ledger_entry_id).count() == 0


def test_decline_handles_previously_voided_credit_without_reactivating_it():
    from ledger.services import void_account_credit

    school, award = _fixture(linked=True)
    approve_award(award=award, actor_user=None)
    award.refresh_from_db()
    credit = _credit_qs(school, award).get()
    void_account_credit(credit=credit)
    award.mark_declined_and_reverse()
    credit.refresh_from_db()
    assert credit.is_void
    assert _credit_qs(school, award).count() == 1
    assert not AidAuditEvent.objects.filter(school=school, entity_id=str(award.id), action="STUDENT_ACCOUNT_CREDIT_VOIDED").exists()


def test_decline_foreign_household_mapping_never_creates_foreign_account():
    school, award = _fixture(linked=False)
    other = School.objects.create(name="Other school decline isolation")
    household = Household.objects.create(school_id=other.id, name="Foreign household")
    HouseholdFamilyLink.objects.create(
        school=school,
        family=award.student.family,
        household_id=household.id,
        source=HouseholdFamilyLink.SOURCE_MANUAL,
    )
    approve_award(award=award, actor_user=None)
    award.refresh_from_db()
    award.mark_declined_and_reverse()
    assert not _credit_qs(school, award).exists()
    assert not LedgerAccount.objects.filter(household_id=household.id).exists()
    assert not Payment.objects.filter(school_id=school.id, source="FINANCIAL_AID").exists()


def test_decline_audit_failure_rolls_back_prior_void_and_reversal():
    from unittest.mock import patch
    from core.models import LedgerEntry

    school, award = _fixture(linked=True)
    approve_award(award=award, actor_user=None)
    award.refresh_from_db()
    original_log = AidAuditEvent.log

    def fail_on_decline(**kwargs):
        if kwargs.get("action") == "AWARD_DECLINED":
            raise RuntimeError("synthetic audit failure")
        return original_log(**kwargs)

    with patch.object(AidAuditEvent, "log", side_effect=fail_on_decline):
        with pytest.raises(RuntimeError, match="synthetic audit failure"):
            award.mark_declined_and_reverse()
    award.refresh_from_db()
    assert award.decision_status == AidAward.DECISION_ACCEPTED
    assert not _credit_qs(school, award).get().is_void
    assert LedgerEntry.objects.filter(reversal_of_id=award.ledger_entry_id).count() == 0
    assert AidBudgetTracker.objects.get(school=school, academic_year=award.academic_year, bucket=award.award_type).awarded_cents == 25_000


def test_preexisting_declined_award_reconciles_old_active_credit_once():
    from core.models import LedgerEntry

    school, award = _fixture(linked=True)
    approve_award(award=award, actor_user=None)
    award.refresh_from_db()
    # Reproduce the historical bug without calling the new decline method.
    original = award.ledger_entry
    LedgerEntry.create_reversal(original)
    award.decision_status = AidAward.DECISION_DECLINED
    award.save(update_fields=["decision_status"])
    assert not _credit_qs(school, award).get().is_void

    award.mark_declined_and_reverse()
    assert _credit_qs(school, award).get().is_void
    assert LedgerEntry.objects.filter(reversal_of=original).count() == 1
    assert AidBudgetTracker.objects.get(school=school, academic_year=award.academic_year, bucket=award.award_type).awarded_cents == 0
    audit_count = AidAuditEvent.objects.filter(school=school, entity_id=str(award.id)).count()
    award.mark_declined_and_reverse()
    assert AidAuditEvent.objects.filter(school=school, entity_id=str(award.id)).count() == audit_count


def test_declined_award_cannot_be_reapproved_or_reoffered():
    school, award = _fixture(linked=True)
    approve_award(award=award, actor_user=None)
    award.refresh_from_db()
    award.mark_declined_and_reverse()
    with pytest.raises(ValidationError, match="controlled reinstatement"):
        approve_award(award=award, actor_user=None)
    with pytest.raises(ValidationError, match="controlled reinstatement"):
        award.mark_accepted_and_post()
    with pytest.raises(ValidationError, match="controlled reinstatement"):
        award.mark_offered()
    assert _credit_qs(school, award).get().is_void


@pytest.mark.django_db(transaction=True)
def test_concurrent_declines_are_serialized_on_postgresql():
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    from django.db import close_old_connections, connection
    from core.models import LedgerEntry

    if connection.vendor != "postgresql":
        pytest.skip("PostgreSQL row locking required")
    school, award = _fixture(linked=True)
    approve_award(award=award, actor_user=None)
    award.refresh_from_db()
    barrier = Barrier(2)

    def decline():
        close_old_connections()
        try:
            barrier.wait(timeout=10)
            AidAward.objects.get(pk=award.pk).mark_declined_and_reverse()
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        a = pool.submit(decline)
        b = pool.submit(decline)
        a.result(timeout=30)
        b.result(timeout=30)
    award.refresh_from_db()
    assert award.decision_status == AidAward.DECISION_DECLINED
    assert _credit_qs(school, award).get().is_void
    assert LedgerEntry.objects.filter(reversal_of_id=award.ledger_entry_id).count() == 1
    assert AidBudgetTracker.objects.get(school=school, academic_year=award.academic_year, bucket=award.award_type).awarded_cents == 0
