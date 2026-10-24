from __future__ import annotations

from dataclasses import dataclass

from crown_api.models import HouseholdMember, Person
from crown_api.models_households import GUARDIAN_ROLES
from crown_api.models_identity import UserPersonLink


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

    try:
        link = user.person_link
    except UserPersonLink.DoesNotExist:
        link = None
    # The explicit authenticated-user link is the sole authority. A matching
    # email is not proof of person/household identity, particularly because
    # this compatibility Person directory has no school ownership column.
    # Fail closed until a verified UserPersonLink is provisioned.
    if link is None:
        return None
    return link.person


def resolve_household_access(request, *, allowed_roles=None) -> HouseholdAccess:
    """Resolve only guardian household access unless a domain explicitly widens it.

    Emergency contacts and pickup delegates cannot inherit protected student
    records, private communications or financial access. Billing callers may
    additionally authorize explicitly financially responsible members.
    """
    user = getattr(request, "user", None)
    staff = is_staff_user(user)

    if staff:
        return HouseholdAccess(is_staff=True, person=None, household_ids=set())

    person = resolve_person_for_user(user)
    if not person:
        return HouseholdAccess(is_staff=False, person=None, household_ids=set())

    permitted = tuple(GUARDIAN_ROLES if allowed_roles is None else allowed_roles)
    if not permitted:
        return HouseholdAccess(is_staff=False, person=person, household_ids=set())

    household_ids = set(
        HouseholdMember.objects.filter(
            person=person, role__in=permitted
        ).values_list("household_id", flat=True)
    )
    return HouseholdAccess(is_staff=False, person=person, household_ids=household_ids)
