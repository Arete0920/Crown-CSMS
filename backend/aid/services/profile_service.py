"""
Jireh annual financial-profile services.

Design goals:
- one canonical family financial profile per school/year;
- explicit provenance for every financial line item;
- safe prior-year carry-forward without treating old values as current verification;
- deterministic review signals for human decision support.
"""

from __future__ import annotations

from types import SimpleNamespace

from django.db import transaction
from django.utils import timezone

from aid.models import (
    AidAuditEvent,
    AidDocument,
    AidFinancialLineItem,
    AidFinancialProfile,
    AidHouseholdMember,
)


SEVERITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


def build_engine_application(app):
    """
    Return a lightweight engine input.

    If a canonical financial profile is attached, its structured totals become
    authoritative for economic fields. Legacy aggregate fields remain the
    compatibility fallback until all callers have migrated.
    """
    totals = None
    if getattr(app, "financial_profile_id", None):
        totals = app.financial_profile.totals()

    return SimpleNamespace(
        income_annual_cents=(
            totals["income_annual_cents"] if totals is not None else app.income_annual_cents
        ),
        assets_cents=totals["assets_cents"] if totals is not None else app.assets_cents,
        liabilities_cents=(
            totals["liabilities_cents"] if totals is not None else app.liabilities_cents
        ),
        statement_of_faith_score=app.statement_of_faith_score,
        church_involvement_score=app.church_involvement_score,
        family_values_survey_score=app.family_values_survey_score,
        pastoral_reference_score=app.pastoral_reference_score,
        pog_preassessment_score=app.pog_preassessment_score,
    )


@transaction.atomic
def carry_forward_profile(*, source_profile, academic_year, actor_user=None):
    """
    Create the next annual profile from a prior profile.

    Only a profile with explicit reuse consent may be carried forward.
    Financial values retain provenance but become unverified for the new year.
    """
    if not source_profile.consent_to_reuse:
        raise ValueError("Prior-year profile does not permit reuse.")

    profile, created = AidFinancialProfile.objects.get_or_create(
        school=source_profile.school,
        academic_year=academic_year,
        family=source_profile.family,
        defaults={
            "carried_forward_from": source_profile,
            "verification_status": AidFinancialProfile.STATUS_DRAFT,
            "consent_to_reuse": source_profile.consent_to_reuse,
        },
    )
    if not created:
        return profile

    AidHouseholdMember.objects.bulk_create(
        [
            AidHouseholdMember(
                profile=profile,
                role=member.role,
                first_name=member.first_name,
                last_name=member.last_name,
                relationship=member.relationship,
                student=member.student,
                lives_in_household=member.lives_in_household,
                financially_responsible=member.financially_responsible,
            )
            for member in source_profile.household_members.all()
        ]
    )

    AidFinancialLineItem.objects.bulk_create(
        [
            AidFinancialLineItem(
                profile=profile,
                category=item.category,
                subcategory=item.subcategory,
                label=item.label,
                annual_amount_cents=item.annual_amount_cents,
                source_type=AidFinancialLineItem.SOURCE_PRIOR_YEAR,
                source_reference=f"profile:{source_profile.id}/line:{item.id}",
                verified=False,
                verified_at=None,
                verified_by=None,
            )
            for item in source_profile.line_items.all()
        ]
    )

    AidAuditEvent.log(
        school=profile.school,
        entity_type=AidAuditEvent.ENTITY_PROFILE,
        entity_id=profile.id,
        action="PROFILE_CARRIED_FORWARD",
        actor_user=actor_user,
        details={
            "source_profile_id": str(source_profile.id),
            "academic_year_id": str(academic_year.id),
            "line_item_count": profile.line_items.count(),
            "household_member_count": profile.household_members.count(),
        },
    )
    return profile


def build_review_signals(app):
    """
    Produce deterministic, explainable review flags for an aid application.

    These signals do not decide eligibility or awards. They identify records
    that deserve human attention and provide the evidence behind each flag.
    """
    signals = []
    profile = getattr(app, "financial_profile", None)

    def add(code, severity, summary, **context):
        signals.append(
            {
                "code": code,
                "severity": severity,
                "summary": summary,
                "context": context,
            }
        )

    if profile is None:
        add(
            "MISSING_FINANCIAL_PROFILE",
            "HIGH",
            "No canonical annual financial profile is attached to this application.",
        )
    else:
        if profile.confirmed_at is None:
            add(
                "PROFILE_NOT_CONFIRMED",
                "HIGH",
                "The family has not confirmed the current-year financial profile.",
            )

        unverified_count = profile.line_items.filter(verified=False).count()
        if unverified_count:
            add(
                "UNVERIFIED_FINANCIAL_ITEMS",
                "HIGH",
                "One or more current-year financial items have not been verified.",
                count=unverified_count,
            )

        if not profile.household_members.exists():
            add(
                "HOUSEHOLD_NOT_STRUCTURED",
                "MEDIUM",
                "No household members have been recorded in the annual profile.",
            )

        totals = profile.totals()
        legacy = {
            "income_annual_cents": int(app.income_annual_cents or 0),
            "assets_cents": int(app.assets_cents or 0),
            "liabilities_cents": int(app.liabilities_cents or 0),
        }
        mismatches = {
            key: {"profile": totals[key], "legacy": legacy[key]}
            for key in legacy
            if legacy[key] and totals[key] != legacy[key]
        }
        if mismatches:
            add(
                "LEGACY_AGGREGATE_MISMATCH",
                "MEDIUM",
                "Legacy application aggregates differ from the canonical financial profile.",
                fields=mismatches,
            )

        prior = profile.carried_forward_from
        if prior is not None:
            prior_income = prior.totals()["income_annual_cents"]
            current_income = totals["income_annual_cents"]
            if prior_income > 0:
                change_bps = int(((current_income - prior_income) * 10_000) / prior_income)
                if abs(change_bps) >= 2000:
                    add(
                        "MATERIAL_INCOME_CHANGE",
                        "MEDIUM",
                        "Household income changed by at least 20% from the prior profile.",
                        prior_income_cents=prior_income,
                        current_income_cents=current_income,
                        change_bps=change_bps,
                    )

        business_income = profile.line_items.filter(
            category=AidFinancialLineItem.CATEGORY_INCOME,
            subcategory__icontains="business",
        ).exists()
        tax_return_received = AidDocument.objects.filter(
            aid_application=app,
            doc_type=AidDocument.DOC_TAX_RETURN,
            received=True,
        ).exists()
        if business_income and not tax_return_received:
            add(
                "BUSINESS_INCOME_DOCUMENTATION",
                "MEDIUM",
                "Business income is reported without a received tax return.",
            )

    missing_documents = list(
        AidDocument.objects.filter(aid_application=app, received=False)
        .values_list("doc_type", flat=True)
        .distinct()
    )
    if missing_documents:
        add(
            "MISSING_DOCUMENTS",
            "HIGH",
            "Required supporting documents remain outstanding.",
            document_types=missing_documents,
        )

    signals.sort(key=lambda item: (SEVERITY_ORDER[item["severity"]], item["code"]))
    return signals
