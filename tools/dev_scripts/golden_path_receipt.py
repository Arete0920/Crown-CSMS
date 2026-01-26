from __future__ import annotations

import argparse
import os
import sys
from uuid import UUID

import django


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--school-id", required=True)
    parser.add_argument("--invoice-id", required=True)
    parser.add_argument("--aid-award-id", required=True)
    parser.add_argument("--aid-application-id", required=True)
    args = parser.parse_args()

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    backend_root = os.path.join(repo_root, "backend")
    sys.path.insert(0, backend_root)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "crown_api.settings")
    django.setup()

    from django.db.models import Sum

    from aid.models import AidApplication, AidAward
    from billing.models import BillingAuditEvent, Invoice
    from core.models import School
    from ledger.models import Allocation, Charge, Payment

    school_id = UUID(str(args.school_id))
    invoice_id = UUID(str(args.invoice_id))

    school = School.objects.get(id=school_id)
    invoice = Invoice.objects.get(id=invoice_id)
    charge = Charge.objects.get(id=invoice.ledger_charge_id)

    alloc_sum = Allocation.objects.filter(charge=charge).aggregate(total=Sum("amount")).get("total")
    latest_payment = Payment.objects.filter(school_id=school_id).order_by("-created_at").values("id", "reference", "amount").first()
    latest_audit = (
        BillingAuditEvent.objects.filter(school_id=school_id)
        .order_by("-created_at")
        .values("created_at", "action", "entity_type", "entity_id")
        .first()
    )

    try:
        award_id_int = int(str(args.aid_award_id))
    except ValueError:
        award_id_int = None

    try:
        app_id_int = int(str(args.aid_application_id))
    except ValueError:
        app_id_int = None

    award = (
        AidAward.objects.filter(id=award_id_int).values("id", "decision_status", "ledger_entry_id", "decided_at").first()
        if award_id_int is not None
        else None
    )
    aid_app = (
        AidApplication.objects.filter(id=app_id_int).values("id", "status").first()
        if app_id_int is not None
        else None
    )

    print(f"school= {school.name} {school.id}")
    print(
        "invoice= "
        + str(
            {
                "id": str(invoice.id),
                "total_amount": str(invoice.total_amount),
                "ledger_charge_id": str(invoice.ledger_charge_id),
            }
        )
    )
    print(f"allocations_total_for_charge= {alloc_sum}")
    print(f"latest_payment= {latest_payment}")
    print(f"latest_billing_audit= {latest_audit}")
    print(f"award= {award}")
    print(f"aid_app= {aid_app}")


if __name__ == "__main__":
    main()
