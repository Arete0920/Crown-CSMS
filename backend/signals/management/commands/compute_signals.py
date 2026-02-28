from django.core.management.base import BaseCommand
from signals.engine import compute_snapshots_for_school, compute_board_metrics


class Command(BaseCommand):
    help = "Compute deterministic Signal Engine snapshots + Board metrics for a school."

    def add_arguments(self, parser):
        parser.add_argument("--school-id", type=int, required=True, help="Tenant school ID")

    def handle(self, *args, **opts):
        school_id = opts["school_id"]
        self.stdout.write(f"Computing signals for school_id={school_id}…")
        compute_snapshots_for_school(school_id=school_id)
        compute_board_metrics(school_id=school_id)
        self.stdout.write(
            self.style.SUCCESS(
                f"Done — signal snapshots + board metrics computed for school_id={school_id}"
            )
        )
