"""Cross-tenant platform operations require an active platform superuser."""
import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from core.models import School
from platform_ops.models import ProvisioningJob
from subscriptions.models import Plan, TenantSubscription
from tenants.models import TenantProfile


@override_settings(TENANT_HEADER_REQUIRED=True, CROWN_DEMO_MODE=False)
class PlatformOperatorBoundaryTests(TestCase):
    def setUp(self):
        self.school = School.objects.create(name="Synthetic School One")
        self.other = School.objects.create(name="Synthetic School Two")
        TenantProfile.objects.create(school=self.school, slug="synthetic-one")
        TenantProfile.objects.create(school=self.other, slug="synthetic-two")
        User = get_user_model()
        self.staff = User.objects.create_user(
            username="synthetic-staff", school=self.school, is_staff=True
        )
        self.owner = User.objects.create_superuser(
            username="synthetic-owner", email="owner@example.invalid",
            password="synthetic-password-for-tests"
        )
        self.plan = Plan.objects.create(code="synthetic-basic", name="Synthetic Basic")
        self.other_plan = Plan.objects.create(code="synthetic-second", name="Synthetic Second")
        TenantSubscription.objects.create(school_id=self.other.id, plan=self.plan)

    def client_for(self, user=None):
        client = APIClient()
        if user is not None:
            client.force_authenticate(user=user)
        return client

    def test_staff_cannot_list_all_schools_or_read_cross_school_job(self):
        client = self.client_for(self.staff)
        response = client.get("/api/platform/schools/list")
        self.assertEqual(response.status_code, 403)
        job = ProvisioningJob.objects.create(
            school=self.other, idempotency_key=str(uuid.uuid4())
        )
        response = client.get(f"/api/platform/provisioning/{job.id}")
        self.assertEqual(response.status_code, 403)
        self.assertNotIn(str(self.other.id), str(response.content))

    def test_staff_cannot_create_tenant(self):
        response = self.client_for(self.staff).post(
            "/api/platform/schools",
            {"name": "Forbidden", "slug": "forbidden",
             "idempotency_key": str(uuid.uuid4())}, format="json"
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(ProvisioningJob.objects.count(), 0)

    def test_operator_can_list_and_queue_once_with_no_header(self):
        client = self.client_for(self.owner)
        response = client.get("/api/platform/schools/list")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total"], 2)
        payload = {"name": "Synthetic Intake", "slug": "synthetic-intake",
                   "idempotency_key": str(uuid.uuid4()), "payment_provider": "none"}
        first = client.post("/api/platform/schools", payload, format="json")
        repeat = client.post("/api/platform/schools", payload, format="json")
        self.assertEqual((first.status_code, repeat.status_code), (201, 200))
        self.assertEqual(ProvisioningJob.objects.count(), 1)
        self.assertEqual(first.data["job_id"], repeat.data["job_id"])
        self.assertEqual(first.data["state"], "queued")
        profile = TenantProfile.objects.get(school_id=first.data["school_id"])
        self.assertEqual(profile.status, "pending")

    def test_overview_exposes_only_authorized_database_facts(self):
        """Owner sees actual registry/job counts, never illustrative revenue."""
        TenantProfile.objects.filter(school=self.school).update(status="active")
        ProvisioningJob.objects.create(
            school=self.school,
            idempotency_key=str(uuid.uuid4()),
            state=ProvisioningJob.STATE_FAILED,
            error="Sensitive diagnostic must not leave the API.",
        )
        response = self.client_for(self.owner).get("/api/platform/overview")
        self.assertEqual(response.status_code, 200)
        body = response.data
        self.assertEqual(body["meta"]["data_source"], "live_db")
        self.assertEqual(body["meta"]["scope"], "current_database")
        self.assertEqual(body["schools"]["total"], 2)
        self.assertEqual(body["schools"]["by_status"]["active"], 1)
        self.assertEqual(body["schools"]["by_status"]["pending"], 1)
        self.assertEqual(body["provisioning"]["by_state"]["failed"], 1)
        self.assertEqual(len(body["provisioning"]["recent_jobs"]), 1)
        self.assertNotIn("Sensitive diagnostic", str(body))
        self.assertEqual(
            body["company_finance"]["data_state"], "not_configured"
        )
        self.assertEqual(
            body["external_payments"]["provisioning_policy"], "disabled"
        )

    def test_overview_denies_anonymous_staff_inactive_and_tenant_header(self):
        self.assertIn(
            self.client_for().get("/api/platform/overview").status_code,
            (401, 403),
        )
        self.assertEqual(
            self.client_for(self.staff).get("/api/platform/overview").status_code,
            403,
        )
        self.assertEqual(
            self.client_for(self.owner).get(
                "/api/platform/overview",
                HTTP_X_SCHOOL_ID=str(self.school.id),
            ).status_code,
            400,
        )
        self.owner.is_active = False
        self.owner.save(update_fields=["is_active"])
        self.assertEqual(
            self.client_for(self.owner).get("/api/platform/overview").status_code,
            403,
        )

    def test_tenant_selector_denied_even_for_superuser(self):
        client = self.client_for(self.owner)
        response = client.get(
            "/api/platform/schools/list", HTTP_X_SCHOOL_ID=str(self.school.id)
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "platform_tenant_selector_forbidden")
        response = client.get(
            f"/api/v1/subscriptions/ops/{self.other.id}/",
            HTTP_X_CROWN_SCHOOL_ID="invalid"
        )
        self.assertEqual(response.status_code, 400)

    def test_school_staff_cannot_change_cross_school_subscription(self):
        client = self.client_for(self.staff)
        url = f"/api/v1/subscriptions/ops/{self.other.id}/"
        self.assertEqual(client.get(url).status_code, 403)
        self.assertEqual(
            client.post(url, {"plan_id": self.other_plan.id}, format="json").status_code,
            403
        )
        self.assertEqual(
            TenantSubscription.objects.get(
                school_id=self.other.id, ended_at__isnull=True
            ).plan_id, self.plan.id
        )

    def test_operator_can_update_other_school_subscription(self):
        client = self.client_for(self.owner)
        url = f"/api/v1/subscriptions/ops/{self.other.id}/"
        self.assertEqual(client.get(url).status_code, 200)
        response = client.post(
            url, {"plan_id": self.other_plan.id}, format="json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(
            TenantSubscription.objects.get(
                school_id=self.other.id, ended_at__isnull=True
            ).plan_id, self.other_plan.id
        )

    def test_large_school_directory_paginates_without_repeating_tenants(self):
        """Platform owner can reach schools beyond the initial 50-record page."""
        for index in range(51):
            school = School.objects.create(name=f"Synthetic Expansion {index:03d}")
            TenantProfile.objects.create(
                school=school, slug=f"expansion-{index:03d}"
            )
        client = self.client_for(self.owner)
        first = client.get("/api/platform/schools/list?page=1&per_page=50")
        second = client.get("/api/platform/schools/list?page=2&per_page=50")
        self.assertEqual((first.status_code, second.status_code), (200, 200))
        self.assertEqual(first.data["total"], 53)
        self.assertEqual(second.data["total"], 53)
        self.assertEqual(len(first.data["results"]), 50)
        self.assertEqual(len(second.data["results"]), 3)
        first_ids = {row["school_id"] for row in first.data["results"]}
        second_ids = {row["school_id"] for row in second.data["results"]}
        self.assertFalse(first_ids & second_ids)
        self.assertEqual(len(first_ids | second_ids), 53)
        self.assertEqual(
            client.get("/api/platform/schools/list?page=bad").status_code,
            400,
        )

    def test_inactive_superuser_denied(self):
        self.owner.is_active = False
        self.owner.save(update_fields=["is_active"])
        self.assertEqual(
            self.client_for(self.owner).get("/api/platform/schools/list").status_code,
            403
        )

    def test_similarly_named_path_not_exempt(self):
        response = self.client_for().get("/api/platform-unsafe/list")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "missing_tenant")
        for path in ("/api/platform/undefined-operation", "/api/platform/schools/export"):
            response = self.client_for().get(path)
            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json()["code"], "missing_tenant")

def test_school_bound_superuser_cannot_perform_platform_operations(self):
        """A school-associated Django superuser is not a platform owner."""
        scoped_user = get_user_model().objects.create_superuser(
            username="synthetic-school-superuser",
            email="school-superuser@example.invalid",
            password="synthetic-password-for-tests",
            school=self.school,
        )
        client = self.client_for(scoped_user)
        job = ProvisioningJob.objects.create(
            school=self.other, idempotency_key=str(uuid.uuid4())
        )
        for path in (
            "/api/platform/overview",
            "/api/platform/schools/list",
            f"/api/platform/provisioning/{job.id}",
            f"/api/v1/subscriptions/ops/{self.other.id}/",
        ):
            with self.subTest(path=path):
                self.assertEqual(client.get(path).status_code, 403)

        response = client.post(
            "/api/platform/schools",
            {"name": "Forbidden Cross-Tenant School",
             "slug": "forbidden-cross-tenant",
             "idempotency_key": str(uuid.uuid4())},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(ProvisioningJob.objects.count(), 1)

        response = client.post(
            f"/api/v1/subscriptions/ops/{self.other.id}/",
            {"plan_id": str(self.other_plan.id)},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            TenantSubscription.objects.get(
                school_id=self.other.id, ended_at__isnull=True
            ).plan_id, self.plan.id,
        )
