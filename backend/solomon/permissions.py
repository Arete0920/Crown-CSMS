"""Governance helpers for SOLOMON read-only APIs."""

from __future__ import annotations

from django.conf import settings

from .models import SolomonLifecycle, SolomonScope, SolomonVisibility


def solomon_api_enabled() -> bool:
	return bool(getattr(settings, "CROWN_SOLOMON_API_ENABLED", False))


def can_view_restricted_solomon_content(request) -> bool:
	user = getattr(request, "user", None)
	if not user or not getattr(user, "is_authenticated", False):
		return False

	if getattr(user, "is_staff", False) or getattr(user, "is_superuser", False):
		return True

	role_value = str(
		getattr(user, "role", "") or getattr(user, "role_code", "") or ""
	).strip().lower()
	return role_value in {"admin", "staff"}


def allowed_resource_statuses(request) -> tuple[str, ...]:
	if can_view_restricted_solomon_content(request):
		return (
			SolomonLifecycle.PUBLISHED,
			SolomonLifecycle.APPROVED,
			SolomonLifecycle.DRAFT,
		)
	return (SolomonLifecycle.PUBLISHED,)


def allowed_resource_visibility_values(request) -> tuple[str, ...]:
	if can_view_restricted_solomon_content(request):
		return (
			SolomonVisibility.PUBLIC,
			SolomonVisibility.AUTHENTICATED,
			SolomonVisibility.STAFF,
			SolomonVisibility.ADMIN,
		)
	return (
		SolomonVisibility.PUBLIC,
		SolomonVisibility.AUTHENTICATED,
	)


def allowed_scope_values(scope: str | None) -> tuple[str, ...]:
	candidate = str(scope or "").strip().lower()
	valid = {choice[0] for choice in SolomonScope.choices}

	if not candidate:
		return (SolomonScope.GLOBAL,)

	if candidate not in valid:
		return ()

	if candidate == SolomonScope.GLOBAL:
		return (SolomonScope.GLOBAL,)

	return (SolomonScope.GLOBAL, candidate)


def normalized_text(value: str | None) -> str:
	return str(value or "").strip()


def can_access_governance_queue(request) -> bool:
	"""
	Check if user can access governance review queue.

	Requires staff or admin access (fail-closed).
	"""
	user = getattr(request, "user", None)
	if not user or not getattr(user, "is_authenticated", False):
		return False

	if getattr(user, "is_staff", False) or getattr(user, "is_superuser", False):
		return True

	role_value = str(
		getattr(user, "role", "") or getattr(user, "role_code", "") or ""
	).strip().lower()
	return role_value in {"admin", "staff"}
