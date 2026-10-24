"""Tenant-bound core student lookup shared by legacy academic read adapters.

The caller must authorize its principal and selected tenant before any student
read. Compatibility household-to-family links never grant cross-school scope.
"""

from django.http import Http404

from core.models import HouseholdFamilyLink, Student as CoreStudent
from crown_api.access_households import resolve_household_access
from households.scoping import get_request_school_id


def get_core_student_or_404_for_request(*, request, student_id):
    """Resolve a student within the authenticated tenant and household authority.

    Generic Django staff status grants no cross-school lookup. Ordinary staff
    may read within the selected, authorized school. Parent access additionally
    requires a same-school household/family bridge. Cross-school and missing
    identities return the same non-disclosing 404.
    """
    school_id = get_request_school_id(request, required=True)
    student = CoreStudent.objects.filter(
        pk=student_id, school_id=school_id
    ).first()
    if student is None:
        raise Http404()

    access = resolve_household_access(request)
    if access.is_staff:
        return student

    if not HouseholdFamilyLink.objects.filter(
        school_id=school_id,
        family_id=student.family_id,
        family__school_id=school_id,
        household_id__in=access.household_ids,
    ).exists():
        raise Http404()

    return student
