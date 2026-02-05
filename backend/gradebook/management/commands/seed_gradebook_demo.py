from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count
from decimal import Decimal
import random

from gradebook.models import GradeEntry
from academics.models import Section


class Command(BaseCommand):
    help = "Seed demo gradebook data (safe to re-run)."

    def add_arguments(self, parser):
        parser.add_argument("--school-id", required=True)
        parser.add_argument("--sections", type=int, default=2)
        parser.add_argument("--students", type=int, default=12)
        parser.add_argument("--assignments", type=int, default=6)
        parser.add_argument("--wipe", action="store_true")

    @transaction.atomic
    def handle(self, *args, **opts):
        school_id = opts["school_id"]
        n_sections = opts["sections"]
        n_students = opts["students"]
        n_assignments = opts["assignments"]

        if opts["wipe"]:
            GradeEntry.objects.filter(school_id=school_id).delete()
            self.stdout.write("Existing gradebook data wiped.")

        assignments = [
            ("Assignment 1", Decimal("10.0")),
            ("Assignment 2", Decimal("20.0")),
            ("Assignment 3", Decimal("25.0")),
            ("Assignment 4", Decimal("15.0")),
            ("Assignment 5", Decimal("30.0")),
            ("Assignment 6", Decimal("10.0")),
        ][:n_assignments]

        def roster_students(section):
            roster = []
            for e in section.enrollments.all():
                if hasattr(e, "first_name") and hasattr(e, "last_name"):
                    roster.append(e)
                elif hasattr(e, "student"):
                    roster.append(e.student)
            return roster

        sections = (
            Section.objects
            .filter(school_id=school_id)
            .annotate(rcount=Count("enrollments"))
            .filter(rcount__gt=0)
            .order_by("id")
        )

        if not sections:
            self.stderr.write("Missing sections or students.")
            return

        created = 0
        updated = 0

        for section in sections:
            roster = roster_students(section)
            if not roster:
                continue

            rng = random.Random(str(section.id))

            for student in roster:
                for name, possible in assignments:
                    pct = Decimal(str(rng.uniform(0.80, 1.00)))
                    earned = (possible * pct).quantize(Decimal("0.01"))

                    _, was_created = GradeEntry.objects.update_or_create(
                        school_id=school_id,
                        section=section,
                        student=student,
                        assignment_name=name,
                        defaults={
                            "points_earned": earned,
                            "points_possible": possible,
                        },
                    )
                    if was_created:
                        created += 1
                    else:
                        updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"GradeEntry seeded across sections. created={created}, updated={updated}"
        ))
