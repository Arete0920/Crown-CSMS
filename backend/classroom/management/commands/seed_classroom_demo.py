import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from core.models import School, Student, Staff
from classroom.models import (
    Classroom,
    ClassroomEnrollment,
    ClassroomAnnouncement,
    ClassroomAssignment,
    ClassroomSeatingChart,
)


class Command(BaseCommand):
    help = "Seed deterministic classroom demo data for the selected school (requires X-School-Id when using APIs)."

    def add_arguments(self, parser):
        parser.add_argument("--school-id", required=False, help="School UUID. If omitted, uses first School().")
        parser.add_argument("--classrooms", type=int, default=6)
        parser.add_argument("--students-per", type=int, default=18)
        parser.add_argument("--seed", type=int, default=26)

    @transaction.atomic
    def handle(self, *args, **opts):
        random.seed(int(opts["seed"]))

        school_id = opts.get("school_id")
        school = None
        if school_id:
            school = School.objects.filter(pk=school_id).first()
        if not school:
            school = School.objects.first()

        if not school:
            raise SystemExit("No School found to seed against.")

        # Students/Staff must exist already (heritage realism pack creates them)
        students = list(Student.objects.filter(school=school).order_by("id")[: (opts["classrooms"] * opts["students_per"])])
        staff = list(Staff.objects.filter(school=school).order_by("id")[: max(1, opts["classrooms"])])

        if not students:
            raise SystemExit("No Students found for this school. Run your main seed first.")
        if not staff:
            # If staff isn't present, we still seed classrooms without a teacher.
            staff = []

        # Clear prior classroom demo data for this school (scoped)
        Classroom.objects.filter(school=school).delete()

        for i in range(opts["classrooms"]):
            teacher = staff[i % len(staff)] if staff else None
            grade = str(9 + (i % 4))
            c = Classroom.objects.create(
                school=school,
                name=f"{grade}th Grade Homeroom {(chr(65+i))}",
                room=f"{chr(65+(i%4))}{200+(i*3)}",
                grade_level=grade,
                homeroom_teacher=teacher,
                is_active=True,
                created_at=timezone.now(),
            )

            roster = students[i * opts["students_per"] : (i + 1) * opts["students_per"]]
            for s in roster:
                ClassroomEnrollment.objects.create(classroom=c, student=s)

            today = date.today()
            
            # Announcements: recent + older for demo
            ClassroomAnnouncement.objects.create(
                classroom=c,
                title="Welcome & Weekly Focus",
                body="This week: character, diligence, and prepared hearts. Reminder: bring your reading notebook.",
                pinned=True,
                created_at=timezone.now() - timedelta(hours=6),
            )
            ClassroomAnnouncement.objects.create(
                classroom=c,
                title="Quiz Friday",
                body="Short quiz at the start of class. Study notes from Monday–Wednesday.",
                pinned=False,
                created_at=timezone.now() - timedelta(days=3),
            )
            
            # Assignments: overdue, due today, upcoming
            ClassroomAssignment.objects.create(
                classroom=c,
                title="Chapter 5 Summary",
                description="One-page summary of Chapter 5. Due by 11:59 PM.",
                due_date=today - timedelta(days=1),  # Past due
                points=40,
                status="published",
            )
            ClassroomAssignment.objects.create(
                classroom=c,
                title="Reading Reflection",
                description="1 page reflection: key idea + one question you still have.",
                due_date=today,  # Due today
                points=50,
                status="published",
            )
            ClassroomAssignment.objects.create(
                classroom=c,
                title="Memory Verse",
                description="Recite the weekly verse during homeroom check-in.",
                due_date=today + timedelta(days=3),  # Upcoming
                points=25,
                status="published",
            )

            # Simple seating chart: rows/cols grid, fill left-to-right
            rows, cols = 4, 6
            seats = []
            idx = 0
            for r in range(rows):
                for col in range(cols):
                    if idx < len(roster):
                        seats.append({"r": r, "c": col, "student_id": str(roster[idx].id)})
                        idx += 1
            ClassroomSeatingChart.objects.create(
                classroom=c,
                layout={"rows": rows, "cols": cols, "seats": seats},
                updated_at=timezone.now(),
            )

        self.stdout.write(self.style.SUCCESS(f"✅ Seeded {opts['classrooms']} classrooms for school={school.id}"))
