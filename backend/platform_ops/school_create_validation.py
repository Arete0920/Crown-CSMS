"""Strict, backward-compatible input contract for owner-only school creation.

Provisioning itself remains a separately authorized, audited one-job action.
No external payment provider may be configured through this endpoint.
"""
from __future__ import annotations

import re
from collections.abc import Mapping

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.validators import DomainNameValidator
from rest_framework import serializers

from tenants.models import TenantProfile


TIMEZONE_SHAPE = re.compile(
    r"^[A-Za-z][A-Za-z0-9_+\-]*(?:/[A-Za-z0-9_+\-]+){0,3}$"
)


class PlatformSchoolCreateSerializer(serializers.Serializer):
    """Validate an exact school-onboarding request before any database write."""

    name = serializers.CharField(max_length=255, min_length=1)
    slug = serializers.RegexField(
        regex=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
        max_length=128,
    )
    idempotency_key = serializers.CharField(max_length=255, min_length=1)
    domain = serializers.CharField(
        max_length=255, required=False, default="", allow_blank=True
    )
    plan_code = serializers.ChoiceField(
        choices=TenantProfile.PLAN_CHOICES,
        required=False,
        default="starter",
    )
    timezone = serializers.CharField(
        max_length=64, required=False, default="America/New_York"
    )
    payment_provider = serializers.ChoiceField(
        choices=TenantProfile.PAYMENT_PROVIDER_CHOICES,
        required=False,
        default="none",
    )

    def to_internal_value(self, data):
        """Reject unexpected, nested, and non-string values (DRF coerces scalars)."""
        if not isinstance(data, Mapping):
            raise serializers.ValidationError(
                {"non_field_errors": ["A JSON object is required."]}
            )
        extra_fields = set(data) - set(self.fields)
        if extra_fields:
            raise serializers.ValidationError(
                {"non_field_errors": ["Unsupported onboarding fields."]}
            )
        wrong_types = {
            key: ["Must be a string."]
            for key in data
            if not isinstance(data[key], str)
        }
        if wrong_types:
            raise serializers.ValidationError(wrong_types)
        return super().to_internal_value(data)

    def validate_domain(self, value: str) -> str:
        """Accept hostnames only; never a URL, credentials, port or path."""
        if value:
            try:
                DomainNameValidator(accept_idna=True)(value)
            except DjangoValidationError as exc:
                raise serializers.ValidationError(
                    "Enter a valid domain name, without a scheme or path."
                ) from exc
            if "." not in value:
                raise serializers.ValidationError(
                    "Enter a fully qualified domain name."
                )
        return value.lower()

    def validate_timezone(self, value: str) -> str:
        """Reject control/path input without depending on local OS tzdata.

        Timezone selection and canonical IANA verification remain part of the
        school setup workflow, rather than an assertion of installed tzdata.
        """
        if not TIMEZONE_SHAPE.fullmatch(value):
            raise serializers.ValidationError(
                "Enter an IANA-style timezone identifier."
            )
        return value
