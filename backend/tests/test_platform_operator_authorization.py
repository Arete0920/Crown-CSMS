"""Cross-tenant platform operations require an active platform superuser."""
import uuid

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from core.models import School
from platform_ops.models import AuditEvent, ProvisioningJob
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
        school = School.objects.get(pk=first.data["school_id"])
        self.assertFalse(school.is_active)
        # A newly created tenant must not be accessible before provisioning,
        # even to a valid user assigned to that tenant. This tests the real
        # middleware boundary, not merely model state.
        preactive_staff = get_user_model().objects.create_user(
            username="synthetic-pending-staff",
            school=school,
            is_staff=True,
        )
        pending_response = self.client_for(preactive_staff).get(
            f"/api/v1/onboarding/{school.pk}/progress/",
            HTTP_X_SCHOOL_ID=str(school.pk),
        )
        self.assertEqual(pending_response.status_code, 404)
        # Gradebook is exempt from early tenant-header middleware. Its shared
        # request-school resolver must also reject inactive pending tenants.
        from core.models import UserRole
        UserRole.objects.create(
            school=school, user=preactive_staff, role_code="HEAD_OF_SCHOOL"
        )
        exempt_gradebook = self.client_for(preactive_staff).get(
            "/api/v1/gradebook/sections/",
            HTTP_X_SCHOOL_ID=str(school.pk),
        )
        self.assertEqual(exempt_gradebook.status_code, 404)
        self.assertTrue(School.objects.get(pk=self.school.pk).is_active)

    def test_intake_rejects_untrusted_fields_without_side_effects(self):
        """Reject bad types, unauthorized provider, and unsupported metadata."""
        key = str(uuid.uuid4())
        base = {
            "name": "Synthetic New School",
            "slug": "synthetic-new-school",
            "idempotency_key": key,
        }
        invalid = [
            {"name": ["not-a-string"]},
            {"name": "x" * 256},
            {"name": ""},
            {"slug": 123},
            {"slug": "BAD slug"},
            {"slug": "x" * 129},
            {"domain": {"nested": "value"}},
            {"domain": "https://school.example.test/path"},
            {"domain": "not-a-qualified-domain"},
            {"timezone": "../etc/passwd"},
            {"timezone": True},
            {"plan_code": "unapproved-tier"},
            {"payment_provider": "stripe"},
            {"idempotency_key": False},
            {"internal_notes": "not-permitted"},
            {"stripe_account_id": "not-permitted"},
        ]
        for changes in invalid:
            with self.subTest(changes=changes):
                response = self.client_for(self.owner).post(
                    "/api/platform/schools", {**base, **changes},
                    format="json",
                )
                self.assertEqual(response.status_code, 400)
                self.assertEqual(ProvisioningJob.objects.count(), 0)
                self.assertEqual(School.objects.count(), 2)
                self.assertEqual(TenantProfile.objects.count(), 2)
                self.assertEqual(AuditEvent.objects.count(), 0)

    def test_intake_idempotency_key_rejects_changed_request_and_actor(self):
        """One key must not return another request's school identifiers."""
        key = str(uuid.uuid4())
        payload = {
            "name": "Synthetic Consistent Intake",
            "slug": "synthetic-consistent-intake",
            "idempotency_key": key,
            "payment_provider": "manual",
        }
        first = self.client_for(self.owner).post(
            "/api/platform/schools", payload, format="json"
        )
        self.assertEqual(first.status_code, 201)
        same = self.client_for(self.owner).post(
            "/api/platform/schools",
            {**payload, "domain": "", "plan_code": "starter"},
            format="json",
        )
        self.assertEqual(same.status_code, 200)
        self.assertEqual(same.data["job_id"], first.data["job_id"])
        self.assertEqual(AuditEvent.objects.filter(action="school.created").count(), 1)

        mismatched = self.client_for(self.owner).post(
            "/api/platform/schools",
            {**payload, "name": "Different School"},
            format="json",
        )
        self.assertEqual(mismatched.status_code, 409)
        self.assertNotIn(first.data["school_id"], str(mismatched.data))

        other_owner = get_user_model().objects.create_superuser(
            username="synthetic-second-owner",
            email="another-owner@example.invalid",
            password="synthetic-password-for-tests",
        )
        cross_actor = self.client_for(other_owner).post(
            "/api/platform/schools", payload, format="json",
        )
        self.assertEqual(cross_actor.status_code, 409)
        self.assertNotIn(first.data["job_id"], str(cross_actor.data))
        self.assertEqual(ProvisioningJob.objects.count(), 1)
        self.assertEqual(School.objects.count(), 3)
        self.assertEqual(TenantProfile.objects.count(), 3)
        self.assertEqual(AuditEvent.objects.count(), 1)

    def test_service_idempotency_result_reports_insert_or_replay(self):
        """Legacy callers retain a job; opt-in callers receive insert status."""
        from platform_ops.provisioning import create_school_and_queue_provisioning

        payload = {
            "name": "Synthetic Service Replay",
            "slug": "synthetic-service-replay",
            "idempotency_key": str(uuid.uuid4()),
            "actor_user_id": self.owner.pk,
        }
        first, created = create_school_and_queue_provisioning(
            **payload, return_created=True,
        )
        self.assertTrue(created)
        repeated, created = create_school_and_queue_provisioning(
            **payload, return_created=True,
        )
        self.assertFalse(created)
        self.assertEqual(first.pk, repeated.pk)
        legacy = create_school_and_queue_provisioning(**payload)
        self.assertEqual(legacy.pk, first.pk)
        self.assertEqual(ProvisioningJob.objects.count(), 1)

    def test_service_level_race_replay_returns_200(self):
        """A job inserted after the view's lookup remains an idempotent replay."""
        from unittest.mock import patch

        from platform_ops.provisioning import create_school_and_queue_provisioning

        payload = {
            "name": "Synthetic Concurrent Intake",
            "slug": "synthetic-concurrent-intake",
            "idempotency_key": str(uuid.uuid4()),
        }
        original = create_school_and_queue_provisioning(
            **payload, actor_user_id=self.owner.pk,
        )
        # Simulate a missed preflight lookup. The service's independent
        # database query still sees the previously committed job.
        with patch(
            "platform_ops.models.ProvisioningJob.objects.select_related"
        ) as select_related:
            select_related.return_value.filter.return_value.first.return_value = None
            result = self.client_for(self.owner).post(
                "/api/platform/schools", payload, format="json",
            )
        self.assertEqual(result.status_code, 200)
        self.assertTrue(result.data["idempotent"])
        self.assertEqual(result.data["job_id"], str(original.pk))
        self.assertEqual(ProvisioningJob.objects.count(), 1)
        self.assertEqual(School.objects.count(), 3)

    def test_intake_duplicate_slug_rolls_back_without_orphan_school(self):
        """A unique school slug collision must not create partial records."""
        payload = {
            "name": "Synthetic Intake Existing Slug",
            "slug": "synthetic-one",
            "idempotency_key": str(uuid.uuid4()),
        }
        response = self.client_for(self.owner).post(
            "/api/platform/schools", payload, format="json",
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(School.objects.count(), 2)
        self.assertEqual(ProvisioningJob.objects.count(), 0)
        self.assertEqual(TenantProfile.objects.count(), 2)
        self.assertEqual(AuditEvent.objects.count(), 0)


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
