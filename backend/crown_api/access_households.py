from __future__ import annotations

from dataclasses import dataclass

from core.permissions import user_has_permission
from crown_api.models import HouseholdMember, Person
from crown_api.models_identity import UserPersonLink


@dataclass(frozen=True)
class HouseholdAccess:
    is_staff: bool
    person: Person | None
    household_ids: set


def resolve_person_for_user(user) -> Person | None:
    if not user or not getattr(user, "is_authenticated", False):
        return None

    # Prefer explicit identity linkage over email heuristics.
    try:
        link = user.person_link
    except UserPersonLink.DoesNotExist:
        link = None
    if link is not None:
        return link.person

    email = (getattr(user, "email", None) or "").strip()
    if not email:
        return None

    # Compatibility fallback only. Authorization remains household/tenant scoped.
    return Person.objects.filter(email__iexact=email).first()


def resolve_household_access(request) -> HouseholdAccess:
    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False):
        return HouseholdAccess(is_staff=False, person=None, household_ids=set())

    school = getattr(request, "school", None)
    staff = bool(
        school is not None
        and user_has_permission(user, "communications.view", school=school)
    )

    if staff:
        return HouseholdAccess(is_staff=True, person=None, household_ids=set())

    person = resolve_person_for_user(user)
    if not person:
        return HouseholdAccess(is_staff=False, person=None, household_ids=set())

    household_ids = set(
        HouseholdMember.objects.filter(person=person).values_list("household_id", flat=True)
    )
    return HouseholdAccess(is_staff=False, person=person, household_ids=household_ids)
