"""Explicit isolation guard and fictional identities for legacy local demo scripts.

These older scripts use crown_api's unscoped household and finance models.
Never run them against a hosted, production, or customer-data database.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from django.conf import settings
from django.core.management.base import CommandError


@dataclass(frozen=True)
class FixtureGuardian:
    first_name: str
    last_name: str
    email: str
    phone: str


@dataclass(frozen=True)
class FixtureHousehold:
    name: str
    code: str
    city: str
    state: str
    primary: FixtureGuardian
    secondary: FixtureGuardian


LEGACY_HOUSEHOLDS = (
    FixtureHousehold(
        name="The Hartwell Family",
        code="HART",
        city="Fairview",
        state="PA",
        primary=FixtureGuardian(
            "Elena", "Hartwell", "elena.hartwell@heritage.example.org",
            "302-555-0101",
        ),
        secondary=FixtureGuardian(
            "Marcus", "Hartwell", "marcus.hartwell@heritage.example.org",
            "302-555-0102",
        ),
    ),
    FixtureHousehold(
        name="The Carter Family",
        code="CART",
        city="Fairview",
        state="PA",
        primary=FixtureGuardian(
            "Nathan", "Carter", "nathan.carter@heritage.example.org",
            "302-555-0103",
        ),
        secondary=FixtureGuardian(
            "Miriam", "Carter", "miriam.carter@heritage.example.org",
            "302-555-0104",
        ),
    ),
)


def require_local_legacy_fixture_seed(operation: str) -> None:
    """Reject operations unless the operator explicitly selected local SQLite."""
    labels = {
        str(os.getenv(name, "")).strip().lower()
        for name in (
            "CROWN_ENV", "DJANGO_ENV", "ENVIRONMENT", "APP_ENV", "AZURE_ENVIRONMENT"
        )
        if os.getenv(name, "").strip()
    }
    if labels.intersection({"prod", "production", "live"}):
        raise CommandError(f"{operation}: production environment is prohibited")
    if any(os.getenv(name) for name in (
        "WEBSITE_HOSTNAME", "WEBSITE_INSTANCE_ID", "AZURE_ENVIRONMENT"
    )):
        raise CommandError(f"{operation}: hosted environments are prohibited")
    if os.getenv("CROWN_ENV", "").strip().lower() not in {"local", "test"}:
        raise CommandError(f"{operation}: CROWN_ENV must be local or test")
    if os.getenv("CROWN_ALLOW_LEGACY_FIXTURE_SEED", "").strip().lower() != "true":
        raise CommandError(
            f"{operation}: CROWN_ALLOW_LEGACY_FIXTURE_SEED=true is required"
        )
    if settings.DATABASES["default"]["ENGINE"] != "django.db.backends.sqlite3":
        raise CommandError(f"{operation}: only isolated SQLite is permitted")


def require_isolated_fixture_directory(Household, Person) -> None:
    """Refuse mixed legacy customer/demo directories before inserting anything."""
    names = [fixture.name for fixture in LEGACY_HOUSEHOLDS]
    emails = [
        guardian.email
        for fixture in LEGACY_HOUSEHOLDS
        for guardian in (fixture.primary, fixture.secondary)
    ]
    if Household.objects.exclude(household_name__in=names).exists():
        raise CommandError(
            "Legacy fixture database contains an unrelated household; "
            "use an isolated demo database"
        )
    if Person.objects.exclude(email__in=emails).exists():
        raise CommandError(
            "Legacy fixture database contains an unrelated person; "
            "use an isolated demo database"
        )
