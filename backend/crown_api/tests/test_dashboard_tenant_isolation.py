"""
Dashboard API Tenant Isolation Tests
Tests that all dashboard endpoints enforce tenant context per TENANT_PRIVACY_CANON.md
"""
from decimal import Decimal

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import AcademicYear, Family, School
from admissions.models import AdmissionsApplication
from billing.models import Invoice, BillingRun
from academics.models import Section, Course
from households.models import Household, Student
from ledger.models import Charge, LedgerAccount

User = get_user_model()


class DashboardTenantIsolationTests(TestCase):
    """
    Verify all dashboard endpoints enforce tenant isolation:
    1. Missing tenant → 400
    2. Invalid UUID → 400
    3. Nonexistent school → 404
    4. Wrong tenant (non-staff override) → 404
    5. Correct tenant → 200 with data
    """
    
    def setUp(self):
        # Create two schools for cross-tenant testing
        self.school_a = School.objects.create(
            name="School A"
        )
        self.school_b = School.objects.create(
            name="School B"
        )
        
        # Create users scoped to each school
        self.user_a = User.objects.create_user(
            username="user_a",
            email="a@test.com",
            password="password",
            school_id=self.school_a.id
        )
        self.user_b = User.objects.create_user(
            username="user_b",
            email="b@test.com",
            password="password",
            school_id=self.school_b.id
        )
        
        # Create test data for school A
        self.academic_year_a = AcademicYear.objects.create(
            school=self.school_a,
            name="2026",
            start_date="2026-01-01",
            end_date="2026-12-31"
        )
        self.family_a = Family.objects.create(
            school=self.school_a,
            family_name="Family A"
        )
        self.app_a = AdmissionsApplication.objects.create(
            school=self.school_a,
            academic_year=self.academic_year_a,
            family=self.family_a,
            status="SUBMITTED"
        )
        
        self.household_a = Household.objects.create(
            school_id=self.school_a.id,
            name="Household A"
        )
        self.student_a = Student.objects.create(
            school_id=self.school_a.id,
            household=self.household_a,
            first_name="Alice",
            last_name="Anderson"
        )
        self.ledger_account_a = LedgerAccount.objects.create(
            school_id=self.school_a.id,
            household=self.household_a,
        )
        Charge.objects.create(
            school_id=self.school_a.id,
            account=self.ledger_account_a,
            description="Tenant finance proof",
            amount=Decimal("1000.00"),
        )
        
        self.billing_run_a = BillingRun.objects.create(
            school_id=self.school_a.id,
            term="2026-SPRING"
        )
        self.invoice_a = Invoice.objects.create(
            school_id=self.school_a.id,
            billing_run=self.billing_run_a,
            household=self.household_a,
            total_amount=Decimal("1000.00")
        )
        
        self.course_a = Course.objects.create(
            school_id=self.school_a.id,
            code="MATH101",
            name="Math 101"
        )
        self.section_a = Section.objects.create(
            school_id=self.school_a.id,
            course=self.course_a,
            term="2026-SPRING"
        )
        
        # Create test data for school B (to prove isolation)
        self.academic_year_b = AcademicYear.objects.create(
            school=self.school_b,
            name="2026",
            start_date="2026-01-01",
            end_date="2026-12-31"
        )
        self.family_b = Family.objects.create(
            school=self.school_b,
            family_name="Family B"
        )
        self.app_b = AdmissionsApplication.objects.create(
            school=self.school_b,
            academic_year=self.academic_year_b,
            family=self.family_b,
            status="UNDER_REVIEW"
        )
        
        self.client = APIClient()
    
    # ===== Admissions Funnel Tests =====
    
    def test_admissions_funnel_missing_tenant_returns_400(self):
        """Missing X-School-Id header → 400 (dashboards require explicit tenant)."""
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get("/api/v1/dashboards/admissions/funnel/")
        self.assertEqual(response.status_code, 400)
    
    def test_admissions_funnel_invalid_uuid_returns_400(self):
        """Invalid UUID in X-School-Id → 400"""
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(
            "/api/v1/dashboards/admissions/funnel/",
            HTTP_X_SCHOOL_ID="not-a-uuid"
        )
        self.assertEqual(response.status_code, 400)

    def test_admissions_funnel_nonexistent_school_returns_404(self):
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(
            "/api/v1/dashboards/admissions/funnel/",
            HTTP_X_SCHOOL_ID="00000000-0000-0000-0000-000000000000",
        )
        self.assertEqual(response.status_code, 404)
    
    def test_admissions_funnel_correct_tenant_returns_200(self):
        """Correct tenant → 200 with school A data only"""
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(
            "/api/v1/dashboards/admissions/funnel/",
            HTTP_X_SCHOOL_ID=str(self.school_a.id)
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["school_id"], str(self.school_a.id))
        
        statuses = {item["status"] for item in response.data["by_stage"]}
        self.assertIn("SUBMITTED", statuses)
        self.assertNotIn("UNDER_REVIEW", statuses)
    
    def test_admissions_funnel_wrong_tenant_returns_empty(self):
        """Non-staff cannot override tenant via header → 404."""
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(
            "/api/v1/dashboards/admissions/funnel/",
            HTTP_X_SCHOOL_ID=str(self.school_b.id)
        )
        self.assertEqual(response.status_code, 404)
    
    # ===== Finance Summary Tests =====
    
    def test_finance_summary_missing_tenant_returns_400(self):
        """Missing X-School-Id header → 400."""
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get("/api/v1/dashboards/finance/summary/")
        self.assertEqual(response.status_code, 400)
    
    def test_finance_summary_correct_tenant_returns_200(self):
        """Correct tenant → 200 with ledger-authoritative financial data."""
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(
            "/api/v1/dashboards/finance/summary/",
            HTTP_X_SCHOOL_ID=str(self.school_a.id)
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["school_id"], str(self.school_a.id))
        self.assertIn(response.data["billed_total"], ["1000", "1000.00"])
        self.assertIn(response.data["paid_total"], ["0", "0.00"])
        self.assertIn(response.data["outstanding_total"], ["1000", "1000.00"])
        self.assertIn(response.data["unapplied_cash_total"], ["0", "0.00"])
    
    def test_finance_summary_wrong_tenant_no_leak(self):
        """Non-staff cannot override tenant via header → 404."""
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(
            "/api/v1/dashboards/finance/summary/",
            HTTP_X_SCHOOL_ID=str(self.school_b.id)
        )
        self.assertEqual(response.status_code, 404)
    
    # ===== Academics Enrollment Tests =====
    
    def test_academics_enrollment_missing_tenant_returns_400(self):
        """Missing X-School-Id header → 400."""
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get("/api/v1/dashboards/academics/enrollment/")
        self.assertEqual(response.status_code, 400)
    
    def test_academics_enrollment_correct_tenant_returns_200(self):
        """Correct tenant → 200 with enrollment data"""
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(
            "/api/v1/dashboards/academics/enrollment/",
            HTTP_X_SCHOOL_ID=str(self.school_a.id)
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["school_id"], str(self.school_a.id))
        self.assertEqual(response.data["active_students"], 1)
        self.assertEqual(response.data["active_sections"], 1)
    
    def test_academics_enrollment_wrong_tenant_no_leak(self):
        """Non-staff cannot override tenant via header → 404."""
        self.client.force_authenticate(user=self.user_a)
        response = self.client.get(
            "/api/v1/dashboards/academics/enrollment/",
            HTTP_X_SCHOOL_ID=str(self.school_b.id)
        )
        self.assertEqual(response.status_code, 404)
