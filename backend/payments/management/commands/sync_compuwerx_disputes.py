from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime

from payments.models import ProviderDispute
from payments.providers import get_gateway


class Command(BaseCommand):
    help = "Sync Compuwerx disputes into Crown."

    def handle(self, *args, **options):
        gateway = get_gateway("compuwerx")
        result = gateway.list_disputes()

        if not result.ok:
            self.stdout.write(self.style.ERROR(result.error))
            return

        count = 0
        for row in result.disputes or []:
            metadata = row.get("metadata", {}) or {}
            dispute_id = row.get("dispute_id") or row.get("id")
            if not dispute_id:
                continue

            dispute, _ = ProviderDispute.objects.update_or_create(
                dispute_id=dispute_id,
                defaults={
                    "school_id": metadata.get("school_id") or row.get("school_id") or None,
                    "provider": "compuwerx",
                    "provider_payment_id": row.get("payment_id", ""),
                    "provider_intent_id": row.get("intent_id", ""),
                    "invoice_id": metadata.get("invoice_id"),
                    "household_id": metadata.get("household_id"),
                    "amount": Decimal(str(row.get("amount") or "0")),
                    "currency": row.get("currency") or "USD",
                    "reason": row.get("reason") or "",
                    "status": row.get("status") or "open",
                    "opened_at": parse_datetime(row.get("opened_at")) if row.get("opened_at") else None,
                    "closed_at": parse_datetime(row.get("closed_at")) if row.get("closed_at") else None,
                    "payload": row,
                },
            )
            count += 1

        self.stdout.write(self.style.SUCCESS(f"Synced {count} disputes."))
