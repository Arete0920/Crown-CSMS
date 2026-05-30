from django.core.management.base import BaseCommand

from sandbox_demo.services import seed_heritage_flagship


class Command(BaseCommand):
    help = "Seed or reset the flagship Heritage Christian Academy demo sandbox."

    def add_arguments(self, parser):
        parser.add_argument("--reset", action="store_true", help="Clear and rebuild Heritage demo data.")

    def handle(self, *args, **opts):
        metrics = seed_heritage_flagship(reset=bool(opts.get("reset")))
        for key, value in metrics.items():
            self.stdout.write(f"{key}: {value}")
        self.stdout.write(self.style.SUCCESS("Heritage flagship sandbox seed complete."))
