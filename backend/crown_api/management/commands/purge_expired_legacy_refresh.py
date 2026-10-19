"""Bounded, opt-in purge of expired one-time legacy refresh token digests."""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from crown_api.auth_models import LegacyRefreshConsumption


class Command(BaseCommand):
    help = "Inspect or purge already-expired legacy refresh consumption digests."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true",
                            help="Explicitly delete expired digest records")
        parser.add_argument("--batch-size", type=int, default=500)
        parser.add_argument("--max-batches", type=int, default=20)

    def handle(self, *args, **options):
        batch_size = options["batch_size"]
        max_batches = options["max_batches"]
        if not 1 <= batch_size <= 1000 or not 1 <= max_batches <= 100:
            raise CommandError("Invalid bounded cleanup batch settings")

        cutoff = timezone.now()
        expired = LegacyRefreshConsumption.objects.filter(expires_at__lte=cutoff)

        if not options["apply"]:
            sample = list(expired.order_by("expires_at", "pk").values_list(
                "pk", flat=True
            )[:batch_size])
            self.stdout.write(
                f"read-only: at least {len(sample)} expired digest records sampled; no deletion"
            )
            return

        count = 0
        for _ in range(max_batches):
            with transaction.atomic():
                identifiers = list(expired.order_by("expires_at", "pk").values_list(
                    "pk", flat=True
                )[:batch_size])
                if not identifiers:
                    break
                deleted, _ = LegacyRefreshConsumption.objects.filter(
                    pk__in=identifiers, expires_at__lte=cutoff
                ).delete()
                count += deleted

        self.stdout.write(self.style.SUCCESS(
            f"expired legacy refresh digest records deleted: {count}"
        ))
