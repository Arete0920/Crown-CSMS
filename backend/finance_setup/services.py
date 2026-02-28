"""
finance_setup.services
======================
All mutating operations on finance policy live here.
Views are thin; every real decision happens in this module.
"""

from django.db import transaction

from .models import (
    DiscountPolicy,
    ExtendedCarePolicy,
    FinancePolicyVersion,
    FinancialAidPolicy,
    PaymentPlanPolicy,
    TuitionPolicy,
)


class PolicyLockedError(Exception):
    """
    Raised when an edit is attempted against a locked FinancePolicyVersion.
    Views catch this and return HTTP 409.
    """
    pass


def _strip_version(payload: dict) -> dict:
    """
    Remove top-level version metadata keys from a validated payload dict.
    What remains are the sub-policy dicts.
    """
    return {k: v for k, v in payload.items() if k != "academic_year"}


@transaction.atomic
def upsert_finance_policies(school_id: int, academic_year: str, payload: dict) -> FinancePolicyVersion:
    """
    Create or update the full policy set for (school_id, academic_year).

    Raises PolicyLockedError if the version is already locked.

    The payload must be pre-validated by FinanceSetupWizardPayloadSerializer
    (i.e. call serializer.is_valid() before calling this function).
    """
    version = (
        FinancePolicyVersion.objects
        .select_for_update()
        .filter(school_id=school_id, academic_year=academic_year)
        .first()
    )

    if version is None:
        version = FinancePolicyVersion.objects.create(
            school_id=school_id,
            academic_year=academic_year,
        )

    if version.is_locked:
        raise PolicyLockedError(
            f"Finance policy for school {school_id} / {academic_year} is locked and cannot be edited."
        )

    tuition_data = payload.get("tuition", {})
    discounts_data = payload.get("discounts", {})
    aid_data = payload.get("aid", {})
    payment_plans_data = payload.get("payment_plans", {})
    extended_care_data = payload.get("extended_care", {})

    _upsert_related(TuitionPolicy, version, "version", tuition_data)
    _upsert_related(DiscountPolicy, version, "version", discounts_data)
    _upsert_related(FinancialAidPolicy, version, "version", aid_data)
    _upsert_related(PaymentPlanPolicy, version, "version", payment_plans_data)
    _upsert_related(ExtendedCarePolicy, version, "version", extended_care_data)

    return version


def _upsert_related(model_class, version, fk_field, data: dict):
    """
    Create or update a OneToOne related policy model.
    """
    obj, _ = model_class.objects.get_or_create(**{fk_field: version})
    for field, value in data.items():
        setattr(obj, field, value)
    obj.save()


@transaction.atomic
def lock_finance_policies(school_id: int, academic_year: str, locked_by: str = None) -> FinancePolicyVersion:
    """
    Permanently lock a policy version. Idempotent if already locked.
    Raises ValueError if no policy exists yet for the given school/year.
    """
    version = (
        FinancePolicyVersion.objects
        .select_for_update()
        .filter(school_id=school_id, academic_year=academic_year)
        .first()
    )

    if version is None:
        raise ValueError(
            f"No finance policy found for school {school_id} / {academic_year}. Configure it first."
        )

    if not version.is_locked:
        version.lock(locked_by=locked_by)

    return version


def get_policy_snapshot(school_id: int, academic_year: str):
    """
    Return a FinancePolicyVersion with all related objects pre-fetched,
    or None if none exists.
    """
    return (
        FinancePolicyVersion.objects
        .select_related(
            "tuition",
            "discounts",
            "aid",
            "payment_plans",
            "extended_care",
        )
        .filter(school_id=school_id, academic_year=academic_year)
        .first()
    )
