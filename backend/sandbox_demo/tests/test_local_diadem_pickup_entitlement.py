"""Fictional Diadem pickup seed must preserve existing entitlement decisions."""
import pytest
from django.core.management.base import CommandError

from core.models import School
from subscriptions.models import EntitlementOverride, Feature
from sandbox_demo.management.commands.seed_local_diadem_pickup import (
    ensure_local_diadem_entitlement,
)

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("existing", [False, None])
def test_denied_or_unset_existing_override_is_not_activated(existing):
    school = School.objects.create(name="Fictional denied Diadem school")
    feature = Feature.objects.create(key="diadem.daycare", name="Fictional childcare")
    original = EntitlementOverride.objects.create(
        school_id=school.pk, feature=feature, enabled=existing,
    )
    with pytest.raises(CommandError, match="not explicitly enabled"):
        ensure_local_diadem_entitlement(school, feature)
    original.refresh_from_db()
    assert original.enabled is existing
    assert EntitlementOverride.objects.filter(school_id=school.pk, feature=feature).count() == 1


def test_explicit_existing_grant_is_preserved():
    school = School.objects.create(name="Fictional authorized Diadem school")
    feature = Feature.objects.create(key="diadem.daycare", name="Fictional childcare")
    original = EntitlementOverride.objects.create(
        school_id=school.pk, feature=feature, enabled=True, limit_int=3,
    )
    result = ensure_local_diadem_entitlement(school, feature)
    original.refresh_from_db()
    assert result.pk == original.pk
    assert original.enabled is True
    assert original.limit_int == 3


def test_only_absent_fictional_grant_may_be_created():
    school = School.objects.create(name="Fictional new Diadem school")
    feature = Feature.objects.create(key="diadem.daycare", name="Fictional childcare")
    created = ensure_local_diadem_entitlement(school, feature)
    assert created.enabled is True
    assert EntitlementOverride.objects.filter(school_id=school.pk, feature=feature).count() == 1


@pytest.mark.parametrize("operation", ["build", "verify"])
def test_direct_scenario_entrypoints_refuse_nonlocal_database_before_io(monkeypatch, operation):
    """Direct imports cannot skip the command-level local SQLite guard."""
    from sandbox_demo.management.commands import seed_local_diadem_pickup as pickup

    calls = []
    def deny_nonlocal():
        calls.append("checked")
        raise CommandError("Nonlocal database is forbidden")

    monkeypatch.setattr(pickup, "_require_isolated_local_database", deny_nonlocal)
    with pytest.raises(CommandError, match="Nonlocal database is forbidden"):
        if operation == "build":
            pickup.build_scenario()
        else:
            pickup.verify_scenario()
    assert calls == ["checked"]


@pytest.mark.parametrize("operation", ["build", "verify"])
def test_direct_scenario_entrypoints_require_explicit_local_launcher_flags(monkeypatch, operation):
    """The guarded helper rejects missing local-launcher flags before DB access."""
    from sandbox_demo.management.commands import seed_local_diadem_pickup as pickup

    monkeypatch.setattr(pickup, "_require_isolated_local_database", lambda: None)
    monkeypatch.delenv("VITE_LOCAL_DEMO", raising=False)
    monkeypatch.delenv("DJANGO_ENV", raising=False)
    with pytest.raises(CommandError, match="restricted to the isolated local Heritage launcher"):
        if operation == "build":
            pickup.build_scenario()
        else:
            pickup.verify_scenario()
