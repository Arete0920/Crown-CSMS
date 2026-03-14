from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils.dateparse import parse_datetime

from payments.models import ProviderPayoutBatch, ProviderPayoutEntry
from payments.providers import get_gateway


class Command(BaseCommand):
    help = "Sync Compuwerx payout batches into Crown."

    def handle(self, *args, **options):
        gateway = get_gateway("compuwerx")
        result = gateway.list_payout_batches()

        if not result.ok:
            self.stdout.write(self.style.ERROR(result.error))
            return

        count = 0
        for row in result.payouts or []:
            metadata = row.get("metadata", {}) or {}
            payout_id = row.get("payout_id") or row.get("id")
            if not payout_id:
                continue

            batch, _ = ProviderPayoutBatch.objects.update_or_create(
                payout_id=payout_id,
                defaults={
                    "school_id": metadata.get("school_id") or row.get("school_id") or None,
                    "provider": "compuwerx",
                    "status": row.get("status") or "",
                    "gross_amount": Decimal(str(row.get("gross_amount") or "0")),
                    "fee_amount": Decimal(str(row.get("fee_amount") or "0")),
                    "net_amount": Decimal(str(row.get("net_amount") or "0")),
                    "currency": row.get("currency") or "USD",
                    "expected_payment_count": int(row.get("expected_payment_count") or 0),
                    "settled_at": parse_datetime(row.get("settled_at")) if row.get("settled_at") else None,
                    "payload": row,
                },
            )

            batch.entries.all().delete()

            for entry in row.get("entries") or []:
                entry_md = entry.get("metadata", {}) or {}
                ProviderPayoutEntry.objects.create(
                    batch=batch,
                    provider_payment_id=entry.get("payment_id", ""),
                    provider_intent_id=entry.get("intent_id", ""),
                    invoice_id=entry_md.get("invoice_id"),
                    household_id=entry_md.get("household_id"),
                    gross_amount=Decimal(str(entry.get("gross_amount") or "0")),
                    fee_amount=Decimal(str(entry.get("fee_amount") or "0")),
                    net_amount=Decimal(str(entry.get("net_amount") or "0")),
                    currency=entry.get("currency") or "USD",
                    payload=entry,
                )

            count += 1

        self.stdout.write(self.style.SUCCESS(f"Synced {count} payout batches."))
