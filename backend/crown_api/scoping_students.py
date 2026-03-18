"""
Student access scoping helpers.

Bridges household-based access control (from resolve_household_access) 
to the new core.models.Student, which uses family FK instead of household.

Uses HouseholdFamilyLink to link families to households for parent scoping.
"""

from django.http import Http404
from core.models import HouseholdFamilyLink, Student as CoreStudent
from crown_api.access_households import resolve_household_access


def get_core_student_or_404_for_request(*, request, student_id):
    """
    Retrieve a core.models.Student with household-based access control.
    
    - Staff: can access any student
    - Parents: can only access student if family is linked to their household via HouseholdFamilyLink
    - Returns: core.models.Student instance
    - Raises: Http404 if not found or out of scope (prevents existence leak)
    """
    access = resolve_household_access(request)
    
    # Start from the target core student
    student = CoreStudent.objects.filter(pk=student_id).first()
    if not student:
        raise Http404()
    
    # Staff can access any student
    if access.is_staff:
        return student
    
    # Parent: enforce household scope via HouseholdFamilyLink family←→household link
    family_is_linked = HouseholdFamilyLink.objects.filter(
        family_id=student.family_id,
        household_id__in=access.household_ids,
    ).exists()
    
    if not family_is_linked:
        raise Http404()
    
    return student
