import uuid
import pytest
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.test import Client

from core.models import School
from households.models import Household, Student
from academics.models import Course, Section, Enrollment
from billing.models import BillingRun, Invoice
from ledger.models import LedgerAccount, Charge, Payment
from ledger.models import Allocation as PaymentAllocation
from financial_aid.models import AidApplication, AidAward, AwardStatus


pytestmark = pytest.mark.django_db


def _mk_user_with_school(school: School):
    User = get_user_model()
    u = User.objects.create_user(username=f"user-{uuid.uuid4()}", password="pass12345!")
    if hasattr(u, "school_id"):
        setattr(u, "school_id", school.id)
        u.save(update_fields=["school_id"])
    return u


def test_disburse_aid_to_billing_run_creates_payment_and_allocation():
    school = School.objects.create(name="Test School")
    hh = Household.objects.create(school_id=school.id, name="Household")

    st = Student.objects.create(
        school_id=school.id,
        household=hh,
        first_name="A",
        last_name="Student",
        grade_level="5",
        is_active=True,
    )

    # enroll
    course = Course.objects.create(school_id=school.id, code="MATH5", name="Math 5")
    sec = Section.objects.create(school_id=school.id, course=course, term="2026-FALL", teacher_name="T", grade_band="5")
    Enrollment.objects.create(school_id=school.id, section=sec, student=st)

    # billing run (direct setup)
    run = BillingRun.objects.create(
        school_id=school.id,
        term="2026-FALL",
        run_type="TUITION",
        description="Run",
        amount_per_student=Decimal("1000.00"),
    )
    inv = Invoice.objects.create(school_id=school.id, billing_run=run, household=hh, total_amount=Decimal("1000.00"))

    acct = LedgerAccount.objects.create(school_id=school.id, household=hh)
    ch = Charge.objects.create(school_id=school.id, account=acct, description="Tuition - 2026-FALL", amount=Decimal("1000.00"))
    inv.ledger_charge_id = ch.id
    inv.save(update_fields=["ledger_charge_id"])

    # award -> approved
    app = AidApplication.objects.create(school_id=school.id, household=hh, academic_year="2026-2027")
    aw = AidAward.objects.create(
        school_id=school.id,
        aid_application=app,
        status=AwardStatus.APPROVED,
        amount_annual=Decimal("400.00"),
    )

    user = _mk_user_with_school(school)
    c = Client()
    c.force_login(user)

    resp = c.post(f"/api/v1/financial-aid/billing-runs/{run.id}/disburse/", data={}, content_type="application/json")
    assert resp.status_code == 200

    pay = Payment.objects.get(account=acct, source="FINANCIAL_AID")
    alloc = PaymentAllocation.objects.get(payment=pay, charge=ch)

    assert Decimal(str(alloc.amount)) == Decimal("400.00")
