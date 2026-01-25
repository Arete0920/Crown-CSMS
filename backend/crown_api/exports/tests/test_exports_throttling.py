import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.cache import cache

from rest_framework.test import APIClient
from rest_framework import throttling as drf_throttling

from core.models import School


pytestmark = pytest.mark.django_db


@pytest.fixture
def finance_user():
    school = School.objects.create(name="Test School")
    User = get_user_model()
    u = User.objects.create_user(username="throttle_user", password="pass12345!")
    if hasattr(u, "school_id"):
        setattr(u, "school_id", school.id)
        u.save(update_fields=["school_id"])

    g, _ = Group.objects.get_or_create(name="Business Manager")
    u.groups.add(g)
    return u


def test_exports_throttle_triggers_for_user(finance_user):
    # Make the test deterministic: lower the rate limits for this test only.
    # DRF binds THROTTLE_RATES at import time, so patch the rate tables directly.
    rates = {
        "exports_user_minute": "2/min",
        "exports_user_hour": "2/hour",
        "exports_ip_minute": "100/min",  # avoid IP throttle dominating this test
    }

    cache.clear()

    client = APIClient()
    client.force_authenticate(user=finance_user)

    drf_throttling.UserRateThrottle.THROTTLE_RATES = rates
    drf_throttling.SimpleRateThrottle.THROTTLE_RATES = rates

    r1 = client.get("/api/exports/invoices.csv")
    r2 = client.get("/api/exports/invoices.csv")
    r3 = client.get("/api/exports/invoices.csv")

    # First two requests should not be throttled.
    assert r1.status_code != 429
    assert r2.status_code != 429

    # Third request should be throttled.
    assert r3.status_code == 429
