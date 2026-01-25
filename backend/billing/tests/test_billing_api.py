import uuid
import pytest

from django.contrib.auth import get_user_model
from django.test import Client

from core.models import School
from households.models import Household, Student
from academics.models import Course, Section, Enrollment
from ledger.models import Charge, LedgerAccount
from billing.models import BillingRun, Invoice


pytestmark = pytest.mark.django_db


def _mk_user_with_school(school: School):
    User = get_user_model()
    u = User.objects.create_user(username=f"user-{uuid.uuid4()}", password="pass12345!")
    if hasattr(u, "school_id"):
        setattr(u, "school_id", school.id)
        u.save(update_fields=["school_id"])
    return u


def test_tuition_billing_run_creates_invoices_and_ledger_charge():
    school = School.objects.create(name="Test School")

    hh = Household.objects.create(school_id=school.id, name="Household")
    st1 = Student.objects.create(school_id=school.id, household=hh, first_name="A", last_name="One", grade_level="5", is_active=True)
    st2 = Student.objects.create(school_id=school.id, household=hh, first_name="B", last_name="Two", grade_level="5", is_active=True)

    course = Course.objects.create(school_id=school.id, code="MATH5", name="Math 5")
    sec = Section.objects.create(school_id=school.id, course=course, term="2026-FALL", teacher_name="T", grade_band="5")
    Enrollment.objects.create(school_id=school.id, section=sec, student=st1)
    Enrollment.objects.create(school_id=school.id, section=sec, student=st2)

    user = _mk_user_with_school(school)
    c = Client()
    c.force_login(user)

    resp = c.post(
        "/api/v1/billing/runs/",
        data={"term": "2026-FALL", "amount_per_student": "1000.00"},
        content_type="application/json",
    )
    assert resp.status_code == 201

    assert BillingRun.objects.count() == 1
    assert Invoice.objects.count() == 1

    acct = LedgerAccount.objects.get(household=hh)
    assert Charge.objects.filter(account=acct).count() == 1
