"""Tests for the sandbox_lockdown_personas management command."""
from io import StringIO

import pytest
from django.core.management import call_command

from sandbox_demo.catalog import SANDBOX_SCHOOLS, get_persona
from sandbox_demo.services import ensure_demo_school, ensure_persona_user

@pytest.mark.django_db
def test_lockdown_sets_unusable_passwords_and_is_idempotent(settings):
    settings.CROWN_SANDBOX_FALLBACK_PASSWORD = ""
    school = ensure_demo_school(SANDBOX_SCHOOLS["heritage-core"])

    admin = ensure_persona_user(school, get_persona("school_admin"))
    parent = ensure_persona_user(school, get_persona("parent"))

    # Simulate legacy deployed state: shared demo password set on existing users.
    for user in (admin, parent):
        user.set_password("CrownDemo!2026")
        user.save(update_fields=["password"])
    assert admin.has_usable_password() and parent.has_usable_password()

    out = StringIO()
    call_command("sandbox_lockdown_personas", stdout=out)

    admin.refresh_from_db()
    parent.refresh_from_db()
    assert not admin.has_usable_password()
    assert not parent.has_usable_password()
    assert "locked:" in out.getvalue()

    # Idempotent second run: nothing left to lock.
    out2 = StringIO()
    call_command("sandbox_lockdown_personas", stdout=out2)
    assert "locked: 0" in out2.getvalue()

@pytest.mark.django_db
def test_lockdown_dry_run_changes_nothing(settings):
    settings.CROWN_SANDBOX_FALLBACK_PASSWORD = ""
    school = ensure_demo_school(SANDBOX_SCHOOLS["heritage-core"])
    admin = ensure_persona_user(school, get_persona("school_admin"))
    admin.set_password("CrownDemo!2026")
    admin.save(update_fields=["password"])

    out = StringIO()
    call_command("sandbox_lockdown_personas", "--dry-run", stdout=out)

    admin.refresh_from_db()
    assert admin.has_usable_password()
    assert "would-lock" in out.getvalue()
