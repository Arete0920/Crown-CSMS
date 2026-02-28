from django.core.management.base import BaseCommand
from aftercare.seed import seed_aftercare_config


class Command(BaseCommand):
    help = "Seed Aftercare default program config for a school."

    def add_arguments(self, parser):
        parser.add_argument("--school-id", type=int, required=True, help="Tenant school ID")

    def handle(self, *args, **opts):
        school_id = opts["school_id"]
        seed_aftercare_config(school_id=school_id)
        self.stdout.write(
            self.style.SUCCESS(f"Aftercare defaults seeded for school_id={school_id}")
        )
