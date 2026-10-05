import pytest
from decimal import Decimal

from core.models import School
from academics.models import Course, Enrollment, Section
from households.models import Household, Student
from billing.models import (
    BillingPayer,
    BillingResponsibilityRule,
    BillingRun,
    Invoice,
    InvoicePayerShare,
)
from billing.services import create_tuition_billing_run


pytestmark = pytest.mark.django_db


def _enrolled_student(*, school, household, amount_term="2026-FALL"):
    student = Student.objects.create(
        school_id=school.id,
        household=household,
        first_name="Alex",
        last_name="Student",
        grade_level="7",
        is_active=True,
    )
    course = Course.objects.create(school_id=school.id, code="MATH7", name="Math 7")
    section = Section.objects.create(
        school_id=school.id,
        course=course,
        term=amount_term,
        teacher_name="Teacher",
        grade_band="7",
    )
    Enrollment.objects.create(school_id=school.id, section=section, student=student)
    return student


def _payer(*, school, household, name):
    return BillingPayer.objects.create(
        school_id=school.id,
        household=household,
        payer_type=BillingPayer.PayerType.THIRD_PARTY,
        display_name=name,
    )


def test_household_responsibility_splits_invoice_without_splitting_ledger_truth():
    school = School.objects.create(name="Split Payer School")
    household = Household.objects.create(school_id=school.id, name="Family")
    _enrolled_student(school=school, household=household)

    payer_a = _payer(school=school, household=household, name="Parent A")
    payer_b = _payer(school=school, household=household, name="Parent B")
    BillingResponsibilityRule.objects.create(
        school_id=school.id,
        household=household,
        payer=payer_a,
        charge_type="TUITION",
        percentage_bps=6000,
    )
    BillingResponsibilityRule.objects.create(
        school_id=school.id,
        household=household,
        payer=payer_b,
        charge_type="TUITION",
        percentage_bps=4000,
    )

    create_tuition_billing_run(
        school_id=school.id,
        term="2026-FALL",
        amount_per_student=Decimal("1000.01"),
    )

    invoice = Invoice.objects.get()
    shares = {
        share.payer_id: share.amount
        for share in InvoicePayerShare.objects.filter(invoice=invoice)
    }

    assert invoice.total_amount == Decimal("1000.01")
    assert sum(shares.values(), Decimal("0.00")) == invoice.total_amount
    assert shares[payer_a.id] == Decimal("600.00")
    assert shares[payer_b.id] == Decimal("400.01")
    assert invoice.ledger_charge_id is not None


def test_student_specific_rules_override_household_default_rules():
    school = School.objects.create(name="Student Override School")
    household = Household.objects.create(school_id=school.id, name="Family")
    student = _enrolled_student(school=school, household=household)

    payer_a = _payer(school=school, household=household, name="Default Payer")
    payer_b = _payer(school=school, household=household, name="Student Payer")

    BillingResponsibilityRule.objects.create(
        school_id=school.id,
        household=household,
        payer=payer_a,
        charge_type="TUITION",
        percentage_bps=10000,
    )
    BillingResponsibilityRule.objects.create(
        school_id=school.id,
        household=household,
        payer=payer_b,
        student=student,
        charge_type="TUITION",
        percentage_bps=10000,
    )

    create_tuition_billing_run(
        school_id=school.id,
        term="2026-FALL",
        amount_per_student=Decimal("500.00"),
    )

    invoice = Invoice.objects.get()
    shares = list(InvoicePayerShare.objects.filter(invoice=invoice))
    assert len(shares) == 1
    assert shares[0].payer_id == payer_b.id
    assert shares[0].amount == Decimal("500.00")


def test_no_responsibility_rules_preserves_existing_household_billing_behavior():
    school = School.objects.create(name="Legacy Billing School")
    household = Household.objects.create(school_id=school.id, name="Family")
    _enrolled_student(school=school, household=household)

    create_tuition_billing_run(
        school_id=school.id,
        term="2026-FALL",
        amount_per_student=Decimal("750.00"),
    )

    invoice = Invoice.objects.get()
    assert invoice.total_amount == Decimal("750.00")
    assert InvoicePayerShare.objects.filter(invoice=invoice).count() == 0
    assert invoice.ledger_charge_id is not None


def test_incomplete_responsibility_percentages_roll_back_billing_run():
    school = School.objects.create(name="Invalid Split School")
    household = Household.objects.create(school_id=school.id, name="Family")
    _enrolled_student(school=school, household=household)

    payer = _payer(school=school, household=household, name="Partial Payer")
    BillingResponsibilityRule.objects.create(
        school_id=school.id,
        household=household,
        payer=payer,
        charge_type="TUITION",
        percentage_bps=9000,
    )

    with pytest.raises(ValueError, match="total 10000 basis points"):
        create_tuition_billing_run(
            school_id=school.id,
            term="2026-FALL",
            amount_per_student=Decimal("1000.00"),
        )

    assert BillingRun.objects.count() == 0
    assert Invoice.objects.count() == 0
    assert InvoicePayerShare.objects.count() == 0
