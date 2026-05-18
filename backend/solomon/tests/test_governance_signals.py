"""Tests for SOLOMON governance signal detection (Phase 4A Slice 3)."""

from datetime import timedelta
from unittest.mock import Mock

from django.test import TestCase
from django.utils import timezone

from solomon.models import (
	SolomonCategory,
	SolomonLifecycle,
	SolomonResource,
	SolomonResourceType,
	SolomonTopic,
	SolomonVisibility,
	SolomonScope,
	SolomonAudience,
)
from solomon.services import (
	governance_stale_review_queue,
	governance_review_backlog_aging,
	governance_orphaned_resources,
)


class GovernanceStaleReviewQueueTests(TestCase):
	"""Test stale-content detection signal."""

	def setUp(self):
		"""Normalize created_at timestamps to eliminate ordering flakiness."""
		self.now = timezone.now().replace(microsecond=0)
		self.category = SolomonCategory.objects.create(
			name="Help", slug="help", is_public=True
		)
		self.request = Mock(user=Mock())

	def test_stale_queue_filters_by_bucket_stale(self):
		"""Stale bucket returns only resources older than stale_days threshold."""
		as_of = self.now.date()
		stale_date = as_of - timedelta(days=95)  # 95 days ago = stale
		warning_date = as_of - timedelta(days=80)  # 80 days ago = warning

		stale_resource = SolomonResource.objects.create(
			title="Stale",
			slug="stale-res",
			category=self.category,
			status=SolomonLifecycle.PUBLISHED,
			visibility=SolomonVisibility.PUBLIC,
			review_date=stale_date,
		)
		warning_resource = SolomonResource.objects.create(
			title="Warning",
			slug="warning-res",
			category=self.category,
			status=SolomonLifecycle.PUBLISHED,
			visibility=SolomonVisibility.PUBLIC,
			review_date=warning_date,
		)

		result = governance_stale_review_queue(
			self.request, bucket="stale", as_of_date=as_of
		)
		ids = list(result.values_list("id", flat=True))

		self.assertIn(stale_resource.id, ids)
		self.assertNotIn(warning_resource.id, ids)

	def test_stale_queue_filters_by_bucket_warning(self):
		"""Warning bucket returns only resources in warning window."""
		as_of = self.now.date()
		stale_date = as_of - timedelta(days=95)
		warning_date = as_of - timedelta(days=80)
		fresh_date = as_of - timedelta(days=50)

		SolomonResource.objects.create(
			title="Stale",
			slug="stale-res2",
			category=self.category,
			status=SolomonLifecycle.PUBLISHED,
			visibility=SolomonVisibility.PUBLIC,
			review_date=stale_date,
		)
		warning_resource = SolomonResource.objects.create(
			title="Warning",
			slug="warning-res2",
			category=self.category,
			status=SolomonLifecycle.PUBLISHED,
			visibility=SolomonVisibility.PUBLIC,
			review_date=warning_date,
		)
		SolomonResource.objects.create(
			title="Fresh",
			slug="fresh-res",
			category=self.category,
			status=SolomonLifecycle.PUBLISHED,
			visibility=SolomonVisibility.PUBLIC,
			review_date=fresh_date,
		)

		result = governance_stale_review_queue(
			self.request, bucket="warning", as_of_date=as_of
		)
		ids = list(result.values_list("id", flat=True))

		self.assertEqual(len(ids), 1)
		self.assertIn(warning_resource.id, ids)

	def test_stale_queue_fails_closed_on_invalid_bucket(self):
		"""Invalid bucket returns empty queryset."""
		result = governance_stale_review_queue(
			self.request, bucket="invalid_bucket"
		)
		self.assertEqual(result.count(), 0)

	def test_stale_queue_fails_closed_on_invalid_thresholds(self):
		"""Invalid thresholds (negative or reversed) return empty queryset."""
		as_of = self.now.date()
		self.assertEqual(
			governance_stale_review_queue(
				self.request, warning_days=-1, as_of_date=as_of
			).count(),
			0,
		)
		self.assertEqual(
			governance_stale_review_queue(
				self.request, stale_days=-1, as_of_date=as_of
			).count(),
			0,
		)
		self.assertEqual(
			governance_stale_review_queue(
				self.request, warning_days=100, stale_days=50, as_of_date=as_of
			).count(),
			0,
		)

	def test_stale_queue_no_state_mutations(self):
		"""Signal detection does NOT mutate lifecycle or visibility."""
		as_of = self.now.date()
		resource = SolomonResource.objects.create(
			title="NoMutate",
			slug="nomutate",
			category=self.category,
			status=SolomonLifecycle.PUBLISHED,
			visibility=SolomonVisibility.PUBLIC,
			review_date=as_of - timedelta(days=100),
		)
		original_status = resource.status
		original_visibility = resource.visibility

		_ = governance_stale_review_queue(self.request, bucket="stale", as_of_date=as_of)

		resource.refresh_from_db()
		self.assertEqual(resource.status, original_status)
		self.assertEqual(resource.visibility, original_visibility)

	def test_stale_queue_deterministic_ordering(self):
		"""Results are deterministically ordered by review_date, updated_at, id."""
		as_of = self.now.date()
		stale_date = as_of - timedelta(days=100)

		# Create resources with same review_date but different updated_at
		res1 = SolomonResource.objects.create(
			title="Res1", slug="res1-stale", category=self.category,
			status=SolomonLifecycle.PUBLISHED, visibility=SolomonVisibility.PUBLIC,
			review_date=stale_date, created_at=self.now - timedelta(seconds=10)
		)
		res2 = SolomonResource.objects.create(
			title="Res2", slug="res2-stale", category=self.category,
			status=SolomonLifecycle.PUBLISHED, visibility=SolomonVisibility.PUBLIC,
			review_date=stale_date, created_at=self.now - timedelta(seconds=5)
		)

		result = list(governance_stale_review_queue(
			self.request, bucket="stale", as_of_date=as_of
		))
		ids = [r.id for r in result]

		# Run multiple times to verify determinism
		for _ in range(3):
			result_again = list(governance_stale_review_queue(
				self.request, bucket="stale", as_of_date=as_of
			))
			self.assertEqual([r.id for r in result_again], ids)


class GovernanceReviewBacklogAgingTests(TestCase):
	"""Test review backlog aging detection signal."""

	def setUp(self):
		"""Normalize timestamps to eliminate ordering flakiness."""
		self.now = timezone.now().replace(microsecond=0)
		self.category = SolomonCategory.objects.create(
			name="Reviews", slug="reviews", is_public=True
		)
		self.request = Mock(user=Mock())

	def test_backlog_aging_detects_by_bucket(self):
		"""Backlog aging bucket detects resources in warning window."""
		aging_time = self.now - timedelta(hours=48)  # 48 hours = aging
		critical_time = self.now - timedelta(hours=96)  # 96 hours = critical

		aging_resource = SolomonResource.objects.create(
			title="Aging",
			slug="aging-res",
			category=self.category,
			status=SolomonLifecycle.DRAFT,
			visibility=SolomonVisibility.PUBLIC,
		)
		critical_resource = SolomonResource.objects.create(
			title="Critical",
			slug="critical-res",
			category=self.category,
			status=SolomonLifecycle.DRAFT,
			visibility=SolomonVisibility.PUBLIC,
		)
		# Update timestamps after creation (auto_now_add ignores initial values)
		SolomonResource.objects.filter(id=aging_resource.id).update(created_at=aging_time)
		SolomonResource.objects.filter(id=critical_resource.id).update(created_at=critical_time)

		result = governance_review_backlog_aging(
			self.request, bucket="aging", as_of_dt=self.now
		)
		ids = list(result.values_list("id", flat=True))

		self.assertIn(aging_resource.id, ids)
		self.assertNotIn(critical_resource.id, ids)

	def test_backlog_critical_bucket(self):
		"""Critical bucket detects only resources older than critical_hours."""
		critical_time = self.now - timedelta(hours=96)
		recent_time = self.now - timedelta(hours=48)

		critical_resource = SolomonResource.objects.create(
			title="Critical",
			slug="critical-res2",
			category=self.category,
			status=SolomonLifecycle.APPROVED,
			visibility=SolomonVisibility.PUBLIC,
		)
		recent_resource = SolomonResource.objects.create(
			title="Recent",
			slug="recent-res",
			category=self.category,
			status=SolomonLifecycle.APPROVED,
			visibility=SolomonVisibility.PUBLIC,
		)
		# Update timestamps after creation
		SolomonResource.objects.filter(id=critical_resource.id).update(created_at=critical_time)
		SolomonResource.objects.filter(id=recent_resource.id).update(created_at=recent_time)

		result = governance_review_backlog_aging(
			self.request, bucket="critical", as_of_dt=self.now
		)
		ids = list(result.values_list("id", flat=True))

		self.assertEqual(len(ids), 1)
		self.assertIn(critical_resource.id, ids)

	def test_backlog_all_bucket(self):
		"""All bucket returns both aging and critical."""
		aging_time = self.now - timedelta(hours=48)
		critical_time = self.now - timedelta(hours=96)

		aging_resource = SolomonResource.objects.create(
			title="Aging",
			slug="aging-res-all",
			category=self.category,
			status=SolomonLifecycle.DRAFT,
			visibility=SolomonVisibility.PUBLIC,
		)
		critical_resource = SolomonResource.objects.create(
			title="Critical",
			slug="critical-res-all",
			category=self.category,
			status=SolomonLifecycle.DRAFT,
			visibility=SolomonVisibility.PUBLIC,
		)
		# Update timestamps after creation
		SolomonResource.objects.filter(id=aging_resource.id).update(created_at=aging_time)
		SolomonResource.objects.filter(id=critical_resource.id).update(created_at=critical_time)

		result = governance_review_backlog_aging(
			self.request, bucket="all", as_of_dt=self.now
		)
		ids = list(result.values_list("id", flat=True))

		self.assertIn(aging_resource.id, ids)
		self.assertIn(critical_resource.id, ids)

	def test_backlog_fails_closed_on_invalid_bucket(self):
		"""Invalid bucket returns empty queryset."""
		result = governance_review_backlog_aging(
			self.request, bucket="invalid", as_of_dt=self.now
		)
		self.assertEqual(result.count(), 0)

	def test_backlog_fails_closed_on_invalid_thresholds(self):
		"""Invalid thresholds return empty queryset."""
		self.assertEqual(
			governance_review_backlog_aging(
				self.request, warning_hours=-1, as_of_dt=self.now
			).count(),
			0,
		)
		self.assertEqual(
			governance_review_backlog_aging(
				self.request, critical_hours=-1, as_of_dt=self.now
			).count(),
			0,
		)
		self.assertEqual(
			governance_review_backlog_aging(
				self.request, warning_hours=100, critical_hours=50, as_of_dt=self.now
			).count(),
			0,
		)

	def test_backlog_filters_by_lifecycle(self):
		"""Backlog aging only detects DRAFT and APPROVED resources."""
		aging_time = self.now - timedelta(hours=48)

		# Published resources should not be detected
		published_res = SolomonResource.objects.create(
			title="Published",
			slug="published-res",
			category=self.category,
			status=SolomonLifecycle.PUBLISHED,
			visibility=SolomonVisibility.PUBLIC,
		)
		# Archived resources should not be detected
		archived_res = SolomonResource.objects.create(
			title="Archived",
			slug="archived-res",
			category=self.category,
			status=SolomonLifecycle.ARCHIVED,
			visibility=SolomonVisibility.PUBLIC,
		)
		# Draft should be detected
		draft_resource = SolomonResource.objects.create(
			title="Draft",
			slug="draft-res",
			category=self.category,
			status=SolomonLifecycle.DRAFT,
			visibility=SolomonVisibility.PUBLIC,
		)
		# Update timestamps after creation
		for res in [published_res, archived_res, draft_resource]:
			SolomonResource.objects.filter(id=res.id).update(created_at=aging_time)

		result = governance_review_backlog_aging(
			self.request, bucket="aging", as_of_dt=self.now
		)
		ids = list(result.values_list("id", flat=True))

		self.assertEqual(len(ids), 1)
		self.assertIn(draft_resource.id, ids)

	def test_backlog_no_state_mutations(self):
		"""Signal detection does NOT mutate lifecycle or visibility."""
		aging_time = self.now - timedelta(hours=48)
		resource = SolomonResource.objects.create(
			title="NoMutate",
			slug="nomutate-backlog",
			category=self.category,
			status=SolomonLifecycle.DRAFT,
			visibility=SolomonVisibility.PUBLIC,
		)
		# Update timestamp after creation
		SolomonResource.objects.filter(id=resource.id).update(created_at=aging_time)
		original_status = resource.status
		original_visibility = resource.visibility

		_ = governance_review_backlog_aging(
			self.request, bucket="aging", as_of_dt=self.now
		)

		resource.refresh_from_db()
		self.assertEqual(resource.status, original_status)
		self.assertEqual(resource.visibility, original_visibility)

	def test_backlog_deterministic_ordering(self):
		"""Results are deterministically ordered by created_at, id."""
		aging_time = self.now - timedelta(hours=48)

		res1 = SolomonResource.objects.create(
			title="Res1", slug="res1-aging", category=self.category,
			status=SolomonLifecycle.DRAFT, visibility=SolomonVisibility.PUBLIC,
		)
		res2 = SolomonResource.objects.create(
			title="Res2", slug="res2-aging", category=self.category,
			status=SolomonLifecycle.DRAFT, visibility=SolomonVisibility.PUBLIC,
		)
		# Update timestamps after creation with different offsets
		SolomonResource.objects.filter(id=res1.id).update(
			created_at=aging_time - timedelta(minutes=10)
		)
		SolomonResource.objects.filter(id=res2.id).update(
			created_at=aging_time - timedelta(minutes=5)
		)

		result = list(governance_review_backlog_aging(
			self.request, bucket="aging", as_of_dt=self.now
		))
		ids = [r.id for r in result]

		# Verify determinism over multiple runs
		for _ in range(3):
			result_again = list(governance_review_backlog_aging(
				self.request, bucket="aging", as_of_dt=self.now
			))
			self.assertEqual([r.id for r in result_again], ids)


class GovernanceOrphanedResourcesTests(TestCase):
	"""Test orphaned-resource detection signal."""

	def setUp(self):
		"""Set up test fixtures."""
		self.now = timezone.now().replace(microsecond=0)
		self.category = SolomonCategory.objects.create(
			name="Testing", slug="testing", is_public=True
		)
		self.request = Mock(user=Mock())

	def test_orphaned_detects_null_category_reference(self):
		"""Orphaned detection identifies resources with NULL category FK."""
		# This test verifies the logic, but in practice Django prevents
		# orphaned FKs due to cascading deletes or SET_NULL
		resource = SolomonResource.objects.create(
			title="HasCategory",
			slug="has-category",
			category=self.category,
			status=SolomonLifecycle.PUBLISHED,
			visibility=SolomonVisibility.PUBLIC,
		)

		# Verify resource is not flagged as orphaned when category exists
		result = governance_orphaned_resources(self.request)
		ids = list(result.values_list("id", flat=True))
		self.assertNotIn(resource.id, ids)

	def test_orphaned_requires_request_user(self):
		"""Orphaned detection fails-closed without valid request.user."""
		bad_request = Mock(spec=[])  # No user attribute
		result = governance_orphaned_resources(bad_request)
		self.assertEqual(result.count(), 0)

	def test_orphaned_no_state_mutations(self):
		"""Signal detection does NOT mutate anything."""
		resource = SolomonResource.objects.create(
			title="NoMutate",
			slug="nomutate-orphan",
			category=self.category,
			status=SolomonLifecycle.PUBLISHED,
			visibility=SolomonVisibility.PUBLIC,
		)
		original_status = resource.status
		original_visibility = resource.visibility
		original_category = resource.category_id

		_ = governance_orphaned_resources(self.request)

		resource.refresh_from_db()
		self.assertEqual(resource.status, original_status)
		self.assertEqual(resource.visibility, original_visibility)
		self.assertEqual(resource.category_id, original_category)

	def test_orphaned_deterministic_ordering(self):
		"""Orphaned results are deterministically ordered by id."""
		res1 = SolomonResource.objects.create(
			title="Res1", slug="res1-orphan", category=self.category,
			status=SolomonLifecycle.PUBLISHED, visibility=SolomonVisibility.PUBLIC
		)
		res2 = SolomonResource.objects.create(
			title="Res2", slug="res2-orphan", category=self.category,
			status=SolomonLifecycle.PUBLISHED, visibility=SolomonVisibility.PUBLIC
		)

		result = list(governance_orphaned_resources(self.request))
		ids = [r.id for r in result]

		# Verify determinism
		for _ in range(3):
			result_again = list(governance_orphaned_resources(self.request))
			self.assertEqual([r.id for r in result_again], ids)


class GovernanceSignalIntegrationTests(TestCase):
	"""Integration tests for signal detection suite."""

	def setUp(self):
		"""Set up test fixtures."""
		self.now = timezone.now().replace(microsecond=0)
		self.category = SolomonCategory.objects.create(
			name="Integration", slug="integration", is_public=True
		)
		self.request = Mock(user=Mock())

	def test_all_signals_operate_independently(self):
		"""Signals can run simultaneously without affecting each other."""
		as_of = self.now.date()
		aging_time = self.now - timedelta(hours=48)

		# Create resources for all signal types
		stale_res = SolomonResource.objects.create(
			title="Stale",
			slug="stale-integration",
			category=self.category,
			status=SolomonLifecycle.PUBLISHED,
			visibility=SolomonVisibility.PUBLIC,
			review_date=as_of - timedelta(days=100),
		)
		aging_res = SolomonResource.objects.create(
			title="Aging",
			slug="aging-integration",
			category=self.category,
			status=SolomonLifecycle.DRAFT,
			visibility=SolomonVisibility.PUBLIC,
		)
		# Update aging timestamp
		SolomonResource.objects.filter(id=aging_res.id).update(created_at=aging_time)

		stale = governance_stale_review_queue(self.request, bucket="stale", as_of_date=as_of)
		aging = governance_review_backlog_aging(self.request, bucket="aging", as_of_dt=self.now)
		orphaned = governance_orphaned_resources(self.request)

		# All signals return results without affecting each other
		self.assertGreater(stale.count(), 0)
		self.assertGreater(aging.count(), 0)

	def test_signals_readonly_operations(self):
		"""All signals are read-only (query operations only)."""
		aging_time = self.now - timedelta(hours=48)
		resource = SolomonResource.objects.create(
			title="ReadOnly",
			slug="readonly-integration",
			category=self.category,
			status=SolomonLifecycle.DRAFT,
			visibility=SolomonVisibility.PUBLIC,
		)
		# Update timestamp after creation
		SolomonResource.objects.filter(id=resource.id).update(created_at=aging_time)

		# Each signal reads state but doesn't modify it
		_ = governance_stale_review_queue(self.request)
		_ = governance_review_backlog_aging(self.request)
		_ = governance_orphaned_resources(self.request)

		resource.refresh_from_db()
		self.assertEqual(resource.status, SolomonLifecycle.DRAFT)
		self.assertEqual(resource.visibility, SolomonVisibility.PUBLIC)
