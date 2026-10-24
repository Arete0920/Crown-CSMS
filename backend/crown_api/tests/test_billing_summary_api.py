from datetime import date

from django.test import TestCase
from rest_framework.test import APIClient

from core.models import CrownPermission, Family, HouseholdFamilyLink, RolePermission, School, UserAccount, UserRole
from crown_api.models import Household, HouseholdMember, Invoice, Payment, Person, UserPersonLink
from crown_api.models_households import ROLE_GUARDIAN, ROLE_FINANCIALLY_RESPONSIBLE, ROLE_AUTHORIZED_PICKUP


TEST_AUTH_SECRET = "TestAuthSecret-LocalOnly"

class BillingSummaryApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.school = School.objects.create(name="Test School")

        self.staff_user = UserAccount.objects.create_user(
            username="staffuser",
            email="staff@example.com",
            password=TEST_AUTH_SECRET,
            is_staff=True,
            school=self.school,
        )
        # A staff account's Django flag is not a financial permission grant.
        permission, _ = CrownPermission.objects.get_or_create(code="billing.view")
        RolePermission.objects.get_or_create(
            role_code="FINANCE_DIRECTOR", permission=permission
        )
        UserRole.objects.get_or_create(
            user=self.staff_user, school=self.school, role_code="FINANCE_DIRECTOR"
        )

        self.parent_user = UserAccount.objects.create_user(
            username="parentuser",
            email="parent@example.com",
            password=TEST_AUTH_SECRET,
            is_staff=False,
            school=self.school,
        )

        self.household_a = Household.objects.create(household_name="Household A")
        self.household_b = Household.objects.create(household_name="Household B")
        # The legacy tables have no tenant key. Real compatibility reads
        # require an explicit, unambiguous school-owned family crosswalk.
        self.family_a = Family.objects.create(school=self.school, family_name="Family A")
        self.family_b = Family.objects.create(school=self.school, family_name="Family B")
        HouseholdFamilyLink.objects.create(
            school=self.school, family=self.family_a,
            household_id=self.household_a.id,
            source=HouseholdFamilyLink.SOURCE_MANUAL,
        )
        HouseholdFamilyLink.objects.create(
            school=self.school, family=self.family_b,
            household_id=self.household_b.id,
            source=HouseholdFamilyLink.SOURCE_MANUAL,
        )

        self.parent_person = Person.objects.create(
            first_name="Parent",
            last_name="A",
            email="parent@example.com",
        )
        UserPersonLink.objects.create(user=self.parent_user, person=self.parent_person)
        HouseholdMember.objects.create(
            household=self.household_a,
            person=self.parent_person,
            role=ROLE_GUARDIAN,
            is_primary=False,
        )

        # Household A invoices: one OPEN, one PAID
        Invoice.objects.create(
            household=self.household_a,
            invoice_number="INV-A-0001",
            amount_cents=150000,
            status=Invoice.STATUS_OPEN,
            issued_date=date(2026, 1, 1),
            due_date=date(2026, 2, 1),
        )
        Invoice.objects.create(
            household=self.household_a,
            invoice_number="INV-A-0002",
            amount_cents=150000,
            status=Invoice.STATUS_PAID,
            issued_date=date(2025, 12, 1),
            due_date=date(2026, 1, 1),
        )

        # Household B invoice (OPEN)
        Invoice.objects.create(
            household=self.household_b,
            invoice_number="INV-B-0001",
            amount_cents=200000,
            status=Invoice.STATUS_OPEN,
            issued_date=date(2026, 1, 2),
            due_date=date(2026, 2, 2),
        )

        # Household A payment
        Payment.objects.create(
            household=self.household_a,
            payment_reference="PAY-A-0001",
            amount_cents=150000,
            payment_date=date(2026, 1, 15),
        )

    def test_staff_can_get_household_billing_summary(self):
        self.client.force_login(self.staff_user)
        self.client.credentials(HTTP_X_SCHOOL_ID=str(self.school.pk))

        resp = self.client.get(f"/api/households/{self.household_a.id}/billing/summary/")
        self.assertEqual(resp.status_code, 200)
        body = resp.json()

        self.assertEqual(body["household_id"], str(self.household_a.id))
        self.assertEqual(body["open_balance_cents"], 150000)
        self.assertEqual(body["invoices_count_open"], 1)
        self.assertEqual(body["invoices_count_total"], 2)
        self.assertEqual(body["last_payment_date"], "2026-01-15")

    def test_staff_without_billing_grant_cannot_read_private_finance(self):
        ungranted = UserAccount.objects.create_user(
            username="synthetic-no-billing-grant",
            email="no-billing-grant@example.invalid",
            is_staff=True,
            school=self.school,
        )
        self.client.force_login(ungranted)
        self.client.credentials(HTTP_X_SCHOOL_ID=str(self.school.pk))
        denied = self.client.get(
            f"/api/households/{self.household_a.pk}/billing/summary/"
        )
        self.assertEqual(denied.status_code, 403)
        self.assertNotIn("INV-A-0001", str(denied.content))

    def test_staff_grant_in_other_school_does_not_authorize_finance(self):
        foreign = School.objects.create(name="Synthetic Billing Grant Other School")
        cross_school = UserAccount.objects.create_user(
            username="synthetic-foreign-billing-grant",
            email="foreign-billing-grant@example.invalid",
            is_staff=True,
            school=self.school,
        )
        UserRole.objects.create(
            user=cross_school, school=foreign, role_code="FINANCE_DIRECTOR"
        )
        self.client.force_login(cross_school)
        self.client.credentials(HTTP_X_SCHOOL_ID=str(self.school.pk))
        denied = self.client.get(
            f"/api/households/{self.household_a.pk}/billing/summary/"
        )
        self.assertEqual(denied.status_code, 403)
        self.assertNotIn("INV-A-0001", str(denied.content))

    def test_parent_scoped_and_no_existence_leak(self):
        self.client.force_login(self.parent_user)
        self.client.credentials(HTTP_X_SCHOOL_ID=str(self.school.pk))

        ok = self.client.get(f"/api/households/{self.household_a.id}/billing/summary/")
        self.assertEqual(ok.status_code, 200)

        no = self.client.get(f"/api/households/{self.household_b.id}/billing/summary/")
        self.assertEqual(no.status_code, 404)

    def test_unauth_403(self):
        # IsAuthenticated + JWT configured → DRF emits 401 (not 403) for unauthenticated
        resp = self.client.get(f"/api/households/{self.household_a.id}/billing/summary/", HTTP_X_SCHOOL_ID=str(self.school.id))
        self.assertEqual(resp.status_code, 401)

    def test_recent_invoices_limited_and_contains_invoice_number(self):
        self.client.force_login(self.staff_user)
        self.client.credentials(HTTP_X_SCHOOL_ID=str(self.school.pk))

        resp = self.client.get(f"/api/households/{self.household_a.id}/billing/summary/")
        self.assertEqual(resp.status_code, 200)
        recent = resp.json()["recent_invoices"]

        self.assertLessEqual(len(recent), 5)
        self.assertTrue(any(row["invoice_number"] == "INV-A-0001" for row in recent))




    def test_staff_cannot_view_foreign_or_ambiguous_legacy_finance(self):
        foreign = School.objects.create(name="Synthetic Foreign Finance School")
        foreign_family = Family.objects.create(school=foreign, family_name="Foreign")
        foreign_household = Household.objects.create(household_name="Foreign Household")
        HouseholdFamilyLink.objects.create(
            school=foreign, family=foreign_family,
            household_id=foreign_household.pk,
            source=HouseholdFamilyLink.SOURCE_MANUAL,
        )
        Invoice.objects.create(
            household=foreign_household,
            invoice_number="SYNTH-FOREIGN-001",
            amount_cents=30000,
            status=Invoice.STATUS_OPEN,
        )
        self.client.force_login(self.staff_user)
        self.client.credentials(HTTP_X_SCHOOL_ID=str(self.school.pk))
        foreign_response = self.client.get(
            f"/api/households/{foreign_household.pk}/billing/summary/"
        )
        self.assertEqual(foreign_response.status_code, 404)
        self.assertNotIn("SYNTH-FOREIGN", str(foreign_response.content))

        # An otherwise permitted legacy household that is linked to two
        # schools cannot safely attribute its unowned invoices to either.
        HouseholdFamilyLink.objects.create(
            school=foreign, family=foreign_family,
            household_id=self.household_a.pk,
            source=HouseholdFamilyLink.SOURCE_MANUAL,
        )
        ambiguous = self.client.get(
            f"/api/households/{self.household_a.pk}/billing/summary/"
        )
        self.assertEqual(ambiguous.status_code, 404)
        self.assertNotIn("INV-A-0001", str(ambiguous.content))

    def test_matching_email_without_link_does_not_grant_legacy_billing(self):
        # Use a distinct email from the existing parent to respect the
        # school's unique (school, email) account constraint. The fictional
        # address still matches a separate legacy household Person, proving
        # that email equality cannot substitute for a UserPersonLink.
        email_only = Person.objects.create(
            first_name="Unlinked", last_name="Guardian",
            email="email-only-synthetic@example.invalid",
        )
        HouseholdMember.objects.create(
            household=self.household_a, person=email_only,
            role=ROLE_GUARDIAN, is_primary=False,
        )
        unlinked = UserAccount.objects.create_user(
            username="synthetic-email-only-billing",
            email="email-only-synthetic@example.invalid",
            school=self.school,
        )
        self.client.force_login(unlinked)
        self.client.credentials(HTTP_X_SCHOOL_ID=str(self.school.pk))
        denied = self.client.get(
            f"/api/households/{self.household_a.pk}/billing/summary/"
        )
        self.assertEqual(denied.status_code, 404)
        self.assertNotIn("INV-A-0001", str(denied.content))


    def test_financially_responsible_member_has_billing_only(self):
        person = Person.objects.create(
            first_name="Responsible", last_name="Payer",
            email="synthetic-payer@example.invalid",
        )
        HouseholdMember.objects.create(
            household=self.household_a, person=person,
            role=ROLE_FINANCIALLY_RESPONSIBLE, is_primary=False,
        )
        account = UserAccount.objects.create_user(
            username="synthetic-financial-payer",
            email="synthetic-payer@example.invalid",
            school=self.school,
        )
        UserPersonLink.objects.create(user=account, person=person)
        self.client.force_login(account)
        self.client.credentials(HTTP_X_SCHOOL_ID=str(self.school.pk))
        allowed = self.client.get(
            f"/api/households/{self.household_a.pk}/billing/summary/"
        )
        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(allowed.json()["open_balance_cents"], 150000)
        wrong = self.client.get(
            f"/api/households/{self.household_b.pk}/billing/summary/"
        )
        self.assertEqual(wrong.status_code, 404)

    def test_pickup_member_cannot_inherit_financial_read_authority(self):
        person = Person.objects.create(
            first_name="Pickup", last_name="Only",
            email="pickup-billing@example.invalid",
        )
        HouseholdMember.objects.create(
            household=self.household_a, person=person,
            role=ROLE_AUTHORIZED_PICKUP, is_primary=False,
        )
        account = UserAccount.objects.create_user(
            username="synthetic-pickup-billing",
            email="pickup-billing@example.invalid",
            school=self.school,
        )
        UserPersonLink.objects.create(user=account, person=person)
        self.client.force_login(account)
        self.client.credentials(HTTP_X_SCHOOL_ID=str(self.school.pk))
        denied = self.client.get(
            f"/api/households/{self.household_a.pk}/billing/summary/"
        )
        self.assertEqual(denied.status_code, 404)
        self.assertNotIn("INV-A-0001", str(denied.content))
