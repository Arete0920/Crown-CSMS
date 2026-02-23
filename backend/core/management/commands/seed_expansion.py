"""
Idempotent seed command for expansion module demo data.
Usage: python manage.py seed_expansion [--school-name "Crown Academy"]
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, date


class Command(BaseCommand):
    help = "Seed demo data for HR, Advancement, PDHub, and Safety modules."

    def add_arguments(self, parser):
        parser.add_argument(
            "--school-name",
            default=None,
            help="Name of the school to seed into. Defaults to first school in DB.",
        )

    def handle(self, *args, **options):
        from schools.models import School

        name = options.get("school_name")
        if name:
            school = School.objects.filter(name=name).first()
            if not school:
                self.stderr.write(f"School '{name}' not found.")
                return
        else:
            school = School.objects.first()
            if not school:
                self.stderr.write("No schools in database. Run seed_schools first.")
                return

        self.stdout.write(f"Seeding expansion modules for: {school.name}")

        self._seed_hr(school)
        self._seed_advancement(school)
        self._seed_pdhub(school)
        self._seed_safety(school)

        self.stdout.write(self.style.SUCCESS("Done — expansion seed complete."))

    # ------------------------------------------------------------------
    def _seed_hr(self, school):
        from hr.models import Employee

        employees = [
            {"first_name": "Alice", "last_name": "Carter",  "department": "Academics",  "role": "Teacher",           "email": "a.carter@crown.example",  "date_hired": date(2018, 8, 15), "active": True},
            {"first_name": "Bob",   "last_name": "Nguyen",  "department": "Operations", "role": "Facilities Manager","email": "b.nguyen@crown.example",  "date_hired": date(2020, 1, 7),  "active": True},
            {"first_name": "Carol", "last_name": "Davis",   "department": "Finance",    "role": "Accountant",        "email": "c.davis@crown.example",   "date_hired": date(2019, 3, 20), "active": True},
            {"first_name": "Dan",   "last_name": "Smith",   "department": "Academics",  "role": "Teacher",           "email": "d.smith@crown.example",   "date_hired": date(2016, 8, 20), "active": False},
            {"first_name": "Eve",   "last_name": "Johnson", "department": "Admissions", "role": "Counselor",         "email": "e.johnson@crown.example", "date_hired": date(2021, 6, 1),  "active": True},
        ]
        for data in employees:
            obj, created = Employee.objects.get_or_create(
                school_id=school.id, email=data["email"], defaults=data
            )
            if created:
                self.stdout.write(f"  HR: created employee {obj.email}")

    # ------------------------------------------------------------------
    def _seed_advancement(self, school):
        from advancement.models import Donor, Campaign

        campaigns = [
            {"name": "Annual Fund 2026", "goal": 500000, "raised": 312000, "active": True},
            {"name": "Capital Campaign",  "goal": 2000000, "raised": 875000, "active": True},
            {"name": "Scholarship Fund",  "goal": 100000,  "raised": 100000, "active": False},
        ]
        for data in campaigns:
            obj, created = Campaign.objects.get_or_create(
                school_id=school.id, name=data["name"], defaults=data
            )
            if created:
                self.stdout.write(f"  Advancement: created campaign '{obj.name}'")

        donors = [
            {"name": "John & Mary Williams", "email": "jmwilliams@example.com", "total_donated": 25000, "last_gift_date": date(2025, 11, 1)},
            {"name": "The Chen Family",       "email": "chen.family@example.com", "total_donated": 10000, "last_gift_date": date(2025, 12, 15)},
            {"name": "Anonymous",             "email": "anon1@example.com",        "total_donated": 5000,  "last_gift_date": date(2026, 1, 3)},
        ]
        for data in donors:
            obj, created = Donor.objects.get_or_create(
                school_id=school.id, email=data["email"], defaults=data
            )
            if created:
                self.stdout.write(f"  Advancement: created donor '{obj.name}'")

    # ------------------------------------------------------------------
    def _seed_pdhub(self, school):
        from pdhub.models import PDResource, PDSession

        resources = [
            {"title": "Trauma-Informed Practices", "category": "Wellbeing",       "url": "https://example.com/trauma-informed"},
            {"title": "Differentiated Instruction",  "category": "Pedagogy",       "url": "https://example.com/diff-instruction"},
            {"title": "EdTech Integration Guide",    "category": "Technology",     "url": "https://example.com/edtech"},
        ]
        for data in resources:
            obj, created = PDResource.objects.get_or_create(
                school_id=school.id, title=data["title"], defaults=data
            )
            if created:
                self.stdout.write(f"  PDHub: created resource '{obj.title}'")

        now = timezone.now()
        sessions = [
            {"title": "Spring PD Day — Literacy Focus", "session_date": now + timedelta(days=14), "duration_hours": 6, "facilitator": "Dr. Rosa Park",   "rating": None},
            {"title": "Technology Bootcamp",             "session_date": now - timedelta(days=30), "duration_hours": 4, "facilitator": "Mr. Lee Chen",    "rating": 4.5},
            {"title": "SEL Workshop",                    "session_date": now - timedelta(days=90), "duration_hours": 3, "facilitator": "Ms. Tina Hughes", "rating": 4.8},
        ]
        for data in sessions:
            obj, created = PDSession.objects.get_or_create(
                school_id=school.id, title=data["title"], defaults=data
            )
            if created:
                self.stdout.write(f"  PDHub: created session '{obj.title}'")

    # ------------------------------------------------------------------
    def _seed_safety(self, school):
        from safety.models import IncidentReport

        today = date.today()
        incidents = [
            {"title": "Playground fall", "description": "Student fell from climbing structure, minor scrape.",  "severity": "low",    "status": "closed",      "incident_date": today - timedelta(days=45)},
            {"title": "Fight in hallway","description": "Two students involved in altercation near gym.",        "severity": "medium", "status": "under_review","incident_date": today - timedelta(days=10)},
            {"title": "Fire alarm (false)","description": "False alarm triggered in science wing.",             "severity": "low",    "status": "closed",      "incident_date": today - timedelta(days=5)},
            {"title": "Unauthorized access","description": "Unknown individual entered grounds via side gate.", "severity": "high",   "status": "open",        "incident_date": today - timedelta(days=2)},
        ]
        for data in incidents:
            obj, created = IncidentReport.objects.get_or_create(
                school_id=school.id, title=data["title"], defaults=data
            )
            if created:
                self.stdout.write(f"  Safety: created incident '{obj.title}'")
