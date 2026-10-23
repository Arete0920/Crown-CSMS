"""Synthetic expired-token cleanup contract, without actual refresh secrets."""
import uuid
from datetime import timedelta
from io import StringIO

import pytest
from django.core.management import call_command
from django.utils import timezone

from crown_api.auth_models import CrownUser, LegacyRefreshConsumption


@pytest.mark.django_db
def test_cleanup_is_read_only_until_explicit_apply():
    user = CrownUser.objects.create(
        email="cleanup@example.invalid", password_hash="synthetic-not-a-password",
        role="staff", school_id=uuid.uuid4(), is_active=True,
    )
    now = timezone.now()
    expired = LegacyRefreshConsumption.objects.create(
        user=user, token_digest="a" * 64, expires_at=now - timedelta(days=2),
    )
    live = LegacyRefreshConsumption.objects.create(
        user=user, token_digest="b" * 64, expires_at=now + timedelta(days=2),
    )
    out = StringIO()
    call_command("purge_expired_legacy_refresh", stdout=out)
    assert "read-only" in out.getvalue()
    assert LegacyRefreshConsumption.objects.filter(pk=expired.pk).exists()
    assert LegacyRefreshConsumption.objects.filter(pk=live.pk).exists()

    out = StringIO()
    call_command("purge_expired_legacy_refresh", "--apply", "--batch-size", "1",
                 "--max-batches", "1", stdout=out)
    assert "deleted: 1" in out.getvalue()
    assert not LegacyRefreshConsumption.objects.filter(pk=expired.pk).exists()
    assert LegacyRefreshConsumption.objects.filter(pk=live.pk).exists()
