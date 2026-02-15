from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command

from core.models import School, AcademicYear


class Command(BaseCommand):
    help = (
        "Seed the minimum deterministic demo dataset required by GOLDEN_PATH_CONTRACT. "
        "Idempotent by design. Prints SCHOOL_ID and ACADEMIC_YEAR_ID."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=10,
            help="Number of admissions applications to ensure exist (default: 10).",
        )

    def handle(self, *args, **options):
        count = int(options["count"])
        if count <= 0:
            raise CommandError("--count must be > 0")

        call_command("seed_demo_school")

        school = School.objects.order_by("created_at", "id").first()
        if not school:
            raise CommandError("No School found after seed_demo_school")

        year = (
            AcademicYear.objects.filter(school=school)
            .order_by("-is_current", "start_date", "id")
            .first()
        )
        if not year:
            raise CommandError("No AcademicYear found for School after seed_demo_school")

        call_command(
            "seed_admissions_demo",
            school_id=str(school.id),
            year_id=str(year.id),
            count=count,
        )

        self.stdout.write("LOCKDOWN_MINIMAL=OK")
        self.stdout.write(f"SCHOOL_ID={school.id}")
        self.stdout.write(f"ACADEMIC_YEAR_ID={year.id}")
        self.stdout.write(f"ADMISSIONS_COUNT_TARGET={count}")
