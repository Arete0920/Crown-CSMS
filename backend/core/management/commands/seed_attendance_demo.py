from __future__ import annotations
import datetime
import random

from django.core.management import BaseCommand
from django.db import transaction

from core.models import School, Student
from crown_api.models_academics_core import AttendanceRecord


class Command(BaseCommand):
    help = "Seed deterministic attendance records for Heritage demo (fixed week: Feb 9-13, 2026)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--school-id",
            type=str,
            help="UUID of the school (defaults to Crown Demo Christian Academy if not provided)",
        )

    def handle(self, *args, **opts):
        school_id = opts.get("school_id")
        
        # Resolve school
        if school_id:
            school = School.objects.filter(pk=school_id).first()
            if not school:
                raise RuntimeError(f"School {school_id} not found")
        else:
            school = School.objects.filter(name="Crown Demo Christian Academy").order_by("-created_at", "id").first()
            if not school:
                raise RuntimeError("No demo school found")
        
        self.stdout.write(f"Seeding attendance for school_id={school.id}")
        
        # Fixed deterministic week: Feb 9-13, 2026 (Mon-Fri)
        week_dates = [
            datetime.date(2026, 2, 9),   # Monday
            datetime.date(2026, 2, 10),  # Tuesday
            datetime.date(2026, 2, 11),  # Wednesday
            datetime.date(2026, 2, 12),  # Thursday
            datetime.date(2026, 2, 13),  # Friday
        ]
        
        # Get active students (deterministic order)
        students = Student.objects.filter(school=school, status="ACTIVE").order_by("id")
        
        student_count = students.count()
        if not student_count:
            self.stdout.write(self.style.WARNING("No active students found; skipping attendance seed"))
            return
        
        self.stdout.write(f"Found {student_count} active students")
        
        # Deterministic status assignment (seed-based randomness for realism)
        random.seed(42)  # Fixed seed for deterministic behavior
        
        created_count = 0
        updated_count = 0
        
        with transaction.atomic():
            for student in students:
                for date in week_dates:
                    # Deterministic status: 92% present, 5% tardy, 3% absent
                    roll = random.random()
                    if roll < 0.92:
                        status = AttendanceRecord.STATUS_PRESENT
                        minutes_late = None
                    elif roll < 0.97:
                        status = AttendanceRecord.STATUS_TARDY
                        minutes_late = random.choice([5, 10, 15])
                    else:
                        status = AttendanceRecord.STATUS_ABSENT
                        minutes_late = None
                    
                    # Idempotent upsert (daily attendance, course=None for demo simplicity)
                    record, created = AttendanceRecord.objects.update_or_create(
                        student=student,
                        course=None,
                        date=date,
                        defaults={
                            "status": status,
                            "minutes_late": minutes_late,
                            "notes_public": "",
                        },
                    )
                    
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Attendance seed complete: {created_count} created, {updated_count} updated"
            )
        )
