from __future__ import annotations
from datetime import date, timedelta
import random
from django.core.management.base import BaseCommand
from servicehours.models import ServiceEntry
from core.models import School, Student

CATEGORIES = ["Chapel Support","Community Service","Missions","Campus Care","Tutoring","Food Pantry"]
ORGS = ["Local Food Pantry","Church Partner","Community Center","Neighborhood Outreach","School Event"]

class Command(BaseCommand):
    help = "Seed demo service hours entries (school-scoped)."

    def add_arguments(self, parser):
        parser.add_argument("--school-id", required=True)
        parser.add_argument("--count", type=int, default=60)

    def handle(self, *args, **opts):
        school = School.objects.get(id=opts["school_id"])
        students = list(Student.objects.filter(school=school)[:200])
        if not students:
            self.stdout.write(self.style.ERROR("No students found for school. Seed students first."))
            return

        today = date.today()
        created = 0
        for i in range(opts["count"]):
            st = random.choice(students)
            d = today - timedelta(days=random.randint(0, 90))
            hrs = round(random.choice([0.5, 1.0, 1.5, 2.0, 3.0]), 2)
            status = "approved" if random.random() > 0.35 else "pending"

            ServiceEntry.objects.create(
                school=school,
                student=st,
                date=d,
                hours=hrs,
                category=random.choice(CATEGORIES),
                organization=random.choice(ORGS),
                supervisor_name="",
                supervisor_contact="",
                notes="Seeded entry",
                status=status,
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded {created} service hour entries for {school.name}"))
