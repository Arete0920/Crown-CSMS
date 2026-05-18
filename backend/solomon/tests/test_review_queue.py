"""Governance review queue and filtering tests."""

from __future__ import annotations

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from solomon.models import (
    SolomonAudience,
    SolomonCategory,
    SolomonLifecycle,
    SolomonResource,
    SolomonResourceType,
    SolomonScope,
    SolomonVisibility,
    SolomonTopic,
)
from solomon.services import governance_review_queue, governance_filtered_review_queue
from solomon.services import governance_stale_review_queue


User = get_user_model()


@override_settings(CROWN_SOLOMON_API_ENABLED=True, ROOT_URLCONF="solomon.urls")
class GovernanceReviewQueueTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = SolomonCategory.objects.create(
            name="Test Category",
            slug="test-category",
            is_public=True,
            sort_order=1,
        )
        self.topic = SolomonTopic.objects.create(
            name="Test Topic",
            slug="test-topic",
        )
        self.audience = SolomonAudience.objects.create(
            name="Test Audience",
            slug="test-audience",
            role_code="test",
            is_public=True,
        )

        # Create test users
        self.staff_user = User.objects.create_user(
            username="staff-user",
            password="password",
            is_staff=True,
        )
        self.regular_user = User.objects.create_user(
            username="regular-user",
            password="password",
        )

        # Create resources in different states
        self.draft_resource = SolomonResource.objects.create(
            title="Draft Resource",
            slug="draft-resource",
            summary="Not yet approved",
            resource_type=SolomonResourceType.ARTICLE,
            status=SolomonLifecycle.DRAFT,
            visibility=SolomonVisibility.STAFF,
            scope=SolomonScope.GLOBAL,
            category=self.category,
            module="test",
            sort_order=1,
        )

        self.approved_resource = SolomonResource.objects.create(
            title="Approved Resource",
            slug="approved-resource",
            summary="Ready to publish",
            resource_type=SolomonResourceType.GUIDE,
            status=SolomonLifecycle.APPROVED,
            visibility=SolomonVisibility.STAFF,
            scope=SolomonScope.GLOBAL,
            category=self.category,
            module="test",
            sort_order=2,
        )

        # Normalize created_at to the same instant so ordering is determined
        # purely by id (draft created first → lower id → appears first in
        # .order_by("-created_at", "id") when timestamps are tied).
        _shared_ts = timezone.now()
        SolomonResource.objects.filter(
            slug__in=["draft-resource", "approved-resource"]
        ).update(created_at=_shared_ts)
        self.draft_resource.refresh_from_db()
        self.approved_resource.refresh_from_db()

        self.published_resource = SolomonResource.objects.create(
            title="Published Resource",
            slug="published-resource",
            summary="Already live",
            resource_type=SolomonResourceType.POLICY,
            status=SolomonLifecycle.PUBLISHED,
            visibility=SolomonVisibility.PUBLIC,
            scope=SolomonScope.GLOBAL,
            category=self.category,
            module="test",
            sort_order=3,
        )

        self.archived_resource = SolomonResource.objects.create(
            title="Archived Resource",
            slug="archived-resource",
            summary="No longer active",
            resource_type=SolomonResourceType.ARTICLE,
            status=SolomonLifecycle.ARCHIVED,
            visibility=SolomonVisibility.PUBLIC,
            scope=SolomonScope.GLOBAL,
            category=self.category,
            module="test",
            sort_order=4,
        )

    def test_review_queue_returns_only_draft_and_approved(self):
        """Review queue returns only DRAFT and APPROVED resources."""
        qs = governance_review_queue(None)
        slugs = set(qs.values_list("slug", flat=True))
        self.assertIn("draft-resource", slugs)
        self.assertIn("approved-resource", slugs)
        self.assertNotIn("published-resource", slugs)
        self.assertNotIn("archived-resource", slugs)

    def test_review_queue_ordering_deterministic(self):
        """Review queue returns draft-first deterministic ordering."""
        qs = governance_review_queue(None)
        resources = list(qs)
        # Draft items are prioritized ahead of approved items.
        self.assertEqual(resources[0].slug, "draft-resource")
        self.assertEqual(resources[1].slug, "approved-resource")

    def test_review_queue_ordering_with_new_items(self):
        """Review queue maintains consistent ordering with additions."""
        first_qs = list(governance_review_queue(None).values_list("slug", flat=True))

        # Add a new draft
        new_draft = SolomonResource.objects.create(
            title="New Draft",
            slug="new-draft",
            status=SolomonLifecycle.DRAFT,
            visibility=SolomonVisibility.STAFF,
            scope=SolomonScope.GLOBAL,
            category=self.category,
            module="test",
        )

        second_qs = list(governance_review_queue(None).values_list("slug", flat=True))

        # New draft should be first (newest)
        self.assertEqual(second_qs[0], "new-draft")
        # Previous items should follow in same order
        self.assertIn("approved-resource", second_qs)
        self.assertIn("draft-resource", second_qs)

    def test_filtered_queue_draft_only(self):
        """Filtering by status=draft returns only draft resources."""
        qs = governance_filtered_review_queue(None, status_filter="draft")
        slugs = set(qs.values_list("slug", flat=True))
        self.assertIn("draft-resource", slugs)
        self.assertNotIn("approved-resource", slugs)
        self.assertEqual(len(slugs), 1)

    def test_filtered_queue_approved_only(self):
        """Filtering by status=approved returns only approved resources."""
        qs = governance_filtered_review_queue(None, status_filter="approved")
        slugs = set(qs.values_list("slug", flat=True))
        self.assertIn("approved-resource", slugs)
        self.assertNotIn("draft-resource", slugs)
        self.assertEqual(len(slugs), 1)

    def test_filtered_queue_both_statuses(self):
        """Filtering by status=draft,approved returns both."""
        qs = governance_filtered_review_queue(None, status_filter="draft,approved")
        slugs = set(qs.values_list("slug", flat=True))
        self.assertIn("draft-resource", slugs)
        self.assertIn("approved-resource", slugs)
        self.assertNotIn("published-resource", slugs)
        self.assertEqual(len(slugs), 2)

    def test_filtered_queue_approved_draft_order_preserved(self):
        """Filtering with status=approved,draft still respects deterministic ordering."""
        qs = governance_filtered_review_queue(None, status_filter="approved,draft")
        slugs = list(qs.values_list("slug", flat=True))
        # Draft items are prioritized ahead of approved items.
        self.assertEqual(slugs[0], "draft-resource")
        self.assertEqual(slugs[1], "approved-resource")

    def test_filtered_queue_empty_filter_returns_all(self):
        """Empty status filter returns all draft and approved resources."""
        qs = governance_filtered_review_queue(None, status_filter="")
        slugs = set(qs.values_list("slug", flat=True))
        self.assertIn("draft-resource", slugs)
        self.assertIn("approved-resource", slugs)
        self.assertEqual(len(slugs), 2)

    def test_filtered_queue_invalid_status_returns_empty(self):
        """Invalid status filter returns empty queryset (fail-closed)."""
        qs = governance_filtered_review_queue(None, status_filter="invalid_status")
        self.assertEqual(qs.count(), 0)

    def test_filtered_queue_mixed_valid_invalid_returns_empty(self):
        """Mixed valid/invalid status returns empty (fail-closed)."""
        qs = governance_filtered_review_queue(None, status_filter="draft,invalid_status")
        self.assertEqual(qs.count(), 0)

    def test_filtered_queue_published_status_returns_empty(self):
        """Cannot filter for published status (only draft/approved allowed)."""
        qs = governance_filtered_review_queue(None, status_filter="published")
        self.assertEqual(qs.count(), 0)

    def test_filtered_queue_archived_status_returns_empty(self):
        """Cannot filter for archived status (only draft/approved allowed)."""
        qs = governance_filtered_review_queue(None, status_filter="archived")
        self.assertEqual(qs.count(), 0)

    def test_filtered_queue_case_insensitive(self):
        """Status filter is case-insensitive."""
        qs_lower = governance_filtered_review_queue(None, status_filter="draft")
        qs_upper = governance_filtered_review_queue(None, status_filter="DRAFT")
        qs_mixed = governance_filtered_review_queue(None, status_filter="DrAfT")

        self.assertEqual(qs_lower.count(), qs_upper.count())
        self.assertEqual(qs_lower.count(), qs_mixed.count())
        self.assertEqual(qs_lower.count(), 1)

    def test_filtered_queue_whitespace_handling(self):
        """Status filter handles whitespace correctly."""
        qs = governance_filtered_review_queue(None, status_filter="draft , approved")
        slugs = set(qs.values_list("slug", flat=True))
        self.assertIn("draft-resource", slugs)
        self.assertIn("approved-resource", slugs)
        self.assertEqual(len(slugs), 2)


@override_settings(CROWN_SOLOMON_API_ENABLED=True, ROOT_URLCONF="solomon.urls")
class ReviewQueueApiEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.category = SolomonCategory.objects.create(
            name="Test Category",
            slug="test-category",
            is_public=True,
        )

        self.staff_user = User.objects.create_user(
            username="staff-user",
            password="password",
            is_staff=True,
        )
        self.regular_user = User.objects.create_user(
            username="regular-user",
            password="password",
        )

        # Create resources in different states
        self.draft_resource = SolomonResource.objects.create(
            title="Draft Resource",
            slug="draft-resource",
            status=SolomonLifecycle.DRAFT,
            visibility=SolomonVisibility.STAFF,
            scope=SolomonScope.GLOBAL,
            category=self.category,
            module="test",
        )

        self.approved_resource = SolomonResource.objects.create(
            title="Approved Resource",
            slug="approved-resource",
            status=SolomonLifecycle.APPROVED,
            visibility=SolomonVisibility.STAFF,
            scope=SolomonScope.GLOBAL,
            category=self.category,
            module="test",
        )

        self.published_resource = SolomonResource.objects.create(
            title="Published Resource",
            slug="published-resource",
            status=SolomonLifecycle.PUBLISHED,
            visibility=SolomonVisibility.PUBLIC,
            scope=SolomonScope.GLOBAL,
            category=self.category,
            module="test",
        )

    def test_review_queue_endpoint_requires_authentication(self):
        """Review queue endpoint requires authentication."""
        response = self.client.get("/api/solomon/governance/review-queue/")
        self.assertEqual(response.status_code, 401)

    def test_review_queue_endpoint_requires_staff_access(self):
        """Review queue endpoint requires staff/admin access."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get("/api/solomon/governance/review-queue/")
        self.assertEqual(response.status_code, 404)

    def test_review_queue_endpoint_staff_access(self):
        """Staff user can access review queue endpoint."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get("/api/solomon/governance/review-queue/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)  # draft + approved

    def test_review_queue_endpoint_returns_draft_and_approved_only(self):
        """Endpoint returns only draft and approved resources."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get("/api/solomon/governance/review-queue/")
        slugs = [r["slug"] for r in response.data]
        self.assertIn("draft-resource", slugs)
        self.assertIn("approved-resource", slugs)
        self.assertNotIn("published-resource", slugs)

    def test_review_queue_endpoint_with_status_filter_draft(self):
        """Endpoint supports status=draft filter."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get("/api/solomon/governance/review-queue/?status=draft")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["slug"], "draft-resource")

    def test_review_queue_endpoint_with_status_filter_approved(self):
        """Endpoint supports status=approved filter."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get("/api/solomon/governance/review-queue/?status=approved")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["slug"], "approved-resource")

    def test_review_queue_endpoint_with_status_filter_both(self):
        """Endpoint supports status=draft,approved filter."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get("/api/solomon/governance/review-queue/?status=draft,approved")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

    def test_review_queue_endpoint_with_invalid_status_filter(self):
        """Endpoint with invalid status filter returns empty (fail-closed)."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get("/api/solomon/governance/review-queue/?status=invalid")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_review_queue_endpoint_with_published_status_filter(self):
        """Cannot filter for published via endpoint."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get("/api/solomon/governance/review-queue/?status=published")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 0)

    def test_review_queue_endpoint_disabled_by_feature_flag(self):
        """Endpoint respects CROWN_SOLOMON_API_ENABLED flag."""
        with override_settings(CROWN_SOLOMON_API_ENABLED=False):
            self.client.force_authenticate(user=self.staff_user)
            response = self.client.get("/api/solomon/governance/review-queue/")
            self.assertEqual(response.status_code, 404)

    def test_review_queue_endpoint_returns_deterministic_ordering(self):
        """Endpoint returns results in consistent order."""
        self.client.force_authenticate(user=self.staff_user)
        response1 = self.client.get("/api/solomon/governance/review-queue/")
        response2 = self.client.get("/api/solomon/governance/review-queue/")

        slugs1 = [r["slug"] for r in response1.data]
        slugs2 = [r["slug"] for r in response2.data]

        self.assertEqual(slugs1, slugs2)

    def test_review_queue_endpoint_response_format(self):
        """Endpoint response includes expected fields."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get("/api/solomon/governance/review-queue/")
        self.assertEqual(response.status_code, 200)

        if response.data:
            resource = response.data[0]
            expected_fields = {
                "id",
                "title",
                "slug",
                "summary",
                "resource_type",
                "status",
                "visibility",
                "scope",
                "category",
                "topics",
                "audiences",
                "owner",
                "approver",
                "review_date",
                "version",
                "license_type",
                "module",
                "created_at",
                "updated_at",
            }
            self.assertTrue(expected_fields.issubset(set(resource.keys())))


@override_settings(CROWN_SOLOMON_API_ENABLED=True, ROOT_URLCONF="solomon.urls")
class ReviewQueueRegressionTests(TestCase):
    """Ensure existing SOLOMON APIs remain functional."""

    def setUp(self):
        self.client = APIClient()
        self.staff_user = User.objects.create_user(
            username="staff-user",
            password="password",
            is_staff=True,
        )
        self.category = SolomonCategory.objects.create(
            name="Test Category",
            slug="test-category",
            is_public=True,
        )
        self.resource = SolomonResource.objects.create(
            title="Test Resource",
            slug="test-resource",
            status=SolomonLifecycle.PUBLISHED,
            visibility=SolomonVisibility.PUBLIC,
            scope=SolomonScope.GLOBAL,
            category=self.category,
            module="test",
        )


@override_settings(CROWN_SOLOMON_API_ENABLED=True, ROOT_URLCONF="solomon.urls")
class GovernanceStaleReviewQueueTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.staff_user = User.objects.create_user(
            username="stale-staff-user",
            password="password",
            is_staff=True,
        )
        self.category = SolomonCategory.objects.create(
            name="Stale Category",
            slug="stale-category",
            is_public=True,
        )

        today = timezone.localdate()

        self.published_stale = SolomonResource.objects.create(
            title="Published Stale",
            slug="published-stale",
            status=SolomonLifecycle.PUBLISHED,
            visibility=SolomonVisibility.PUBLIC,
            scope=SolomonScope.GLOBAL,
            category=self.category,
            module="governance",
            review_date=today - timedelta(days=120),
        )

        self.approved_missing_review = SolomonResource.objects.create(
            title="Approved Missing Review",
            slug="approved-missing-review",
            status=SolomonLifecycle.APPROVED,
            visibility=SolomonVisibility.STAFF,
            scope=SolomonScope.GLOBAL,
            category=self.category,
            module="governance",
            review_date=None,
        )

        self.published_warning = SolomonResource.objects.create(
            title="Published Warning",
            slug="published-warning",
            status=SolomonLifecycle.PUBLISHED,
            visibility=SolomonVisibility.PUBLIC,
            scope=SolomonScope.GLOBAL,
            category=self.category,
            module="governance",
            review_date=today - timedelta(days=80),
        )

        self.published_fresh = SolomonResource.objects.create(
            title="Published Fresh",
            slug="published-fresh",
            status=SolomonLifecycle.PUBLISHED,
            visibility=SolomonVisibility.PUBLIC,
            scope=SolomonScope.GLOBAL,
            category=self.category,
            module="governance",
            review_date=today - timedelta(days=20),
        )

        self.draft_missing_review = SolomonResource.objects.create(
            title="Draft Missing Review",
            slug="draft-missing-review",
            status=SolomonLifecycle.DRAFT,
            visibility=SolomonVisibility.STAFF,
            scope=SolomonScope.GLOBAL,
            category=self.category,
            module="governance",
            review_date=None,
        )

    def test_stale_bucket_returns_missing_and_old_review_items(self):
        qs = governance_stale_review_queue(None, bucket="stale")
        slugs = set(qs.values_list("slug", flat=True))

        self.assertIn("published-stale", slugs)
        self.assertIn("approved-missing-review", slugs)
        self.assertNotIn("published-warning", slugs)
        self.assertNotIn("published-fresh", slugs)
        self.assertNotIn("draft-missing-review", slugs)

    def test_warning_bucket_returns_warning_window_only(self):
        qs = governance_stale_review_queue(None, bucket="warning")
        slugs = set(qs.values_list("slug", flat=True))

        self.assertIn("published-warning", slugs)
        self.assertNotIn("published-stale", slugs)
        self.assertNotIn("approved-missing-review", slugs)
        self.assertNotIn("published-fresh", slugs)

    def test_all_bucket_returns_union_of_stale_and_warning(self):
        qs = governance_stale_review_queue(None, bucket="all")
        slugs = set(qs.values_list("slug", flat=True))

        self.assertIn("published-stale", slugs)
        self.assertIn("approved-missing-review", slugs)
        self.assertIn("published-warning", slugs)
        self.assertNotIn("published-fresh", slugs)
        self.assertNotIn("draft-missing-review", slugs)

    def test_invalid_bucket_fails_closed(self):
        qs = governance_stale_review_queue(None, bucket="invalid")
        self.assertEqual(qs.count(), 0)

    def test_invalid_thresholds_fail_closed(self):
        qs_zero = governance_stale_review_queue(None, bucket="stale", warning_days=0, stale_days=90)
        qs_reversed = governance_stale_review_queue(None, bucket="stale", warning_days=90, stale_days=90)

        self.assertEqual(qs_zero.count(), 0)
        self.assertEqual(qs_reversed.count(), 0)

    def test_stale_detection_deterministic(self):
        first = list(governance_stale_review_queue(None, bucket="all").values_list("slug", flat=True))
        second = list(governance_stale_review_queue(None, bucket="all").values_list("slug", flat=True))

        self.assertEqual(first, second)

    def test_categories_endpoint_still_works(self):
        """Existing categories endpoint not affected."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get("/api/solomon/categories/")
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data), 0)

    def test_resources_endpoint_still_works(self):
        """Existing resources endpoint not affected."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get("/api/solomon/resources/")
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data), 0)

    def test_context_endpoint_still_works(self):
        """Existing context endpoint not affected."""
        self.client.force_authenticate(user=self.staff_user)
        response = self.client.get("/api/solomon/context/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("resources", response.data)
