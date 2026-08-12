from crown_api.billing_api.permissions import has_finance_runtime_role
from households.models import Household


def user_can_access_household_finance(user, household_id, school_id) -> bool:
    """Authorize household Finance access within the current school boundary."""
    if not user or not getattr(user, "is_authenticated", False):
        return False

    if not Household.objects.filter(id=household_id, school_id=school_id).exists():
        return False

    if has_finance_runtime_role(user):
        return True

    if str(getattr(user, "household_id", "")) == str(household_id):
        return True

    households_rel = getattr(user, "households", None)
    filter_method = getattr(households_rel, "filter", None)
    if callable(filter_method) and filter_method(id=household_id, school_id=school_id).exists():
        return True

    profile = getattr(user, "profile", None)
    if profile is not None and str(getattr(profile, "household_id", "")) == str(household_id):
        return True

    return False
