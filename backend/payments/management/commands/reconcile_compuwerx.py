from django.core.management.base import BaseCommand

from payments.models import PaymentIntentRecord
from payments.providers import get_gateway


class Command(BaseCommand):
    help = "Reconcile unsettled Compuwerx intents by querying the provider."

    def handle(self, *args, **options):
        gateway = get_gateway("compuwerx")
        count = 0

        queryset = PaymentIntentRecord.objects.filter(
            provider="compuwerx",
            status__in=["created", "pending", "authorized", "settling"],
        ).order_by("id")

        for record in queryset:
            if not record.provider_intent_id:
                self.stdout.write(
                    self.style.WARNING(
                        f"[WARN] id={record.id} missing provider_intent_id"
                    )
                )
                continue

            result = gateway.fetch_status(provider_intent_id=record.provider_intent_id)
            if not result.ok:
                self.stdout.write(
                    self.style.WARNING(
                        f"[WARN] intent={record.provider_intent_id} error={result.error}"
                    )
                )
                continue

            record.status = result.status or record.status
            record.provider_payment_id = result.provider_payment_id or record.provider_payment_id
            record.response_payload = result.raw or {}
            record.save(update_fields=["status", "provider_payment_id", "response_payload", "updated_at"])
            count += 1

        self.stdout.write(self.style.SUCCESS(f"Reconciled {count} Compuwerx intents."))
