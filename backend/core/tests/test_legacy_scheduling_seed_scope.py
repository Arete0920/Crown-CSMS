"""Verify that legacy scheduling seeding never enumerates arbitrary school years."""

from __future__ import annotations

import os
import uuid

import pytest
from django.core.management.base import CommandError

from core.models import AcademicYear, School
from scripts import seed_scheduling


@pytest.mark.django_db
def test_scheduling_seed_requires_explicit_school_before_any_writes(monkeypatch, settings):
    monkeypatch.setenv("CROWN_ENV", "local")
    monkeypatch.setenv("CROWN_ALLOW_LEGACY_SCHEDULING_SEED", "true")
    monkeypatch.delenv("CROWN_LEGACY_SCHEDULING_SCHOOL_ID", raising=False)
    monkeypatch.delenv("WEBSITE_HOSTNAME", raising=False)
    monkeypatch.delenv("WEBSITE_INSTANCE_ID", raising=False)
    monkeypatch.delenv("AZURE_ENVIRONMENT", raising=False)
    if settings.DATABASES["default"]["ENGINE"] != "django.db.backends.sqlite3":
        pytest.skip("This script is only supported with local SQLite")
    with pytest.raises(CommandError, match="SCHOOL_ID is required"):
        seed_scheduling.run()


@pytest.mark.django_db
def test_scheduling_seed_rejects_mixed_school_directory(monkeypatch, settings):
    monkeypatch.setenv("CROWN_ENV", "local")
    monkeypatch.setenv("CROWN_ALLOW_LEGACY_SCHEDULING_SEED", "true")
    monkeypatch.delenv("WEBSITE_HOSTNAME", raising=False)
    monkeypatch.delenv("WEBSITE_INSTANCE_ID", raising=False)
    monkeypatch.delenv("AZURE_ENVIRONMENT", raising=False)
    if settings.DATABASES["default"]["ENGINE"] != "django.db.backends.sqlite3":
        pytest.skip("This script is only supported with local SQLite")
    heritage = School.objects.create(name="Heritage Christian Academy")
    School.objects.create(name="Other Christian School")
    monkeypatch.setenv("CROWN_LEGACY_SCHEDULING_SCHOOL_ID", str(heritage.id))
    with pytest.raises(CommandError, match="single-school"):
        seed_scheduling.run()


@pytest.mark.django_db
def test_scheduling_seed_rejects_hosted_and_production(monkeypatch):
    monkeypatch.setenv("CROWN_ENV", "production")
    monkeypatch.setenv("CROWN_LEGACY_SCHEDULING_SCHOOL_ID", str(uuid.uuid4()))
    monkeypatch.setenv("CROWN_ALLOW_LEGACY_SCHEDULING_SEED", "true")
    with pytest.raises(CommandError, match="production"):
        seed_scheduling.run()
