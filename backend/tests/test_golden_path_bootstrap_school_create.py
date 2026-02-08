"""Test golden_path_bootstrap creates school when school_id provided."""
import pytest
from uuid import UUID
from django.core.management import call_command
from core.models import School


@pytest.fixture(autouse=True)
def _set_required_demo_password_env(monkeypatch):
    """Provide a dummy demo password required by golden_path_bootstrap."""
    monkeypatch.setenv("CROWN_DEMO_PASSWORD", "dummy-test-password")


@pytest.mark.django_db
def test_bootstrap_creates_school_when_id_provided():
    """
    PROOF: golden_path_bootstrap creates school if not exists when school_id provided.
    
    This test prevents regression of the bug where bootstrap would crash
    if school_id was provided but school didn't exist in DB.
    
    Context: Azure DEV Smoke depends on OPS reset workflow, which calls
    golden_path_bootstrap with a deterministic school_id. Before this fix,
    bootstrap would raise ValueError instead of creating the school.
    """
    # Use canonical demo school UUID from seed_a535.py
    test_school_id = UUID('a5351136-98fe-4d48-add0-fa8f62d9ceff')
    
    # Ensure school doesn't exist
    School.objects.filter(id=test_school_id).delete()
    assert not School.objects.filter(id=test_school_id).exists()
    
    # Run bootstrap with explicit school_id
    call_command(
        'golden_path_bootstrap',
        '--force',
        f'--school-id={test_school_id}',
        verbosity=0
    )
    
    # School should now exist
    school = School.objects.get(id=test_school_id)
    assert school.name == 'Crown Demo School'
    assert school.timezone == 'America/New_York'
    assert school.is_active is True


@pytest.mark.django_db
def test_bootstrap_idempotent_with_existing_school():
    """
    PROOF: golden_path_bootstrap is idempotent when school already exists.
    
    Running bootstrap twice with same school_id should not crash or duplicate.
    """
    test_school_id = UUID('a5351136-98fe-4d48-add0-fa8f62d9ceff')
    
    # First run: creates school
    School.objects.filter(id=test_school_id).delete()
    call_command(
        'golden_path_bootstrap',
        '--force',
        f'--school-id={test_school_id}',
        verbosity=0
    )
    
    # Second run: should not crash (idempotent)
    call_command(
        'golden_path_bootstrap',
        '--force',
        f'--school-id={test_school_id}',
        verbosity=0
    )
    
    # School still exists, no duplicates
    assert School.objects.filter(id=test_school_id).count() == 1
