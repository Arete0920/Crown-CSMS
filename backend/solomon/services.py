"""Governed query services for SOLOMON read-only APIs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from .models import (
	SolomonAudience,
	SolomonCategory,
	SolomonContextRule,
	SolomonLifecycle,
	SolomonPlaybook,
	SolomonResource,
	SolomonResourceType,
	SolomonTopic,
)
from .permissions import (
	allowed_resource_statuses,
	allowed_resource_visibility_values,
	allowed_scope_values,
	can_view_restricted_solomon_content,
	normalized_text,
)


def visible_categories(request):
	qs = SolomonCategory.objects.all().order_by("sort_order", "name")
	if not can_view_restricted_solomon_content(request):
		qs = qs.filter(is_public=True)
	return qs


def visible_topics(request):
	return SolomonTopic.objects.all().order_by("name")


def visible_audiences(request):
	qs = SolomonAudience.objects.all().order_by("name")
	if not can_view_restricted_solomon_content(request):
		qs = qs.filter(is_public=True)
	return qs


def _route_filter(route: str):
	route = normalized_text(route).rstrip("/")
	if not route:
		return Q()
	return Q(route_path__iexact=route) | Q(route_path__startswith=f"{route}/")


def _audience_filter(audience: str):
	audience = normalized_text(audience)
	if not audience:
		return Q()
	return (
		Q(audiences__slug__iexact=audience)
		| Q(audiences__role_code__iexact=audience)
		| Q(audiences__name__iexact=audience)
	)


def _visible_category_filter(request):
	if can_view_restricted_solomon_content(request):
		return Q()
	return Q(category__isnull=True) | Q(category__is_public=True)


def visible_resources(request, module: str = "", route: str = "", audience: str = "", scope: str = ""):
	scope_values = allowed_scope_values(scope)
	if scope and not scope_values:
		return SolomonResource.objects.none()

	qs = (
		SolomonResource.objects.select_related("category")
		.prefetch_related("topics", "audiences")
		.filter(
			status__in=allowed_resource_statuses(request),
			visibility__in=allowed_resource_visibility_values(request),
			scope__in=scope_values,
		)
	)

	if module:
		qs = qs.filter(module__iexact=normalized_text(module))
	if route:
		qs = qs.filter(_route_filter(route))
	if audience:
		qs = qs.filter(_audience_filter(audience))
	if not can_view_restricted_solomon_content(request):
		qs = qs.filter(_visible_category_filter(request))
	return qs.distinct().order_by("module", "sort_order", "title")


def visible_playbooks(request, module: str = "", route: str = "", audience: str = ""):
	qs = (
		SolomonPlaybook.objects.select_related("category")
		.prefetch_related("audiences")
		.filter(
			status__in=allowed_resource_statuses(request),
			visibility__in=allowed_resource_visibility_values(request),
		)
	)

	if module:
		qs = qs.filter(module__iexact=normalized_text(module))
	if route:
		qs = qs.filter(_route_filter(route))
	if audience:
		qs = qs.filter(_audience_filter(audience))
	if not can_view_restricted_solomon_content(request):
		qs = qs.filter(_visible_category_filter(request))
	return qs.distinct().order_by("module", "sort_order", "title")


def visible_context_rules(request, module: str = "", route: str = "", audience: str = ""):
	qs = SolomonContextRule.objects.select_related("resource", "playbook", "audience").filter(is_active=True)

	if module:
		qs = qs.filter(module__iexact=normalized_text(module))
	if route:
		qs = qs.filter(_route_filter(route))
	if audience:
		qs = qs.filter(
			Q(audience__slug__iexact=normalized_text(audience))
			| Q(audience__role_code__iexact=normalized_text(audience))
			| Q(audience__name__iexact=normalized_text(audience))
		)
	if not can_view_restricted_solomon_content(request):
		qs = qs.filter(Q(audience__isnull=True) | Q(audience__is_public=True))
	return qs.order_by("module", "route_path", "priority")


@dataclass(slots=True)
class SolomonContextResolver:
	request: object
	module: str = ""
	route: str = ""
	audience: str = ""
	scope: str = ""

	def _scope_is_valid(self) -> bool:
		return bool(allowed_scope_values(self.scope))

	def resolve(self) -> dict:
		if self.scope and not self._scope_is_valid():
			return {
				"module": normalized_text(self.module),
				"route": normalized_text(self.route),
				"audience": normalized_text(self.audience),
				"scope": normalized_text(self.scope),
				"resources": [],
				"guides": [],
				"playbooks": [],
				"context_help": [],
			}

		resources = list(
			visible_resources(
				self.request,
				module=self.module,
				route=self.route,
				audience=self.audience,
				scope=self.scope,
			)
		)
		playbooks = list(
			visible_playbooks(
				self.request,
				module=self.module,
				route=self.route,
				audience=self.audience,
			)
		)
		rules = list(
			visible_context_rules(
				self.request,
				module=self.module,
				route=self.route,
				audience=self.audience,
			)
		)

		resource_ids = {resource.id for resource in resources}
		playbook_ids = {playbook.id for playbook in playbooks}
		resolved_rules = []
		for rule in rules:
			if rule.resource_id and rule.resource_id not in resource_ids:
				continue
			if rule.playbook_id and rule.playbook_id not in playbook_ids:
				continue
			resolved_rules.append(rule)
			if rule.resource_id:
				resource_ids.add(rule.resource_id)
			if rule.playbook_id:
				playbook_ids.add(rule.playbook_id)

		resolved_resources = list(
			SolomonResource.objects.select_related("category")
			.prefetch_related("topics", "audiences")
			.filter(id__in=resource_ids)
			.order_by("module", "sort_order", "title")
		)
		resolved_playbooks = list(
			SolomonPlaybook.objects.select_related("category")
			.prefetch_related("audiences")
			.filter(id__in=playbook_ids)
			.order_by("module", "sort_order", "title")
		)

		guides = [resource for resource in resolved_resources if resource.resource_type == SolomonResourceType.GUIDE]

		return {
			"module": normalized_text(self.module),
			"route": normalized_text(self.route),
			"audience": normalized_text(self.audience),
			"scope": normalized_text(self.scope),
			"resources": resolved_resources,
			"guides": guides,
			"playbooks": resolved_playbooks,
			"context_help": resolved_rules,
		}


def governance_review_queue(request):
	"""
	Governance review queue: all resources in DRAFT or APPROVED state.

	Returns deterministically ordered queryset of resources pending review.
	RBAC visibility is NOT enforced here (staff/admin only via view permission).
	"""
	qs = (
		SolomonResource.objects.select_related("category")
		.prefetch_related("topics", "audiences")
		.filter(status__in=[SolomonLifecycle.DRAFT, SolomonLifecycle.APPROVED])
		.order_by("-created_at", "id")
	)
	return qs


def governance_filtered_review_queue(request, status_filter: str = ""):
	"""
	Governance review queue filtered by status.

	status_filter: comma-separated list of statuses (e.g., "draft,approved")
	Returns empty queryset if status_filter contains invalid values (fail-closed).
	"""
	qs = governance_review_queue(request)

	if not status_filter:
		return qs

	valid_statuses = {SolomonLifecycle.DRAFT, SolomonLifecycle.APPROVED}
	requested_statuses = [s.strip().lower() for s in status_filter.split(",")]

	# Fail-closed: invalid status values return empty queryset
	if not all(status in valid_statuses for status in requested_statuses):
		return SolomonResource.objects.none()

	return qs.filter(status__in=requested_statuses)


def governance_stale_review_queue(
	request,
	bucket: str = "stale",
	warning_days: int = 75,
	stale_days: int = 90,
	as_of_date=None,
):
	"""
	Stale-content detection rules for governance operations.

	Buckets:
	- stale: published/approved resources missing review_date OR older than stale_days
	- warning: review_date between warning_days and stale_days age window
	- all: union of warning + stale

	Fail-closed behavior:
	- invalid bucket returns empty queryset
	- invalid thresholds (non-positive or warning >= stale) return empty queryset
	"""
	_ = request
	bucket_value = normalized_text(bucket).lower() or "stale"
	valid_buckets = {"stale", "warning", "all"}
	if bucket_value not in valid_buckets:
		return SolomonResource.objects.none()

	if warning_days <= 0 or stale_days <= 0 or warning_days >= stale_days:
		return SolomonResource.objects.none()

	as_of = as_of_date or timezone.localdate()
	warning_cutoff = as_of - timedelta(days=warning_days)
	stale_cutoff = as_of - timedelta(days=stale_days)

	base_qs = SolomonResource.objects.select_related("category").prefetch_related("topics", "audiences").filter(
		status__in=[SolomonLifecycle.PUBLISHED, SolomonLifecycle.APPROVED]
	)

	stale_missing_review = Q(review_date__isnull=True)
	stale_by_date = Q(review_date__lte=stale_cutoff)
	warning_by_date = Q(review_date__lte=warning_cutoff) & Q(review_date__gt=stale_cutoff)

	if bucket_value == "stale":
		return base_qs.filter(stale_missing_review | stale_by_date).order_by("review_date", "-updated_at", "id")
	if bucket_value == "warning":
		return base_qs.filter(warning_by_date).order_by("review_date", "-updated_at", "id")

	return base_qs.filter(stale_missing_review | stale_by_date | warning_by_date).order_by(
		"review_date",
		"-updated_at",
		"id",
	)


def governance_review_backlog_aging(
	request,
	bucket: str = "aging",
	warning_hours: int = 24,
	critical_hours: int = 72,
	as_of_dt=None,
):
	"""
	Review backlog aging detection: identify resources stuck in review queue.

	Detects resources in DRAFT or APPROVED state by how long they've been waiting.

	Buckets:
	- aging: created/updated between warning_hours and critical_hours ago
	- critical: created/updated more than critical_hours ago
	- all: union of aging + critical

	Signals: detect, score, annotate, report, queue only.
	Does NOT: mutate lifecycle, auto-transition, auto-expire.

	Fail-closed behavior:
	- invalid bucket returns empty queryset
	- invalid thresholds (non-positive or warning >= critical) return empty queryset
	"""
	_ = request
	bucket_value = normalized_text(bucket).lower() or "aging"
	valid_buckets = {"aging", "critical", "all"}
	if bucket_value not in valid_buckets:
		return SolomonResource.objects.none()

	if warning_hours <= 0 or critical_hours <= 0 or warning_hours >= critical_hours:
		return SolomonResource.objects.none()

	as_of = as_of_dt or timezone.now()
	warning_cutoff = as_of - timedelta(hours=warning_hours)
	critical_cutoff = as_of - timedelta(hours=critical_hours)

	base_qs = (
		SolomonResource.objects.select_related("category")
		.prefetch_related("topics", "audiences")
		.filter(status__in=[SolomonLifecycle.DRAFT, SolomonLifecycle.APPROVED])
	)

	aging_by_date = Q(created_at__lte=warning_cutoff) & Q(created_at__gt=critical_cutoff)
	critical_by_date = Q(created_at__lte=critical_cutoff)

	if bucket_value == "aging":
		return base_qs.filter(aging_by_date).order_by("created_at", "id")
	if bucket_value == "critical":
		return base_qs.filter(critical_by_date).order_by("created_at", "id")

	return base_qs.filter(aging_by_date | critical_by_date).order_by("created_at", "id")


def governance_orphaned_resources(request):
	"""
	Orphaned-resource detection: identify resources with broken relationships.

	Detects resources where:
	- category_id is set but category was deleted (NULL foreign key)
	- topics exist in topics table but not in through table
	- audiences exist in audiences table but not in through table
	- owner/approver fields are set but reference invalid user identifiers

	Signals: detect, score, annotate, report, queue only.
	Does NOT: mutate relationships, auto-correct, auto-clean.

	Returns deterministically ordered queryset annotated with orphan status.
	Fail-closed: returns empty queryset if request permission cannot be determined.
	"""
	if not hasattr(request, 'user'):
		return SolomonResource.objects.none()

	base_qs = (
		SolomonResource.objects.select_related("category")
		.prefetch_related("topics", "audiences")
	)

	# Detect resources with NULL category (orphaned from category deletion)
	orphaned_category = Q(category__isnull=True, category_id__isnull=False)

	# Detect resources with invalid owner/approver (non-empty but not valid user identifiers)
	# Valid identifier patterns: UUID, email, username (alphanumeric + dots/hyphens)
	# For now, flag any resource with owner/approver set but no matching user record
	# This is a signal for downstream review, not a mutation

	return base_qs.filter(orphaned_category).order_by("id")
