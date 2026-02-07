"""
Canonical helpers for deterministic seed/bootstrap operations.

This module provides single-source-of-truth helpers for creating
deterministic demo/test resources. All smoke tests, bootstrap scripts,
and OPS endpoints should use these helpers to prevent drift.
"""
from uuid import UUID
from core.models import School


def ensure_deterministic_school(school_id: UUID) -> tuple[School, bool]:
    """
    Idempotently ensure a school exists with deterministic defaults.
    
    Used by:
    - ensure_ci_user endpoint (smoke tests)
    - golden_path_bootstrap management command
    - Any other OPS/seed operations requiring deterministic school creation
    
    Args:
        school_id: Explicit UUID for the school (must be deterministic)
    
    Returns:
        tuple of (School instance, created: bool)
    
    Raises:
        ValueError: If school_id is not a valid UUID
    
    Deterministic defaults:
        - name: 'Crown Demo School'
        - timezone: 'America/New_York'
        - is_active: True
    
    Example:
        >>> from uuid import UUID
        >>> school_id = UUID('a5351136-98fe-4d48-add0-fa8f62d9ceff')
        >>> school, created = ensure_deterministic_school(school_id)
        >>> assert school.name == 'Crown Demo School'
    """
    if not isinstance(school_id, UUID):
        raise ValueError(f"school_id must be UUID, got {type(school_id)}")
    
    school, created = School.objects.get_or_create(
        id=school_id,
        defaults={
            'name': 'Crown Demo School',
            'timezone': 'America/New_York',
            'is_active': True,
        }
    )
    
    return school, created
