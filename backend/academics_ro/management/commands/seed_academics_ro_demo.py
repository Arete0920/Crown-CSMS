import uuid

from django.core.management.base import BaseCommand, CommandError
from django.db import router, transaction

from academics.models import Course, Section


DEMO_SCHOOL_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


class Command(BaseCommand):
    help = "Seed demo academics rows through tenant-integrity guarded ORM writers."

    def add_arguments(self, parser):
        parser.add_argument("--wipe", action="store_true")
        parser.add_argument("--term", default="2025-26 S1")

    def handle(self, *args, **opts):
        term = opts["term"]
        course_alias = router.db_for_write(Course)
        section_alias = router.db_for_write(Section)
        if section_alias != course_alias:
            raise CommandError(
                "Course and Section writes must route to the same database alias for atomic seeding."
            )

        using = course_alias
        courses_qs = Course.objects.using(using)
        sections_qs = Section.objects.using(using)

        with transaction.atomic(using=using):
            if opts["wipe"]:
                sections_qs.filter(school_id=DEMO_SCHOOL_ID).delete()
                courses_qs.filter(
                    school_id=DEMO_SCHOOL_ID, code__startswith="DEMO-"
                ).delete()
                self.stdout.write(self.style.WARNING("Wiped existing demo data."))

            courses = [
                ("DEMO-ALG1", "Algebra I"),
                ("DEMO-ENG9", "English 9"),
                ("DEMO-BIO", "Biology"),
            ]

            created = 0
            updated = 0
            for code, name in courses:
                course, _ = courses_qs.update_or_create(
                    school_id=DEMO_SCHOOL_ID,
                    code=code,
                    defaults={"name": name},
                )
                section, was_created = sections_qs.update_or_create(
                    school_id=DEMO_SCHOOL_ID,
                    course=course,
                    term=term,
                    defaults={
                        "teacher_name": f"Ms. {name.split()[0]} Teacher",
                        "grade_band": "9-12",
                    },
                )
                created += int(was_created)
                updated += int(not was_created)
                self.stdout.write(
                    f"{'Created' if was_created else 'Updated'} section: {name} ({code})"
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded academics demo sections: created={created}, updated={updated}."
            )
        )
