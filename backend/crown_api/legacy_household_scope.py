"""Fail-closed tenant attribution for legacy schoolless household records.

CROWN's legacy Household and Student rows have no school key. A current,
consistent HouseholdFamilyLink is the only supported school attribution. A
household linked to multiple schools or mismatched family ownership is never
authorized by a selected-school header alone.
"""

from core.models import HouseholdFamilyLink


def tenant_household_ids(school_id):
    """Select household IDs whose *every* recorded family attribution agrees."""
    inconsistent = HouseholdFamilyLink.objects.exclude(
        school_id=school_id, family__school_id=school_id
    ).values("household_id")
    return (
        HouseholdFamilyLink.objects.filter(
            school_id=school_id,
            family__school_id=school_id,
        )
        .exclude(household_id__in=inconsistent)
        .values("household_id")
    )
