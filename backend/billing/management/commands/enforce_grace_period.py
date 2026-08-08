"""
Management command: enforce_grace_period

Suspends households that have exceeded the configured grace period, one school
at a time under explicit tenant context.

Usage:
    python manage.py enforce_grace_period

Cron (daily at 03:00 UTC):
    0 3 * * * /app/.venv/bin/python /app/manage.py enforce_grace_period
"""
from django.core.management.base import BaseCommand

from billing.services_grace import enforce_grace_period
from core.models import School
from core.tenant_models import tenant_context


class Command(BaseCommand):
    help = "Suspend households that have exceeded the grace period after delinquency."

    def handle(self, *args, **options):
        self.stdout.write("Enforcing grace period by school tenant...")
        total_suspended = 0
        school_count = 0

        for school in School.objects.filter(is_active=True).iterator():
            with tenant_context(school):
                result = enforce_grace_period(school_id=school.id)
            total_suspended += result["suspended_count"]
            school_count += 1

        msg = (
            f"Grace period enforcement complete — schools: {school_count}; "
            f"suspended: {total_suspended}"
        )
        if total_suspended > 0:
            self.stdout.write(self.style.WARNING(msg))
        else:
            self.stdout.write(self.style.SUCCESS(msg))
