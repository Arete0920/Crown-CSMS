"""Restricted legacy demo invoice/payment fixtures.

Never enumerate every household. The old crown_api models are not tenant
scoped, so this command requires an isolated local SQLite database and exactly
the two explicitly designated fictional household scenarios.
"""

from __future__ import annotations

import logging
import os
from datetime import date

logger = logging.getLogger(__name__)


def run() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crown_api.settings")
    import django
    django.setup()

    from django.core.management.base import CommandError
    from django.db import transaction
    from crown_api.models import Household, Invoice, Payment, Person
    from crown_api.models_households import HouseholdMember, ROLE_PRIMARY_GUARDIAN
    from core.legacy_demo_seed_safety import (
        LEGACY_HOUSEHOLDS,
        require_isolated_fixture_directory,
        require_local_legacy_fixture_seed,
    )

    require_local_legacy_fixture_seed("seed_finance")
    with transaction.atomic():
        require_isolated_fixture_directory(Household, Person)
        households = list(Household.objects.all())
        if len(households) != len(LEGACY_HOUSEHOLDS):
            raise CommandError(
                "The two fictional households are required; seed_households first"
            )
        by_name = {household.household_name: household for household in households}

        expected_invoices = []
        expected_payments = []
        for scenario in LEGACY_HOUSEHOLDS:
            household = by_name.get(scenario.name)
            if household is None:
                raise CommandError("Missing a configured fictional household")
            if not HouseholdMember.objects.filter(
                household=household,
                person__email=scenario.primary.email,
                role=ROLE_PRIMARY_GUARDIAN,
            ).exists():
                raise CommandError(
                    "Missing a verified fictional guardian; refusing invoice creation"
                )

            invoice_prefix = f"HCA-FIX-{scenario.code}"
            expected_invoices.extend((
                (
                    f"{invoice_prefix}-2026-01", household,
                    150000, Invoice.STATUS_OPEN,
                    date(2026, 1, 1), date(2026, 2, 1),
                ),
                (
                    f"{invoice_prefix}-2025-12", household,
                    150000, Invoice.STATUS_PAID,
                    date(2025, 12, 1), date(2026, 1, 1),
                ),
            ))
            expected_payments.append((
                f"{invoice_prefix}-PMT-01", household,
                150000, date(2026, 1, 15),
            ))

        invoice_numbers = [record[0] for record in expected_invoices]
        payment_refs = [record[0] for record in expected_payments]
        if Invoice.objects.exclude(invoice_number__in=invoice_numbers).exists():
            raise CommandError("Unrelated legacy invoices exist: use isolated demo database")
        if Payment.objects.exclude(payment_reference__in=payment_refs).exists():
            raise CommandError("Unrelated legacy payments exist: use isolated demo database")

        # Prevalidate every existing fixture before making the first write.
        for number, household, amount, status, issued, due in expected_invoices:
            existing = Invoice.objects.filter(invoice_number=number).first()
            if existing is not None and (
                existing.household_id != household.id
                or existing.amount_cents != amount
                or existing.status != status
                or existing.issued_date != issued
                or existing.due_date != due
            ):
                raise CommandError("Existing fictional invoice differs from approved scenario")

        for ref, household, amount, paid_at in expected_payments:
            existing = Payment.objects.filter(payment_reference=ref).first()
            if existing is not None and (
                existing.household_id != household.id
                or existing.amount_cents != amount
                or existing.payment_date != paid_at
            ):
                raise CommandError("Existing fictional payment differs from approved scenario")

        for number, household, amount, status, issued, due in expected_invoices:
            Invoice.objects.get_or_create(
                invoice_number=number,
                defaults={
                    "household": household,
                    "amount_cents": amount,
                    "status": status,
                    "issued_date": issued,
                    "due_date": due,
                },
            )
        for ref, household, amount, paid_at in expected_payments:
            Payment.objects.get_or_create(
                payment_reference=ref,
                defaults={
                    "household": household,
                    "amount_cents": amount,
                    "payment_date": paid_at,
                },
            )

        logger.info("Seeded %d fictional invoices and %d fictional payments",
                    len(expected_invoices), len(expected_payments))


if __name__ == "__main__":
    run()
