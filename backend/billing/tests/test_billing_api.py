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


def test_invoices_list_endpoint_returns_200():
    """D3 Gate: GET /api/billing/invoices/ returns 200 for authenticated user."""
    school = School.objects.create(name="Test School")
    user = _mk_user_with_school(school)
    
    # Create test invoice data
    hh = Household.objects.create(school_id=school.id, name="Test Household")
    billing_run = BillingRun.objects.create(
        school_id=school.id,
        term="2026-TEST",
        amount_per_student=500.00
    )
    Invoice.objects.create(
        school_id=school.id,
        household=hh,
        billing_run=billing_run,
        total_amount=500.00,
        due_on="2026-03-01"
    )
    
    c = Client()
    c.force_login(user)
    
    resp = c.get(
        "/api/billing/invoices/",
        **{"HTTP_X_SCHOOL_ID": str(school.id)}
    )
    
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["household_name"] == "Test Household"
    assert float(data[0]["total_amount"]) == 500.00


def test_invoices_list_scoped_to_school():
    """D3 Gate: Invoices are scoped to the user's school."""
    school1 = School.objects.create(name="School 1")
    school2 = School.objects.create(name="School 2")
    
    user = _mk_user_with_school(school1)
    
    # Create invoices in both schools
    hh1 = Household.objects.create(school_id=school1.id, name="Household 1")
    hh2 = Household.objects.create(school_id=school2.id, name="Household 2")
    
    billing_run1 = BillingRun.objects.create(school_id=school1.id, term="2026-TEST", amount_per_student=500.00)
    billing_run2 = BillingRun.objects.create(school_id=school2.id, term="2026-TEST", amount_per_student=600.00)
    
    Invoice.objects.create(school_id=school1.id, household=hh1, billing_run=billing_run1, total_amount=500.00, due_on="2026-03-01")
    Invoice.objects.create(school_id=school2.id, household=hh2, billing_run=billing_run2, total_amount=600.00, due_on="2026-03-01")
    
    c = Client()
    c.force_login(user)
    
    resp = c.get(
        "/api/billing/invoices/",
        **{"HTTP_X_SCHOOL_ID": str(school1.id)}
    )
    
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["household_name"] == "Household 1"
