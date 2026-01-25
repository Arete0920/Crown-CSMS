from __future__ import annotations

from dataclasses import dataclass

from crown_api.models import HouseholdMember, Person


@dataclass(frozen=True)
class HouseholdAccess:
    is_staff: bool
    person: Person | None
    household_ids: set


def is_staff_user(user) -> bool:
    if not user or not getattr(user, "is_authenticated", False):
        return False
    return bool(getattr(user, "is_staff", False) or getattr(user, "is_superuser", False))


def resolve_person_for_user(user) -> Person | None:
    if not user or not getattr(user, "is_authenticated", False):
        return None

    email = (getattr(user, "email", None) or "").strip()
    if not email:
        return None

    return Person.objects.filter(email__iexact=email).first()


def resolve_household_access(request) -> HouseholdAccess:
    user = getattr(request, "user", None)
    staff = is_staff_user(user)

    if staff:
        return HouseholdAccess(is_staff=True, person=None, household_ids=set())

    person = resolve_person_for_user(user)
    if not person:
        return HouseholdAccess(is_staff=False, person=None, household_ids=set())

    household_ids = set(
        HouseholdMember.objects.filter(person=person).values_list("household_id", flat=True)
    )
    return HouseholdAccess(is_staff=False, person=person, household_ids=household_ids)
