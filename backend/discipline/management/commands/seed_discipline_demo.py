from __future__ import annotations
from datetime import timedelta
import random
from django.core.management.base import BaseCommand
from django.utils import timezone

from discipline.models import DisciplineIncident, DisciplineAction
from core.models import School, Student

CATEGORIES = ["tardy","dress_code","disruption","disrespect","bullying","academic_dishonesty","other"]
SEVERITIES = ["minor","moderate","major"]
STATUSES = ["open","investigating","closed"]
LOCATIONS = ["Hallway","Classroom","Cafeteria","Gym","Chapel","Bus Line","Playground"]

SUMMARIES = [
    "Repeated tardiness to first period",
    "Dress code reminder needed",
    "Disrupted class with repeated talking",
    "Disrespectful tone toward staff",
    "Conflict with another student",
    "Academic integrity concern on quiz",
    "Inappropriate language reported",
]

DETAILS = [
    "Teacher documented the event and spoke with the student. Follow-up recommended.",
    "Student acknowledged expectations. Parent notification may be needed if repeated.",
    "Incident logged for pattern tracking and support planning.",
]

class Command(BaseCommand):
    help = "Seed demo discipline incidents (school-scoped)."

    def add_arguments(self, parser):
        parser.add_argument("--school-id", required=True)
        parser.add_argument("--count", type=int, default=16)

    def handle(self, *args, **opts):
        school_id = opts["school_id"]
        count = opts["count"]

        school = School.objects.get(id=school_id)
        students = list(Student.objects.filter(school=school)[:120])
        if not students:
            self.stdout.write(self.style.ERROR("No students found for school. Seed students first."))
            return

        created = 0
        now = timezone.now()

        for i in range(count):
            st = random.choice(students)
            occurred_at = now - timedelta(days=random.randint(0, 21), hours=random.randint(0, 6))
            category = random.choice(CATEGORIES)
            severity = random.choice(SEVERITIES)
            status = random.choice(STATUSES if i > 3 else ["open","investigating"])  # keep some open
            summary = random.choice(SUMMARIES)
            details = random.choice(DETAILS)

            inc = DisciplineIncident.objects.create(
                school=school,
                student=st,
                reported_by=None,
                assigned_to=None,
                occurred_at=occurred_at,
                location=random.choice(LOCATIONS),
                category=category,
                severity=severity,
                status=status,
                summary=summary,
                details=details,
                parent_notified=(status=="closed" and random.random() > 0.3),
                parent_notified_at=(occurred_at + timedelta(hours=2)) if (status=="closed" and random.random() > 0.5) else None,
            )
            DisciplineAction.objects.create(incident=inc, actor=None, action_type="created", note="Seeded incident")
            if inc.parent_notified:
                DisciplineAction.objects.create(incident=inc, actor=None, action_type="parent_notified", note="Parent notified (seed)")
            if inc.status == "closed":
                DisciplineAction.objects.create(incident=inc, actor=None, action_type="closed", note="Closed (seed)")

            created += 1

        self.stdout.write(self.style.SUCCESS(f"Seeded {created} discipline incidents for {school.name}"))
