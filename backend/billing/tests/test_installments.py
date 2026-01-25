import uuid
from datetime import date
from decimal import Decimal

import pytest

from academics.models import Course, Section, Enrollment
from billing.models import BillingRun, Invoice, InstallmentPlan, InstallmentScheduleItem
from billing.services import create_tuition_billing_run, generate_installments_for_household
from core.models import School
from households.models import Household, Student
from ledger.models import Charge

pytestmark = pytest.mark.django_db


def test_generate_installments_rounding_and_idempotency():
    school = School.objects.create(name="Test School")
    hh = Household.objects.create(school_id=school.id, name="Household")

    plan = InstallmentPlan.objects.create(
        school_id=school.id,
        term="2026-FALL",
        name="3-pay",
        installment_count=3,
        first_due_on=date(2026, 9, 1),
        cadence_days=30,
    )

    items1 = generate_installments_for_household(
        school_id=school.id,
        household_id=hh.id,
        term="2026-FALL",
        plan=plan,
        amount=Decimal("1000.00"),
    )
    assert [Decimal(str(i.amount)) for i in items1] == [Decimal("333.33"), Decimal("333.33"), Decimal("333.34")]

    # Idempotent: second call returns existing, does not create duplicates
    items2 = generate_installments_for_household(
        school_id=school.id,
        household_id=hh.id,
        term="2026-FALL",
        plan=plan,
        amount=Decimal("1000.00"),
    )
    assert len(items2) == 3
    assert InstallmentScheduleItem.objects.filter(school_id=school.id, plan=plan, household=hh).count() == 3


def test_billing_run_creates_multiple_invoices_with_plan():
    school = School.objects.create(name="Test School")
    hh = Household.objects.create(school_id=school.id, name="Household")

    # Students in same household
    st1 = Student.objects.create(school_id=school.id, household=hh, first_name="A", last_name="One")
    st2 = Student.objects.create(school_id=school.id, household=hh, first_name="B", last_name="Two")

    # Minimal academics setup so create_tuition_billing_run can find enrollments
    course = Course.objects.create(school_id=school.id, code=f"C-{uuid.uuid4().hex[:6]}", name="Course")
    section = Section.objects.create(school_id=school.id, course=course, term="2026-FALL")
    Enrollment.objects.create(school_id=school.id, section=section, student=st1)
    Enrollment.objects.create(school_id=school.id, section=section, student=st2)

    plan = InstallmentPlan.objects.create(
        school_id=school.id,
        term="2026-FALL",
        name="3-pay",
        installment_count=3,
        first_due_on=date(2026, 9, 1),
        cadence_days=30,
    )

    result = create_tuition_billing_run(
        school_id=school.id,
        term="2026-FALL",
        amount_per_student=Decimal("1000.00"),
        description="Run",
        installment_plan_id=plan.id,
    )

    run = BillingRun.objects.get(id=result.billing_run_id)
    invoices = Invoice.objects.filter(school_id=school.id, billing_run=run, household=hh).order_by("due_on")
    assert invoices.count() == 3

    # Household total billed = 2 students * 1000 = 2000 (split into 3 invoices)
    assert sum([Decimal(str(i.total_amount)) for i in invoices]) == Decimal("2000.00")

    for inv in invoices:
        assert inv.due_on is not None
        assert inv.ledger_charge_id is not None
        # Charge exists and matches invoice
        ch = Charge.objects.get(id=inv.ledger_charge_id)
        assert Decimal(str(ch.amount)) == Decimal(str(inv.total_amount))
        # Lines sum to invoice total
        line_sum = sum([Decimal(str(l.amount)) for l in inv.lines.all()])
        assert line_sum == Decimal(str(inv.total_amount))
        # 2 students => 2 lines
        assert inv.lines.count() == 2
