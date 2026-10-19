"""Regression tests for isolation of the legacy, non-tenant-keyed seed models."""

from __future__ import annotations

import pytest
from django.core.management.base import CommandError

from core.legacy_demo_seed_safety import (
    LEGACY_HOUSEHOLDS,
    require_local_legacy_fixture_seed,
)
from crown_api.models import Household, Invoice, Payment, Person
from scripts import seed_finance, seed_households


@pytest.fixture
def local_legacy_seed(monkeypatch, settings):
    monkeypatch.setenv("CROWN_ENV", "local")
    monkeypatch.setenv("CROWN_ALLOW_LEGACY_FIXTURE_SEED", "true")
    monkeypatch.delenv("WEBSITE_HOSTNAME", raising=False)
    monkeypatch.delenv("WEBSITE_INSTANCE_ID", raising=False)
    monkeypatch.delenv("AZURE_ENVIRONMENT", raising=False)
    if settings.DATABASES["default"]["ENGINE"] != "django.db.backends.sqlite3":
        pytest.skip("Legacy fixture seed requires isolated SQLite")


def test_legacy_seed_requires_explicit_operator_opt_in(monkeypatch):
    monkeypatch.setenv("CROWN_ENV", "local")
    monkeypatch.delenv("CROWN_ALLOW_LEGACY_FIXTURE_SEED", raising=False)
    with pytest.raises(CommandError, match="CROWN_ALLOW_LEGACY_FIXTURE_SEED"):
        require_local_legacy_fixture_seed("seed_finance")


def test_legacy_seed_rejects_hosted_environments(monkeypatch):
    monkeypatch.setenv("CROWN_ENV", "local")
    monkeypatch.setenv("CROWN_ALLOW_LEGACY_FIXTURE_SEED", "true")
    monkeypatch.setenv("WEBSITE_HOSTNAME", "crown-api-dev.azurewebsites.net")
    with pytest.raises(CommandError, match="hosted"):
        require_local_legacy_fixture_seed("seed_finance")


def test_legacy_seed_rejects_conflicting_production_label(monkeypatch):
    monkeypatch.setenv("CROWN_ENV", "local")
    monkeypatch.setenv("DJANGO_ENV", "production")
    monkeypatch.setenv("CROWN_ALLOW_LEGACY_FIXTURE_SEED", "true")
    with pytest.raises(CommandError, match="production"):
        require_local_legacy_fixture_seed("seed_households")


@pytest.mark.django_db
def test_legacy_households_are_fictional_repeatable_and_reserved(local_legacy_seed):
    seed_households.run()
    seed_households.run()
    assert Household.objects.count() == 2
    assert Person.objects.count() == 4
    assert {
        row.household_name for row in Household.objects.all()
    } == {fixture.name for fixture in LEGACY_HOUSEHOLDS}
    assert not Person.objects.filter(last_name="Megahan").exists()
    assert all(
        p.email.endswith("@heritage.example.org") and "-555-01" in p.phone
        for p in Person.objects.all()
    )


@pytest.mark.django_db
def test_legacy_finance_seeds_exactly_two_guarded_households(local_legacy_seed):
    seed_households.run()
    seed_finance.run()
    seed_finance.run()
    assert Invoice.objects.count() == 4
    assert Payment.objects.count() == 2
    assert all(
        inv.invoice_number.startswith("HCA-FIX-")
        for inv in Invoice.objects.all()
    )


@pytest.mark.django_db
def test_legacy_finance_refuses_unrelated_household_without_writes(local_legacy_seed):
    seed_households.run()
    Household.objects.create(household_name="Actual Family Record")
    with pytest.raises(CommandError, match="unrelated household"):
        seed_finance.run()
    assert Invoice.objects.count() == 0
    assert Payment.objects.count() == 0


@pytest.mark.django_db
def test_legacy_finance_refuses_nonfixture_invoice_before_writing(local_legacy_seed):
    seed_households.run()
    Invoice.objects.create(
        household=Household.objects.first(),
        invoice_number="CUSTOMER-INVOICE-001",
        amount_cents=12345,
        status=Invoice.STATUS_OPEN,
    )
    with pytest.raises(CommandError, match="Unrelated legacy invoices"):
        seed_finance.run()
    assert Invoice.objects.count() == 1
    assert Payment.objects.count() == 0
