from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.compliance.models import ConsentAudit


class Command(BaseCommand):
    help = "Compliance retention enforcement scaffold."

    def handle(self, *args, **options):
        cutoff = timezone.now() - timedelta(days=3650)

        old_audits = ConsentAudit.objects.filter(accepted_at__lt=cutoff)

        count = old_audits.count()

        self.stdout.write(
            self.style.SUCCESS(
                f"Retention review complete. Records eligible: {count}"
            )
        )
