from django.core.management.base import BaseCommand, CommandError

from core.models import School
from signals.engine import compute_board_metrics, compute_snapshots_for_school


class Command(BaseCommand):
    help = "Compute deterministic Signal Engine snapshots + Board metrics for a school."

    def add_arguments(self, parser):
        parser.add_argument(
            "--school",
            required=True,
            help="UUID primary key of the tenant School record",
        )

    def handle(self, *args, **opts):
        school_pk = opts["school"]
        try:
            school = School.objects.get(pk=school_pk)
        except School.DoesNotExist:
            raise CommandError(f"School not found: {school_pk!r}")

        self.stdout.write(f"Computing signals for school={school.name} ({school.pk})...")
        compute_snapshots_for_school(school)
        compute_board_metrics(school)
        self.stdout.write(
            self.style.SUCCESS(
                f"Done -- signal snapshots + board metrics computed for {school.name}"
            )
        )
