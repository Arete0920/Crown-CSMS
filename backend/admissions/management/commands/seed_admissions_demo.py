from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from core.models import AcademicYear, Family, School
from admissions.models import AdmissionsApplication


class Command(BaseCommand):
    help = "Seed deterministic admissions applications for demo/gate checks"

    def add_arguments(self, parser):
        parser.add_argument("--school-id", required=True)
        parser.add_argument("--year-id", required=True)
        parser.add_argument("--count", type=int, default=10)

    def handle(self, *args, **options):
        school_id = options["school_id"]
        year_id = options["year_id"]
        target_count = options["count"]

        if target_count < 1:
            raise CommandError("--count must be >= 1")

        try:
            school = School.objects.get(pk=school_id)
        except School.DoesNotExist as exc:
            raise CommandError(f"School not found: {school_id}") from exc

        try:
            year = AcademicYear.objects.get(pk=year_id, school=school)
        except AcademicYear.DoesNotExist as exc:
            raise CommandError(f"Academic year not found for school: {year_id}") from exc

        marker = "seed_admissions_demo"
        existing_seeded = AdmissionsApplication.objects.filter(
            school=school,
            academic_year=year,
            notes_internal=marker,
        ).count()

        needed = target_count - existing_seeded
        if needed <= 0:
            self.stdout.write(self.style.SUCCESS(
                f"seed_admissions_demo: already seeded {existing_seeded} applications"
            ))
            return

        families = list(Family.objects.filter(school=school).order_by("created_at", "id")[:needed])
        if len(families) < needed:
            raise CommandError(
                f"Not enough families to seed admissions applications (needed={needed}, found={len(families)})"
            )

        status_cycle = [
            AdmissionsApplication.STATUS_SUBMITTED,
            AdmissionsApplication.STATUS_UNDER_REVIEW,
            AdmissionsApplication.STATUS_NEEDS_INFO,
            AdmissionsApplication.STATUS_ACCEPTED,
            AdmissionsApplication.STATUS_WAITLISTED,
        ]

        created = 0
        for index, family in enumerate(families):
            status = status_cycle[index % len(status_cycle)]
            AdmissionsApplication.objects.create(
                school=school,
                academic_year=year,
                family=family,
                status=status,
                submitted_at=timezone.now(),
                notes_internal=marker,
                essay_received=True,
                transcript_received=True,
                recommendations_received=2,
            )
            created += 1

        total = AdmissionsApplication.objects.filter(school=school, academic_year=year).count()
        self.stdout.write(self.style.SUCCESS(
            f"seed_admissions_demo: created={created}, seeded_marker_total={existing_seeded + created}, applications_total={total}"
        ))
