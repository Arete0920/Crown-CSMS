from crown_api.billing_api.permissions import has_finance_runtime_role


def user_can_access_household_finance(user, household_id) -> bool:
    """
    Finance/admin users get broad access.
    Parent/family access is allowed only when the user is actually tied to the household.

    This helper is defensive because projects often model household linkage differently.
    It checks several common patterns safely.
    """
    if not user or not getattr(user, "is_authenticated", False):
        return False

    if has_finance_runtime_role(user):
        return True

    # Pattern 1: direct household_id on user
    if str(getattr(user, "household_id", "")) == str(household_id):
        return True

    # Pattern 2: one-to-many relation like user.households
    households_rel = getattr(user, "households", None)
    if households_rel is not None:
        try:
            if households_rel.filter(id=household_id).exists():
                return True
        except Exception:
            pass

    # Pattern 3: profile-based relation
    profile = getattr(user, "profile", None)
    if profile is not None and str(getattr(profile, "household_id", "")) == str(household_id):
        return True

    return False
