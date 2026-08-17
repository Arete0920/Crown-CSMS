from uuid import UUID

from django.core.management.base import BaseCommand, CommandError

from aftercare.seed import seed_aftercare_config


class Command(BaseCommand):
    help = "Seed Aftercare default program config for a school UUID."

    def add_arguments(self, parser):
        parser.add_argument("--school-id", required=True, help="Canonical tenant school UUID")

    def handle(self, *args, **opts):
        try:
            school_id = UUID(opts["school_id"])
        except (TypeError, ValueError) as exc:
            raise CommandError("--school-id must be a valid UUID") from exc
        seed_aftercare_config(school_id=school_id)
        self.stdout.write(self.style.SUCCESS(f"Aftercare defaults seeded for school_id={school_id}"))
