from __future__ import annotations

import datetime
import random

from django.core.management import BaseCommand
from django.db import transaction

from academics.models import Enrollment as AcademicEnrollment
from core.models import School, Student, StudentIdentityLink
from crown_api.models_academics_core import AttendanceRecord


class Command(BaseCommand):
    help = "Seed deterministic section-aware attendance records for Heritage demo (fixed week: Feb 9-13, 2026)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--school-id",
            type=str,
            help="UUID of the school (defaults to Heritage Christian Academy if not provided)",
        )

    def handle(self, *args, **opts):
        school_id = opts.get("school_id")
        if school_id:
            school = School.objects.filter(pk=school_id).first()
            if not school:
                raise RuntimeError(f"School {school_id} not found")
        else:
            school = (
                School.objects.filter(name="Heritage Christian Academy")
                .order_by("-created_at", "id")
                .first()
            )
            if not school:
                raise RuntimeError("No demo school found")

        self.stdout.write(f"Seeding section-aware attendance for school_id={school.id}")

        week_dates = [
            datetime.date(2026, 2, 9),
            datetime.date(2026, 2, 10),
            datetime.date(2026, 2, 11),
            datetime.date(2026, 2, 12),
            datetime.date(2026, 2, 13),
        ]

        students = Student.objects.filter(school=school, status="ACTIVE").order_by("id")
        if not students.exists():
            self.stdout.write(self.style.WARNING("No active students found; skipping attendance seed"))
            return

        random.seed(42)
        created_count = 0
        updated_count = 0
        skipped_unmapped = 0
        skipped_unenrolled = 0

        with transaction.atomic():
            for student in students:
                link = (
                    StudentIdentityLink.objects.select_related("compatibility_student")
                    .filter(
                        school=school,
                        core_student=student,
                        verification_status=StudentIdentityLink.STATUS_VERIFIED,
                        compatibility_student__school_id=school.id,
                    )
                    .first()
                )
                if link is None:
                    skipped_unmapped += 1
                    continue

                enrollment = (
                    AcademicEnrollment.objects.select_related("section")
                    .filter(
                        school_id=school.id,
                        student=link.compatibility_student,
                        section__school_id=school.id,
                    )
                    .order_by("section_id")
                    .first()
                )
                if enrollment is None:
                    skipped_unenrolled += 1
                    continue

                section = enrollment.section
                # Retire the pre-section demo fixture for this exact proof window so
                # a single logical attendance fact is not represented twice.
                AttendanceRecord.objects.filter(
                    student=student,
                    section__isnull=True,
                    course__isnull=True,
                    date__in=week_dates,
                ).delete()

                for attendance_date in week_dates:
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

                    _, created = AttendanceRecord.objects.update_or_create(
                        student=student,
                        section=section,
                        date=attendance_date,
                        defaults={
                            "course": None,
                            "status": status,
                            "minutes_late": minutes_late,
                            "notes_public": "Heritage section-aware demo attendance.",
                        },
                    )
                    if created:
                        created_count += 1
                    else:
                        updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                "Attendance seed complete: "
                f"{created_count} created, {updated_count} updated, "
                f"{skipped_unmapped} skipped_unmapped, {skipped_unenrolled} skipped_unenrolled"
            )
        )
